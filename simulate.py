"""
Demo runner — ResolveAI (Banking & Insurance / Real-Time Fraud
Intervention, sandbox).

Simulates five call scenarios end-to-end through the real guardrail +
tool code. As of this revision, each demo starts with an explicit
fraud-event → incident → call binding step (fraud_events.py), matching
QA finding #1: the case a call concerns is decided server-side, before
any call happens — never chosen by the agent mid-call.

Five scenarios:
  1. Successful fraud intervention (English) — the core "2am" story
  2. Arabic customer — multilingual path, same guardrails
  3. Failed verification — hardened check rejects a wrong code
  4. Customer disputes the fraud flag — no freeze, human review instead
  5. High-value transaction — human authorization gate blocks a
     unilateral freeze even with full customer confirmation

Direct adversarial/attack attempts (skip verification, hijack an
incident, freeze via a manipulated payload) are covered in
test_guardrails.py instead of as scripted demos — stricter evidence,
since it asserts the block programmatically on every run.

Run: python3 simulate.py
Produces: transcripts printed to stdout + demo_output/*.json (audit trail)
"""

import json
import os
import uuid
import time

import tools
import fraud_events
from guardrails import CallState, AUDIT_LOG
from data.fraud_cases import reset_mock_data


TRANSCRIPTS = []


def say(speaker: str, text: str) -> None:
    line = f"{speaker}: {text}"
    TRANSCRIPTS.append({"speaker": speaker, "text": text})
    print(line)


def timeline(label: str) -> None:
    line = f"  [{time.strftime('%H:%M:%S')}] {label}"
    TRANSCRIPTS.append({"speaker": "TIMELINE", "text": label})
    print(line)


def divider(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def start_call(case_id: str) -> tuple[CallState, str]:
    """Models the real chronology: bank detects fraud -> ResolveAI backend
    creates an incident (never the agent) -> ResolveAI places the
    outbound call, which is where call_id first exists -> the incident
    is bound to that call_id. The agent's very first tool call
    (verify_customer) only ever receives incident_id, never case_id."""
    timeline("FRAUD SIGNAL RECEIVED (bank's detection system)")
    incident = fraud_events.create_incident(case_id)
    timeline(f"INCIDENT CREATED — incident_id={incident['incident_id']} (case never exposed to agent)")
    state = CallState(call_id=str(uuid.uuid4()))
    timeline(f"OUTBOUND CALL INITIATED — call_id={state.call_id}")
    timeline("CUSTOMER ANSWERED")
    return state, incident["incident_id"]


def demo_1_success_freeze():
    divider("DEMO 1 — SUCCESSFUL FRAUD INTERVENTION, ENGLISH (CASE-2001)")
    state, incident_id = start_call("CASE-2001")

    say("AGENT", "Hello, this is an automated call from your bank's fraud "
                 "protection team. This call is recorded. We detected "
                 "unusual activity on your card — is now a good time to "
                 "continue?")
    say("CUSTOMER", "Yes, go ahead.")

    say("AGENT", "Thank you. We've sent a 4-digit verification code to "
                 "your registered number — could you read that back to "
                 "me? I will never ask for your card PIN.")
    say("CUSTOMER", "Sure, it's 4471.")
    result = tools.verify_customer(state, incident_id, spoken_verification_code="4471")
    say("SYSTEM", f"verify_customer -> {result}")
    timeline("VERIFICATION PASSED")

    result = tools.get_fraud_case(state)
    say("SYSTEM", f"get_fraud_case -> {result}")
    say("AGENT", f"We flagged a transaction of {result['transaction_amount']} "
                 f"{result['transaction_currency']} at {result['transaction_merchant']} "
                 f"on your card ending {result['masked_card'][-4:]}. "
                 "Did you make this purchase?")
    say("CUSTOMER", "No, that wasn't me.")

    result = tools.confirm_fraud_and_freeze(state, customer_confirmed=True)
    say("SYSTEM", f"confirm_fraud_and_freeze -> {result}")
    timeline("CARD FROZEN")
    timeline("TRANSACTION BLOCKED")
    say("AGENT", "Thank you — I've frozen your card and blocked that "
                 "transaction. A replacement card process will follow "
                 "through your usual channels. Is there anything else?")
    say("CUSTOMER", "No, that's all.")
    say("AGENT", "This call has been recorded and transcribed for your "
                 "protection. Goodbye.")
    timeline("AUDIT COMPLETE")

    return state


def demo_2_arabic_customer():
    divider("DEMO 2 — ARABIC CUSTOMER (CASE-2002)")
    state, incident_id = start_call("CASE-2002")

    say("AGENT (AR)", "مرحباً، هذا اتصال آلي من فريق حماية الاحتيال في "
                       "بنكك. يتم تسجيل هذه المكالمة. رصدنا نشاطاً غير "
                       "معتاد على بطاقتك — هل الوقت مناسب للمتابعة؟")
    say("CUSTOMER (AR)", "نعم، تفضل.")

    say("AGENT (AR)", "شكراً. أرسلنا رمز تحقق مكوناً من 4 أرقام إلى رقمك "
                       "المسجل — هل يمكنك قراءته لي؟ لن أطلب منك أبداً "
                       "الرقم السري لبطاقتك.")
    say("CUSTOMER (AR)", "بالتأكيد، إنه 8823.")
    result = tools.verify_customer(state, incident_id, spoken_verification_code="8823")
    say("SYSTEM", f"verify_customer -> {result}")
    timeline("VERIFICATION PASSED")

    result = tools.get_fraud_case(state)
    say("SYSTEM", f"get_fraud_case -> {result}")
    say("AGENT (AR)", f"رصدنا معاملة بقيمة {result['transaction_amount']} "
                       f"{result['transaction_currency']} لدى "
                       f"{result['transaction_merchant']} في دولة مختلفة "
                       "خلال فترة زمنية قصيرة جداً. هل قمت بهذه المعاملة؟")
    say("CUSTOMER (AR)", "لا، لم أقم بهذه المعاملة.")

    result = tools.confirm_fraud_and_freeze(state, customer_confirmed=True)
    say("SYSTEM", f"confirm_fraud_and_freeze -> {result}")
    timeline("CARD FROZEN")
    timeline("TRANSACTION BLOCKED")
    say("AGENT (AR)", "شكراً لك — لقد قمت بتجميد بطاقتك وحظر هذه "
                       "المعاملة. سيتم التواصل معك بخصوص بطاقة بديلة. "
                       "شكراً لوقتك، مع السلامة.")
    timeline("AUDIT COMPLETE")

    return state


def demo_3_failed_verification():
    divider("DEMO 3 — FAILED VERIFICATION, WRONG CODE (CASE-2001)")
    state, incident_id = start_call("CASE-2001")

    say("AGENT", "We've sent a 4-digit verification code to your "
                 "registered number — could you read that back to me?")
    say("CUSTOMER", "Umm, I think it's 1234.")  # wrong — real code is 4471
    result = tools.verify_customer(state, incident_id, spoken_verification_code="1234")
    say("SYSTEM", f"verify_customer (wrong code) -> {result}")
    assert result["ok"] is False and result["reason"] == "VERIFICATION_FAILED"
    assert state.verified is False
    timeline("VERIFICATION FAILED")

    attempt = tools.get_fraud_case(state)
    say("SYSTEM", f"get_fraud_case (should be BLOCKED, unverified) -> {attempt}")
    assert attempt["ok"] is False and attempt["reason"] == "G3_UNVERIFIED"

    say("AGENT", "That doesn't match what we have on file — I'm not able "
                 "to discuss this case over this channel. I'll arrange a "
                 "callback so you can be verified a different way. In the "
                 "meantime, the flagged transaction remains on hold.")
    result = tools.escalate_to_human(state, reason_code="VERIFICATION_FAILED")
    say("SYSTEM", f"escalate_to_human -> {result}")
    timeline("ESCALATED TO HUMAN")

    return state


def demo_4_customer_disputes():
    divider("DEMO 4 — CUSTOMER DISPUTES THE FRAUD FLAG (CASE-2004)")
    state, incident_id = start_call("CASE-2004")

    say("AGENT", "This is an automated call from your bank's fraud team. "
                 "We flagged an unusual transaction — is now a good time?")
    say("CUSTOMER", "Okay.")

    result = tools.verify_customer(state, incident_id, spoken_verification_code="5502")
    say("SYSTEM", f"verify_customer -> {result}")
    timeline("VERIFICATION PASSED")

    result = tools.get_fraud_case(state)
    say("SYSTEM", f"get_fraud_case -> {result}")
    say("AGENT", f"We flagged a transaction of {result['transaction_amount']} "
                 f"{result['transaction_currency']} at {result['transaction_merchant']}. "
                 "Did you make this purchase?")
    say("CUSTOMER", "Yes, actually that was me — I forgot I bought that.")

    result = tools.customer_disputes_fraud(state)
    say("SYSTEM", f"customer_disputes_fraud -> {result}")
    timeline("CUSTOMER DISPUTES FLAG")
    say("AGENT", "Thank you for confirming — I won't take any action on "
                 "your card. I'm noting this so the flag doesn't trigger "
                 "again for this type of purchase.")

    attempt = tools.confirm_fraud_and_freeze(state, customer_confirmed=True)
    say("SYSTEM", f"confirm_fraud_and_freeze (should be BLOCKED) -> {attempt}")
    assert attempt["ok"] is False and attempt["reason"] == "G4_DISPUTED", \
        "Guardrail 4 failed to block a freeze after the customer disputed the flag"

    result = tools.escalate_to_human(state, reason_code="CUSTOMER_DISPUTES_FLAG")
    say("SYSTEM", f"escalate_to_human -> {result}")
    timeline("ESCALATED TO HUMAN")
    say("AGENT", "I've logged this for review to help improve future "
                 "detection. Thank you, goodbye.")

    return state


def demo_5_high_value_authorization_gate():
    divider("DEMO 5 — HIGH-VALUE TRANSACTION, HUMAN AUTHORIZATION GATE (CASE-2003)")
    state, incident_id = start_call("CASE-2003")

    say("AGENT", "This is an automated call from your bank's fraud team "
                 "regarding a high-value transaction on your card.")
    say("CUSTOMER", "Go ahead.")

    result = tools.verify_customer(state, incident_id, spoken_verification_code="1190")
    say("SYSTEM", f"verify_customer -> {result}")
    timeline("VERIFICATION PASSED")

    result = tools.get_fraud_case(state)
    say("SYSTEM", f"get_fraud_case -> {result}")
    say("AGENT", f"We flagged a transaction of {result['transaction_amount']} "
                 f"{result['transaction_currency']} at {result['transaction_merchant']} "
                 "— well above your typical spend. Did you make this purchase?")
    say("CUSTOMER", "No, definitely not me.")

    attempt = tools.confirm_fraud_and_freeze(state, customer_confirmed=True)
    say("SYSTEM", f"confirm_fraud_and_freeze (should require human authorization) -> {attempt}")
    assert attempt["ok"] is False and attempt["reason"] == "G7_DUAL_AUTH_REQUIRED", \
        "Guardrail 7 failed to block a unilateral high-value freeze"
    timeline("HUMAN AUTHORIZATION REQUIRED — FREEZE BLOCKED")

    say("AGENT", "Thank you for confirming. Given the value of this "
                 "transaction, I need an authorized reviewer to approve "
                 "the freeze — I'm escalating this now so it's actioned "
                 "within minutes, not left with just my say-so.")
    result = tools.escalate_to_human(state, reason_code="HUMAN_AUTHORIZATION_REQUIRED")
    say("SYSTEM", f"escalate_to_human -> {result}")
    timeline("ESCALATED TO HUMAN")

    return state


def main():
    os.makedirs("demo_output", exist_ok=True)

    demos = (
        demo_1_success_freeze,
        demo_2_arabic_customer,
        demo_3_failed_verification,
        demo_4_customer_disputes,
        demo_5_high_value_authorization_gate,
    )

    for demo_fn in demos:
        global TRANSCRIPTS
        TRANSCRIPTS = []
        reset_mock_data()          # pristine card/case state
        fraud_events.reset_incidents()  # pristine incident state
        state = demo_fn()
        out_name = demo_fn.__name__
        with open(f"demo_output/{out_name}_transcript.json", "w") as f:
            json.dump(TRANSCRIPTS, f, indent=2, ensure_ascii=False)
        print(f"\n[state after {out_name}] verified={state.verified} "
              f"disputed={state.disputed} escalated={state.escalated}")

    with open("demo_output/full_audit_log.json", "w") as f:
        json.dump(AUDIT_LOG, f, indent=2)

    divider("ALL DEMOS COMPLETE — GUARDRAIL ASSERTIONS PASSED")
    print(f"Audit events recorded: {len(AUDIT_LOG)}")
    print("Transcripts + audit log written to demo_output/")


if __name__ == "__main__":
    main()
