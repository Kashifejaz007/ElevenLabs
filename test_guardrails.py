"""
Adversarial guardrail test suite — ResolveAI (Banking & Insurance /
Real-Time Fraud Intervention, sandbox).

Rewritten after external QA review found two real gaps (see README):
  1. case_id was an agent-supplied parameter that could target any
     case directly — now resolved server-side from an incident bound
     to the call, and removed as a parameter entirely.
  2. customer_confirmed only checked truthiness (`if not x`), so a
     malformed payload sending the STRING "false" would have passed —
     now requires a strict Python/JSON boolean.

Coverage: every exposed tool, every mock case's full path, verification
bypass, incident hijack/replay, strict-type bypass, dispute bypass,
unsupported-fraud bypass, high-value-authorization-gate bypass,
idempotency, and audit-event generation.

Run (no external deps required):
    python3 -c "
    import sys, test_guardrails as t
    tests = [n for n in dir(t) if n.startswith('test_')]
    ok = 0
    for n in tests:
        getattr(t, n)(); ok += 1
    print(f'{ok}/{len(tests)} passed')
    "
"""

import inspect
import uuid

import tools
import fraud_events
from guardrails import CallState, AUDIT_LOG
from data.fraud_cases import CARDS, reset_mock_data

CODES = {
    "CASE-2001": "4471",
    "CASE-2002": "8823",
    "CASE-2003": "1190",
    "CASE-2004": "5502",
    "CASE-2005": "6634",
}


def new_state():
    return CallState(call_id=str(uuid.uuid4()))


def start_incident(case_id: str) -> str:
    """Sandbox stand-in for the bank's fraud system notifying ResolveAI.
    Returns the incident_id — the only thing that ever reaches a call."""
    incident = fraud_events.create_incident(case_id)
    return incident["incident_id"]


def verified_state(case_id: str) -> CallState:
    """Full realistic setup: create incident, start a call, verify.
    Callers that mutate CARDS/FRAUD_CASES must call reset_mock_data()
    themselves first — this helper doesn't, so intent stays visible at
    the call site."""
    incident_id = start_incident(case_id)
    state = new_state()
    result = tools.verify_customer(state, incident_id, spoken_verification_code=CODES[case_id])
    assert result["ok"] is True, f"setup failed to verify {case_id}"
    return state


def _reset_all():
    reset_mock_data()
    fraud_events.reset_incidents()


# ===========================================================================
# GUARDRAIL 1 — No unilateral financial decision-making (by absence)
# ===========================================================================

def test_no_forbidden_financial_tools_exist():
    tool_names = {name for name in dir(tools) if not name.startswith("_")}
    forbidden = {
        "approve_transaction", "reject_transaction", "approve_claim",
        "reject_claim", "transfer_funds", "refund_funds",
        "override_freeze", "unfreeze_card", "set_card_status",
    }
    assert forbidden.isdisjoint(tool_names), (
        f"Forbidden tool(s) exposed: {forbidden.intersection(tool_names)}"
    )


def test_no_pin_cvv_password_collection_tools_exist():
    tool_names = {name.lower() for name in dir(tools) if not name.startswith("_")}
    for forbidden_substring in ("pin", "cvv", "password"):
        matches = {n for n in tool_names if forbidden_substring in n}
        assert not matches, f"Tool name references '{forbidden_substring}': {matches}"


def test_get_fraud_case_response_contains_no_pin_cvv_or_decision_field():
    _reset_all()
    state = verified_state("CASE-2001")
    result = tools.get_fraud_case(state)
    forbidden_keys = {"pin", "cvv", "password", "decision", "approved"}
    assert forbidden_keys.isdisjoint(result.keys())


def test_get_fraud_case_never_returns_full_card_number():
    _reset_all()
    state = verified_state("CASE-2001")
    result = tools.get_fraud_case(state)
    assert result["masked_card"].startswith("****")
    assert len(result["masked_card"].replace("*", "").replace(" ", "")) == 4


# ===========================================================================
# GUARDRAIL 2 — Freeze target binding + strict confirmation
# QA fix #1: case_id removed entirely as a tool parameter — structural
# test, same pattern as Guardrail 1.
# QA fix #2: customer_confirmed must be a strict bool.
# ===========================================================================

def test_confirm_freeze_has_no_case_id_parameter():
    """QA finding #1, verified structurally: there is no case_id
    parameter anywhere on confirm_fraud_and_freeze's signature for an
    agent (or a manipulated payload) to redirect to a different case."""
    sig = inspect.signature(tools.confirm_fraud_and_freeze)
    assert "case_id" not in sig.parameters, (
        "confirm_fraud_and_freeze still accepts a case_id parameter — "
        "QA finding #1 regression"
    )


def test_verify_customer_has_no_case_id_parameter():
    sig = inspect.signature(tools.verify_customer)
    assert "case_id" not in sig.parameters, (
        "verify_customer still accepts a case_id parameter directly — "
        "it should only ever receive incident_id"
    )


def test_freeze_rejects_without_confirmation():
    _reset_all()
    state = verified_state("CASE-2001")
    result = tools.confirm_fraud_and_freeze(state, customer_confirmed=False)
    assert result["ok"] is False
    assert result["reason"] == "G2_NO_CONFIRMATION"


def test_freeze_rejects_non_boolean_confirmation_values():
    """QA finding #2, directly: a malformed/manipulated JSON payload
    sending the STRING "false" (truthy in Python) must NOT pass. Also
    covers other JSON-shaped values a client might send instead of a
    real boolean: "true", "no", "1", 1, 0, None, [], {}."""
    _reset_all()
    non_boolean_values = ["false", "true", "no", "yes", "1", "0", 1, 0, None, [], {}]
    for bad_value in non_boolean_values:
        state = verified_state("CASE-2001")
        result = tools.confirm_fraud_and_freeze(state, customer_confirmed=bad_value)
        assert result["ok"] is False, (
            f"confirm_fraud_and_freeze incorrectly accepted "
            f"customer_confirmed={bad_value!r} ({type(bad_value).__name__})"
        )
        assert result["reason"] in ("G2_INVALID_TYPE", "G2_NO_CONFIRMATION"), (
            f"unexpected reason for {bad_value!r}: {result['reason']}"
        )
        assert CARDS["CARD-8821"]["status"] == "ACTIVE", (
            f"card was frozen despite non-boolean confirmation {bad_value!r}"
        )


def test_freeze_rejects_string_false_specifically():
    """The exact case QA flagged: a non-empty string is truthy in
    Python, so a naive `if not customer_confirmed` check would have let
    "false" (the string) through. This must be rejected before that
    check ever runs."""
    _reset_all()
    state = verified_state("CASE-2001")
    result = tools.confirm_fraud_and_freeze(state, customer_confirmed="false")
    assert result["ok"] is False
    assert result["reason"] == "G2_INVALID_TYPE"
    assert CARDS["CARD-8821"]["status"] == "ACTIVE"


def test_freeze_accepts_only_strict_true():
    _reset_all()
    state = verified_state("CASE-2001")
    result = tools.confirm_fraud_and_freeze(state, customer_confirmed=True)
    assert result["ok"] is True


# ===========================================================================
# GUARDRAIL 3 — Verification required, hardened, incident-bound
# ===========================================================================

def test_get_fraud_case_blocked_without_verification():
    state = new_state()
    result = tools.get_fraud_case(state)
    assert result["ok"] is False
    assert result["reason"] == "G3_UNVERIFIED"


def test_freeze_blocked_without_verification():
    _reset_all()
    state = new_state()
    result = tools.confirm_fraud_and_freeze(state, customer_confirmed=True)
    assert result["ok"] is False
    assert result["reason"] == "G3_UNVERIFIED"


def test_dispute_blocked_without_verification():
    state = new_state()
    result = tools.customer_disputes_fraud(state)
    assert result["ok"] is False
    assert result["reason"] == "G3_UNVERIFIED"


def test_verification_fails_on_wrong_code():
    _reset_all()
    incident_id = start_incident("CASE-2001")
    state = new_state()
    result = tools.verify_customer(state, incident_id, spoken_verification_code="0000")
    assert result["ok"] is False
    assert result["reason"] == "VERIFICATION_FAILED"
    assert state.verified is False


def test_verification_fails_on_empty_or_malformed_code():
    _reset_all()
    for bad_code in ("", "   ", None, "abcd"):
        incident_id = start_incident("CASE-2001")
        state = new_state()
        result = tools.verify_customer(state, incident_id, spoken_verification_code=bad_code)
        assert result["ok"] is False, f"bad code '{bad_code}' incorrectly accepted"
        assert state.verified is False


def test_no_tool_exposes_the_verification_code():
    _reset_all()
    state = verified_state("CASE-2001")
    result = tools.get_fraud_case(state)
    forbidden_keys = {"verification_code", "code", "otp"}
    assert forbidden_keys.isdisjoint(result.keys())
    tool_names = {name for name in dir(tools) if not name.startswith("_")}
    assert "get_verification_code" not in tool_names


# --- Incident binding, hijack, and replay protection (QA finding #1) ------

def test_verify_fails_for_unknown_incident_id():
    _reset_all()
    state = new_state()
    result = tools.verify_customer(state, "INC-doesnotexist", spoken_verification_code="4471")
    assert result["ok"] is False
    assert result["reason"] == "INCIDENT_NOT_FOUND"
    assert state.verified is False


def test_incident_cannot_be_hijacked_by_a_different_call():
    """The core fix for QA finding #1: once an incident is bound to the
    real call, a second, different call_id attempting to claim the same
    incident_id must be rejected — this is what stops a leaked/guessed
    incident_id from being usable by anyone other than the call it was
    actually issued for."""
    _reset_all()
    incident_id = start_incident("CASE-2001")
    real_call = new_state()
    result1 = tools.verify_customer(real_call, incident_id, spoken_verification_code="4471")
    assert result1["ok"] is True

    attacker_call = new_state()
    result2 = tools.verify_customer(attacker_call, incident_id, spoken_verification_code="4471")
    assert result2["ok"] is False
    assert result2["reason"] == "INCIDENT_ALREADY_BOUND"
    assert attacker_call.verified is False


def test_same_call_id_rebinding_same_incident_is_idempotent():
    """A retry of the SAME call (same call_id) against the same
    incident should not be treated as a hijack attempt."""
    _reset_all()
    incident_id = start_incident("CASE-2001")
    call_id = str(uuid.uuid4())
    state1 = CallState(call_id=call_id)
    result1 = tools.verify_customer(state1, incident_id, spoken_verification_code="4471")
    assert result1["ok"] is True

    state2 = CallState(call_id=call_id)  # simulates a retry with the same call_id
    result2 = tools.verify_customer(state2, incident_id, spoken_verification_code="4471")
    assert result2["ok"] is True


def test_incident_case_resolution_matches_what_was_created():
    """Verifies the resolved case is actually the one the incident was
    created for — not, say, always defaulting to the first case."""
    _reset_all()
    incident_id = start_incident("CASE-2003")
    state = new_state()
    result = tools.verify_customer(state, incident_id, spoken_verification_code=CODES["CASE-2003"])
    assert result["ok"] is True
    assert state.case_id == "CASE-2003"


# ===========================================================================
# GUARDRAIL 4 — Dispute suppression
# ===========================================================================

def test_freeze_blocked_after_dispute():
    _reset_all()
    state = verified_state("CASE-2001")
    tools.customer_disputes_fraud(state)
    result = tools.confirm_fraud_and_freeze(state, customer_confirmed=True)
    assert result["ok"] is False
    assert result["reason"] == "G4_DISPUTED"


def test_card_remains_active_after_disputed_freeze_attempt():
    _reset_all()
    state = verified_state("CASE-2001")
    tools.customer_disputes_fraud(state)
    tools.confirm_fraud_and_freeze(state, customer_confirmed=True)
    assert CARDS["CARD-8821"]["status"] == "ACTIVE"


# ===========================================================================
# GUARDRAIL 5 — Unsupported fraud-type fallback
# ===========================================================================

def test_freeze_blocked_for_unsupported_case():
    _reset_all()
    state = verified_state("CASE-2005")
    result = tools.confirm_fraud_and_freeze(state, customer_confirmed=True)
    assert result["ok"] is False
    assert result["reason"] == "G5_UNSUPPORTED"


def test_unsupported_case_still_reports_info_for_agent_to_explain():
    _reset_all()
    state = verified_state("CASE-2005")
    result = tools.get_fraud_case(state)
    assert result["ok"] is True
    assert result["supported"] is False


# ===========================================================================
# GUARDRAIL 6 — Auditability
# ===========================================================================

def _run_and_count(fn) -> int:
    before = len(AUDIT_LOG)
    fn()
    return len(AUDIT_LOG) - before


def test_every_tool_produces_audit_event_on_success():
    _reset_all()
    assert _run_and_count(lambda: verified_state("CASE-2001")) >= 1
    state = verified_state("CASE-2002")
    assert _run_and_count(lambda: tools.get_fraud_case(state)) >= 1
    assert _run_and_count(lambda: tools.confirm_fraud_and_freeze(
        state, customer_confirmed=True)) >= 1
    state2 = verified_state("CASE-2004")
    assert _run_and_count(lambda: tools.customer_disputes_fraud(state2)) >= 1
    assert _run_and_count(lambda: tools.escalate_to_human(state2, "CUSTOMER_DISPUTES_FLAG")) >= 1


def test_every_tool_produces_audit_event_on_denial():
    _reset_all()
    state = new_state()
    assert _run_and_count(lambda: tools.verify_customer(
        state, "INC-doesnotexist", spoken_verification_code="0000")) >= 1
    assert _run_and_count(lambda: tools.get_fraud_case(state)) >= 1
    assert _run_and_count(lambda: tools.confirm_fraud_and_freeze(
        state, customer_confirmed=True)) >= 1
    assert _run_and_count(lambda: tools.customer_disputes_fraud(state)) >= 1


# ===========================================================================
# GUARDRAIL 7 — High-value human authorization gate
# (renamed from "dual authorization" per QA finding #6 — see guardrails.py)
# ===========================================================================

def test_freeze_blocked_for_high_value_case_even_with_confirmation():
    _reset_all()
    state = verified_state("CASE-2003")
    result = tools.confirm_fraud_and_freeze(state, customer_confirmed=True)
    assert result["ok"] is False
    assert result["reason"] == "G7_DUAL_AUTH_REQUIRED"


def test_high_value_card_remains_active_after_blocked_attempt():
    _reset_all()
    state = verified_state("CASE-2003")
    tools.confirm_fraud_and_freeze(state, customer_confirmed=True)
    assert CARDS["CARD-7734"]["status"] == "ACTIVE"


def test_dual_authorization_flag_visible_to_agent_before_attempting_freeze():
    _reset_all()
    state = verified_state("CASE-2003")
    result = tools.get_fraud_case(state)
    assert result["requires_dual_authorization"] is True


# ===========================================================================
# Idempotency
# ===========================================================================

def test_freeze_is_idempotent_no_duplicate_side_effect():
    _reset_all()
    state = verified_state("CASE-2001")

    first = tools.confirm_fraud_and_freeze(state, customer_confirmed=True)
    assert first["ok"] is True
    assert first["already_frozen"] is False
    assert CARDS["CARD-8821"]["status"] == "FROZEN"

    second = tools.confirm_fraud_and_freeze(state, customer_confirmed=True)
    assert second["ok"] is True
    assert second["already_frozen"] is True
    assert CARDS["CARD-8821"]["status"] == "FROZEN"


def test_repeated_freeze_calls_produce_only_one_success_audit_event():
    _reset_all()
    state = verified_state("CASE-2001")
    tools.confirm_fraud_and_freeze(state, customer_confirmed=True)
    tools.confirm_fraud_and_freeze(state, customer_confirmed=True)
    tools.confirm_fraud_and_freeze(state, customer_confirmed=True)

    success_events = [
        e for e in AUDIT_LOG
        if e["tool"] == "confirm_fraud_and_freeze"
        and e["call_id"] == state.call_id
        and e["outcome"] == "SUCCESS"
    ]
    assert len(success_events) == 1, (
        f"Expected exactly one SUCCESS freeze event for this call, got {len(success_events)}"
    )


# ===========================================================================
# Full flow per mock case
# ===========================================================================

def test_full_flow_case2001_standard_freeze():
    _reset_all()
    state = verified_state("CASE-2001")
    info = tools.get_fraud_case(state)
    assert info["ok"] and info["fraud_type"] == "CARD_NOT_PRESENT_ONLINE"
    result = tools.confirm_fraud_and_freeze(state, customer_confirmed=True)
    assert result["ok"] is True
    assert result["card_status"] == "FROZEN"
    assert result["transaction_status"] == "BLOCKED"


def test_full_flow_case2002_standard_freeze_different_case():
    _reset_all()
    state = verified_state("CASE-2002")
    info = tools.get_fraud_case(state)
    assert info["ok"] and info["fraud_type"] == "GEO_VELOCITY_MISMATCH"
    result = tools.confirm_fraud_and_freeze(state, customer_confirmed=True)
    assert result["ok"] is True
    assert CARDS["CARD-4192"]["status"] == "FROZEN"


def test_full_flow_case2003_authorization_gate_escalation_path():
    _reset_all()
    state = verified_state("CASE-2003")
    tools.confirm_fraud_and_freeze(state, customer_confirmed=True)
    escalation = tools.escalate_to_human(state, "HUMAN_AUTHORIZATION_REQUIRED")
    assert escalation["ok"] is True
    assert state.escalated is True


def test_full_flow_case2004_dispute_path():
    _reset_all()
    state = verified_state("CASE-2004")
    tools.customer_disputes_fraud(state)
    assert state.disputed is True
    escalation = tools.escalate_to_human(state, "CUSTOMER_DISPUTES_FLAG")
    assert escalation["ok"] is True


def test_full_flow_case2005_unsupported_path():
    _reset_all()
    state = verified_state("CASE-2005")
    info = tools.get_fraud_case(state)
    assert info["ok"] and info["supported"] is False
    escalation = tools.escalate_to_human(state, "UNSUPPORTED_FRAUD_TYPE")
    assert escalation["ok"] is True
