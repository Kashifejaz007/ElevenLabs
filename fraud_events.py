"""
Fraud Event Engine — ResolveAI (sandbox).

Fixes a real gap found in QA: the case a call is "about" must be bound
server-side, at incident-creation time — never chosen by the agent
mid-call via a free-text case_id parameter. Previously, any call to
verify_customer could pass ANY case_id, meaning an agent bug (or a
manipulated webhook payload) could target a case unrelated to the
customer actually being called.

Real-world chronology this models:
  1. Bank's fraud system detects something → POSTs to ResolveAI
     (create_incident). ResolveAI — not the LLM — decides which case
     this is.
  2. ResolveAI places the outbound call via ElevenLabs' outbound-call
     API, passing incident_id as a custom dynamic variable in
     conversation_initiation_client_data (confirmed real ElevenLabs
     capability — see elevenlabs_config/tool_configuration.md).
  3. ElevenLabs creates the actual call and hands the agent both
     system__conversation_id (call_id) and the incident_id dynamic
     variable — both bound as "Dynamic variable" tool parameters, never
     "LLM Prompt". The agent never sees or supplies case_id directly,
     at any point, in any tool.
  4. verify_customer resolves case_id server-side from incident_id.

incident_id is a large random token (not a guessable sequential ID like
"CASE-2001"), and can only ever be bound to ONE call_id — first bind
wins. A second bind attempt with a different call_id is rejected,
which is real (if basic) replay protection: a captured/leaked
incident_id can't be used to start a second parallel session once the
real call has claimed it. Incidents also expire after a fixed window
if never used.
"""

import datetime
import uuid

from data.fraud_cases import FRAUD_CASES

INCIDENT_EXPIRY_SECONDS = 15 * 60  # 15 minutes — a real deployment would tune this

_INCIDENTS: dict[str, dict] = {}


def _now():
    return datetime.datetime.now(datetime.UTC)


def create_incident(case_id: str) -> dict:
    """Simulates the bank's fraud system notifying ResolveAI. Takes a
    known case_id here as the sandbox stand-in for a real fraud-signal
    payload; in production this would receive fraud-detection data and
    resolve/create the case itself. Returns an unguessable incident_id
    — this is the ONLY thing that ever reaches the eventual voice call.

    Also surfaces whether this case's customer has previously opted out
    of AI-handled contact (see the opt-out registry below). This does
    NOT block incident creation — a fraud case still needs handling —
    it's a signal for whatever system places the outbound call to route
    to a human channel instead of an AI voice agent for this customer."""
    if case_id not in FRAUD_CASES:
        raise ValueError(f"Unknown case_id: {case_id}")

    customer_id = FRAUD_CASES[case_id]["customer_id"]
    incident_id = "INC-" + uuid.uuid4().hex[:16]
    _INCIDENTS[incident_id] = {
        "incident_id": incident_id,
        "case_id": case_id,
        "created_at": _now(),
        "call_id": None,  # bound once the outbound call actually starts
    }
    result = dict(_INCIDENTS[incident_id])
    result["customer_opted_out"] = is_customer_opted_out(customer_id)
    return result


def _is_expired(incident: dict) -> bool:
    age = (_now() - incident["created_at"]).total_seconds()
    return age > INCIDENT_EXPIRY_SECONDS


def bind_call_to_incident(incident_id: str, call_id: str) -> dict:
    """Simulates ElevenLabs handing this server the conversation ID at
    call start. Binds call_id -> incident's case server-side, before
    verification ever happens. First bind wins — a second, different
    call_id attempting to claim the same incident is rejected (basic
    replay/hijack protection); the same call_id re-binding is treated
    as idempotent (a retry of the same call)."""
    incident = _INCIDENTS.get(incident_id)
    if incident is None:
        return {"ok": False, "reason": "INCIDENT_NOT_FOUND"}

    if _is_expired(incident):
        return {"ok": False, "reason": "INCIDENT_EXPIRED"}

    if incident["call_id"] is not None and incident["call_id"] != call_id:
        return {"ok": False, "reason": "INCIDENT_ALREADY_BOUND"}

    incident["call_id"] = call_id
    return {"ok": True, "case_id": incident["case_id"]}


def get_case_id_for_call(call_id: str) -> str | None:
    """The only way tools.py resolves which case a call concerns — by
    lookup, never by trusting an agent-supplied case_id."""
    for incident in _INCIDENTS.values():
        if incident["call_id"] == call_id and not _is_expired(incident):
            return incident["case_id"]
    return None


def reset_incidents() -> None:
    _INCIDENTS.clear()


# ---------------------------------------------------------------------------
# Opt-out registry (Box K row 5 — the gap identified in Step 12's audit).
#
# Two distinct things, deliberately kept separate:
#   1. In-call: the customer can ask for a human / decline AI at any
#      point, verified or not — handled by tools.customer_opts_out,
#      which escalates THIS call immediately, same as any other
#      escalation trigger.
#   2. Persistent: opting out also marks the CUSTOMER (not just the
#      call) so a future fraud incident for them is flagged before any
#      new outbound AI call is placed. This registry is keyed by
#      customer_id, resolved the same secure way case_id already is —
#      via bind_call_to_incident — never by an agent-supplied customer
#      identifier. It does NOT block a future incident from being
#      created: a customer declining the AI channel still needs their
#      fraud case handled, just by a human, not silently dropped.
# ---------------------------------------------------------------------------

_OPTED_OUT_CUSTOMERS: set[str] = set()


def record_opt_out(customer_id: str) -> None:
    _OPTED_OUT_CUSTOMERS.add(customer_id)


def is_customer_opted_out(customer_id: str) -> bool:
    return customer_id in _OPTED_OUT_CUSTOMERS


def reset_opt_outs() -> None:
    _OPTED_OUT_CUSTOMERS.clear()
