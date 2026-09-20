# Fraud Response Policy — ResolveAI (Sandbox)

This is the knowledge-base source the agent's RAG retrieval is
restricted to when explaining a flagged transaction or deciding what it
may do about it. The agent must not state anything about a case that
isn't derived from this document or from `get_fraud_case()`'s live
response.

> Sandbox note: these entries correspond to the fraud types in
> `data/fraud_cases.py`. In a real deployment this document would be
> replaced with the bank's actual published fraud-response procedures.

## CARD_NOT_PRESENT_ONLINE

**Plain description:** A card-not-present purchase (online, phone) that
doesn't match the customer's usual spending pattern.

**Approved response:** Explain the transaction (amount, merchant,
masked card). Ask directly whether the customer made the purchase. If
not, proceed to `confirm_fraud_and_freeze`. If they confirm it was
theirs, do not freeze — call `customer_disputes_fraud` instead.

## GEO_VELOCITY_MISMATCH

**Plain description:** Two transactions in different countries within a
window too short for physical travel between them.

**Approved response:** Same as above — explain, ask, act only on the
customer's explicit answer.

## HIGH_VALUE_ANOMALY

**Plain description:** A transaction well above the customer's typical
spend, flagged for additional review regardless of the customer's
answer.

**Approved response:** Explain and ask as normal. If the customer says
it wasn't them, attempt `confirm_fraud_and_freeze` — but the agent must
expect and correctly explain a `G7_DUAL_AUTH_REQUIRED` result (a human
authorization gate, not a completed two-person approval): the
transaction value requires a second authorized reviewer before any
freeze takes effect, regardless of how confident the customer is. Tell
the customer this plainly and escalate — do not imply the freeze has
already happened.

## SUSPECTED_ACCOUNT_TAKEOVER

**Plain description:** Pattern consistent with account takeover (e.g. a
credential or device change shortly before the transaction).

**Approved response:** No automated correction exists for this fraud
type. The agent explains that this requires specialist review and
escalates immediately via `escalate_to_human`. Do not attempt
`confirm_fraud_and_freeze` — it will be blocked, and repeatedly trying
different framings to get it through is not permitted.

## General rules for all cases

1. The agent never proceeds to freeze without the customer's explicit
   verbal "no, that wasn't me" (or equivalent) captured in the current
   turn — never an inferred or assumed answer.
2. The agent never discusses whether a dispute, insurance claim, or
   loan will ultimately be approved — that decision belongs to human
   staff and is out of scope entirely; no tool exists for it.
3. If the customer says the transaction is theirs, the agent does not
   argue or double-check — it accepts the answer, does not freeze, and
   logs it via `customer_disputes_fraud`.
4. The agent never asks for a PIN, CVV, full card number, or banking
   password under any circumstance, including if the customer offers
   one unprompted — it should politely decline to hear it and remind
   them the bank never asks for this.
