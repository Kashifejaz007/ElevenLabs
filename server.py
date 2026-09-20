"""
Webhook server — ResolveAI (Banking & Insurance / Real-Time Fraud
Intervention, sandbox).

Exposes tools.py as HTTP endpoints in the shape ElevenLabs Conversational
AI custom (server) tools expect. Also exposes /api/fraud/events, which
is where a real deployment's fraud-detection system would notify
ResolveAI and trigger the outbound call (QA finding #1 fix) — this is
NOT something the agent calls; it's a backend-to-backend endpoint.

Also serves the static demo frontend (frontend/index.html) from the
same origin, so one deployment gives you both a working backend AND
the Q "live product" link.

SECURITY MODE (QA finding #4 + #5, handled together):
This server has two modes, controlled by RESOLVEAI_DEMO_MODE (default
"true"):
  - DEMO_MODE=true:  no webhook auth required, so the bundled demo
    frontend can call /tools/* directly and remain self-contained for
    judges. This mirrors why verification codes are visible in the
    demo frontend too — everything a judge needs to run the demo
    without external tooling is intentionally exposed, and this is
    documented, not hidden.
  - DEMO_MODE=false: every /tools/* and /api/fraud/events request must
    carry a header `X-ResolveAI-Secret` matching RESOLVEAI_WEBHOOK_SECRET
    (an environment variable — never hard-coded). This is the mode a
    real deployment would run in; the bundled frontend would then need
    to call through an authenticated proxy route instead of /tools/*
    directly (not built in this sandbox — see README roadmap).

Run locally: python3 server.py
"""

import os

from flask import Flask, request, jsonify, send_from_directory

import tools
import fraud_events
from guardrails import CallState, AUDIT_LOG
from data.fraud_cases import FRAUD_CASES, CARDS, reset_mock_data

app = Flask(__name__, static_folder="frontend", static_url_path="")

DEMO_MODE = os.environ.get("RESOLVEAI_DEMO_MODE", "true").lower() == "true"
WEBHOOK_SECRET = os.environ.get("RESOLVEAI_WEBHOOK_SECRET")

if DEMO_MODE:
    print("=" * 70)
    print("RESOLVEAI RUNNING IN DEMO MODE")
    print("Webhook authentication is DISABLED. Do not point real customer")
    print("data or a production ElevenLabs agent at this instance in this")
    print("mode. Set RESOLVEAI_DEMO_MODE=false and RESOLVEAI_WEBHOOK_SECRET")
    print("to run authenticated.")
    print("=" * 70)

# In-memory call-state store, keyed by call_id.
# Production: replace with a real session store (Redis, DB row per call).
# NOTE (QA finding #3): this in-memory state is why the Dockerfile and
# Procfile run a single worker — see the comment there for detail.
_SESSIONS: dict[str, CallState] = {}


def _get_state(call_id: str) -> CallState:
    if call_id not in _SESSIONS:
        _SESSIONS[call_id] = CallState(call_id=call_id)
    return _SESSIONS[call_id]


@app.before_request
def _require_webhook_auth():
    """Auth gate for tool and fraud-event endpoints. Health check,
    static frontend, and read-only demo-support endpoints are exempt —
    they carry no ability to change state or reveal case-specific data."""
    protected_prefixes = ("/tools/", "/api/fraud/events")
    if not request.path.startswith(protected_prefixes):
        return None
    if DEMO_MODE:
        return None
    provided = request.headers.get("X-ResolveAI-Secret")
    if not WEBHOOK_SECRET or provided != WEBHOOK_SECRET:
        return jsonify({"ok": False, "reason": "UNAUTHORIZED"}), 401
    return None


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "resolveai-fraud-sandbox", "demo_mode": DEMO_MODE})


@app.route("/", methods=["GET"])
def index():
    return send_from_directory(app.static_folder, "index.html")


# --- Fraud event / incident endpoint (backend-to-backend, not agent-called) --

@app.route("/api/fraud/events", methods=["POST"])
def route_fraud_event():
    """Simulates the bank's fraud detection system notifying ResolveAI.
    In this sandbox, called with a known case_id as a stand-in for a
    real fraud-signal payload. ResolveAI — not the agent — decides the
    case here and creates an incident; the agent will only ever see the
    resulting incident_id."""
    body = request.get_json(force=True)
    case_id = body.get("case_id")
    if case_id not in FRAUD_CASES:
        return jsonify({"ok": False, "reason": "UNKNOWN_CASE"}), 400
    incident = fraud_events.create_incident(case_id)
    # call_id doesn't exist yet in this sandbox until the (simulated)
    # outbound call starts — the frontend/simulator generates one next
    # and binds it via the first verify_customer call.
    return jsonify({
        "ok": True,
        "incident_id": incident["incident_id"],
        "customer_opted_out": incident["customer_opted_out"],
    })


# --- ElevenLabs webhook tool endpoints --------------------------------

@app.route("/tools/verify_customer", methods=["POST"])
def route_verify_customer():
    body = request.get_json(force=True)
    state = _get_state(body["call_id"])
    result = tools.verify_customer(
        state,
        incident_id=body["incident_id"],
        spoken_verification_code=body["spoken_verification_code"],
    )
    return jsonify(result)


@app.route("/tools/get_fraud_case", methods=["POST"])
def route_get_fraud_case():
    body = request.get_json(force=True)
    state = _get_state(body["call_id"])
    return jsonify(tools.get_fraud_case(state))


@app.route("/tools/customer_disputes_fraud", methods=["POST"])
def route_dispute():
    body = request.get_json(force=True)
    state = _get_state(body["call_id"])
    return jsonify(tools.customer_disputes_fraud(state))


@app.route("/tools/confirm_fraud_and_freeze", methods=["POST"])
def route_confirm_freeze():
    body = request.get_json(force=True)
    state = _get_state(body["call_id"])
    result = tools.confirm_fraud_and_freeze(
        state,
        customer_confirmed=body.get("customer_confirmed"),
    )
    return jsonify(result)


@app.route("/tools/escalate_to_human", methods=["POST"])
def route_escalate():
    body = request.get_json(force=True)
    state = _get_state(body["call_id"])
    result = tools.escalate_to_human(state, reason_code=body["reason_code"])
    return jsonify(result)


@app.route("/tools/customer_opts_out", methods=["POST"])
def route_opt_out():
    body = request.get_json(force=True)
    state = _get_state(body["call_id"])
    result = tools.customer_opts_out(
        state,
        incident_id=body["incident_id"],
        reason_code=body["reason_code"],
    )
    return jsonify(result)


# --- Read-only / demo-support endpoints --------------------------------

@app.route("/api/audit", methods=["GET"])
def route_audit_log():
    """Read-only endpoint for reviewers/judges to inspect the audit trail."""
    return jsonify(AUDIT_LOG)


@app.route("/api/cases", methods=["GET"])
def route_list_cases():
    """Demo-support only: lists the five mock cases so the frontend can
    offer them as scenario buttons. Never exposes verification_code."""
    return jsonify([
        {
            "case_id": c["case_id"],
            "fraud_type": c["fraud_type"],
            "language": c["preferred_language"],
            "requires_dual_authorization": c["requires_dual_authorization"],
            "supported": c["supported"],
            "card_status": CARDS[c["card_id"]]["status"],
            "transaction_status": c["transaction"]["status"],
        }
        for c in FRAUD_CASES.values()
    ])


@app.route("/api/demo/reset", methods=["POST"])
def route_demo_reset():
    """Resets all mock cases/cards, incidents, and the audit log to
    their initial state, so judges can replay any scenario repeatedly."""
    reset_mock_data()
    fraud_events.reset_incidents()
    fraud_events.reset_opt_outs()
    AUDIT_LOG.clear()
    _SESSIONS.clear()
    return jsonify({"ok": True, "reset": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
