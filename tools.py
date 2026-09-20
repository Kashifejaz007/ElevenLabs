"""
Tool / Webhook layer — ResolveAI (Banking & Insurance / Real-Time
Fraud Intervention, sandbox).

These are the ONLY functions an ElevenLabs agent (or this simulator)
can call. In a real deployment these would be exposed as ElevenLabs
webhook/server tools with this exact signature set — nothing more.

Notice what is deliberately absent: there is no approve_transaction(),
reject_transaction(), transfer_funds(), or any PIN/CVV/password
collection function (Guardrail 1, "no PIN" requirement — enforced by
omission). As of this revision, `case_id` is ALSO absent from every
tool signature — it is never a parameter the agent supplies, anywhere.
It is resolved server-side from `incident_id` (see fraud_events.py),
which is itself a Dynamic-variable-bound value set by ResolveAI at
outbound-call time, never typed or chosen by the LLM. This closes a
real gap found in QA review: previously an agent could pass any
case_id string directly to verify_customer.
"""

import datetime

from data.fraud_cases import FRAUD_CASES, CARDS
import fraud_events
from guardrails import (
    CallState,
    GuardrailViolation,
    check_verified,
    check_not_disputed,
    check_supported,
    check_no_dual_authorization_required,
    record_audit_event,
)


def _now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


def _audit(call_id: str, tool: str, outcome: str, detail: str) -> None:
    record_audit_event({
        "timestamp": _now(),
        "call_id": call_id,
        "tool": tool,
        "outcome": outcome,
        "detail": detail,
    })


def _mask_last4(card_id: str) -> str:
    card = CARDS.get(card_id)
    return f"**** {card['last4']}" if card else "**** ????"


def verify_customer(state: CallState, incident_id: str, spoken_verification_code: str) -> dict:
    """Approved verification challenge.

    SECURITY (two layers, both hardened):

    1. Which case this concerns is resolved from `incident_id` — a
       server-generated, unguessable token created at incident time
       (see fraud_events.create_incident), bound to exactly one call_id
       on first use. The agent never supplies or sees a case_id.
    2. Whether verification succeeded is a server-side string
       comparison against the code on file for that resolved case —
       never an agent-asserted boolean. No tool reveals the correct
       code back to the agent. This is never a PIN — it's a one-time
       code tied to this specific contact attempt.
    """
    bind_result = fraud_events.bind_call_to_incident(incident_id, state.call_id)
    if not bind_result["ok"]:
        _audit(state.call_id, "verify_customer", "DENIED", f"Incident binding failed: {bind_result['reason']}")
        return {"ok": False, "reason": bind_result["reason"]}

    case_id = bind_result["case_id"]
    expected_code = FRAUD_CASES[case_id]["verification_code"]
    provided = (spoken_verification_code or "").strip()

    if provided == expected_code:
        state.verified = True
        state.case_id = case_id
        _audit(state.call_id, "verify_customer", "SUCCESS", case_id)
        return {"ok": True}

    _audit(state.call_id, "verify_customer", "DENIED", "Verification code mismatch")
    return {"ok": False, "reason": "VERIFICATION_FAILED"}


def get_fraud_case(state: CallState) -> dict:
    """Returns only the minimum information needed to explain the flagged
    activity — masked card, transaction summary, fraud type. Never the
    full card number, never anything beyond this specific case."""
    try:
        check_verified(state)
    except GuardrailViolation as e:
        _audit(state.call_id, "get_fraud_case", "BLOCKED", e.message)
        return {"ok": False, "reason": e.code}

    case = FRAUD_CASES[state.case_id]
    _audit(state.call_id, "get_fraud_case", "SUCCESS", case["fraud_type"])
    return {
        "ok": True,
        "fraud_type": case["fraud_type"],
        "fraud_description": case["fraud_description"],
        "masked_card": _mask_last4(case["card_id"]),
        "transaction_amount": case["transaction"]["amount"],
        "transaction_currency": case["transaction"]["currency"],
        "transaction_merchant": case["transaction"]["merchant"],
        "requires_dual_authorization": case["requires_dual_authorization"],
        "supported": case["supported"],
    }


def customer_disputes_fraud(state: CallState) -> dict:
    """Called when the customer says the transaction IS theirs — i.e.
    disputes the fraud flag itself. Suppresses the freeze tool and
    routes to human review rather than either freezing or dismissing
    the case automatically."""
    try:
        check_verified(state)
    except GuardrailViolation as e:
        _audit(state.call_id, "customer_disputes_fraud", "BLOCKED", e.message)
        return {"ok": False, "reason": e.code}

    state.disputed = True
    _audit(state.call_id, "customer_disputes_fraud", "FLAGGED", "Customer states transaction is legitimate")
    return {"ok": True, "next_action": "ESCALATE_TO_HUMAN"}


def confirm_fraud_and_freeze(state: CallState, customer_confirmed) -> dict:
    """The single highest-stakes tool in the system. Freezes the card and
    blocks the pending transaction — but only if every guardrail below
    passes. Acts ONLY on state.case_id, bound during verify_customer —
    there is no case_id parameter here for the agent to supply, so
    there's nothing to redirect.

    SECURITY: `customer_confirmed` must be a genuine Python/JSON
    boolean. A malformed or manipulated payload sending the STRING
    "false" is truthy in Python and would previously have passed an
    `if not customer_confirmed` check — this now rejects anything that
    isn't strictly True or False before that check ever runs.

    Idempotent: calling this twice on an already-frozen card does not
    re-run the freeze or produce a duplicate side effect — it reports
    ALREADY_FROZEN and changes nothing further.
    """
    try:
        check_verified(state)
        check_not_disputed(state)
        case = FRAUD_CASES[state.case_id]
        check_supported(case)
        check_no_dual_authorization_required(case)
    except GuardrailViolation as e:
        _audit(state.call_id, "confirm_fraud_and_freeze", "BLOCKED", e.message)
        return {"ok": False, "reason": e.code, "message": e.message}

    if not isinstance(customer_confirmed, bool):
        _audit(state.call_id, "confirm_fraud_and_freeze", "BLOCKED",
               f"customer_confirmed was not a strict boolean (got {type(customer_confirmed).__name__}: {customer_confirmed!r})")
        return {"ok": False, "reason": "G2_INVALID_TYPE"}

    if not customer_confirmed:
        _audit(state.call_id, "confirm_fraud_and_freeze", "BLOCKED", "No explicit customer confirmation")
        return {"ok": False, "reason": "G2_NO_CONFIRMATION"}

    case = FRAUD_CASES[state.case_id]
    card = CARDS[case["card_id"]]

    if card["status"] == "FROZEN":
        _audit(state.call_id, "confirm_fraud_and_freeze", "ALREADY_FROZEN", case["case_id"])
        return {
            "ok": True,
            "already_frozen": True,
            "card_status": "FROZEN",
            "transaction_status": case["transaction"]["status"],
        }

    # --- the actual protective action ---
    card["status"] = "FROZEN"
    case["transaction"]["status"] = "BLOCKED"
    _audit(state.call_id, "confirm_fraud_and_freeze", "SUCCESS", case["case_id"])
    return {
        "ok": True,
        "already_frozen": False,
        "card_status": "FROZEN",
        "transaction_status": "BLOCKED",
    }


def escalate_to_human(state: CallState, reason_code: str) -> dict:
    state.escalated = True
    _audit(state.call_id, "escalate_to_human", "SUCCESS", reason_code)
    return {"ok": True, "queued": True, "reason_code": reason_code}
