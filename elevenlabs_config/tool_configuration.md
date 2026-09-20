# ElevenLabs Webhook Tool Configuration — Fraud Domain

Verified dashboard field shape (Sept 2026 ElevenLabs docs): Name,
Description, Method, URL, then a Body-parameters table with Data
Type/Identifier/Value type/Description per field. Tool Type = Webhook,
Content Type = application/json.

`call_id` binds to `system__conversation_id` (Value type: Dynamic
variable) — real, confirmed system variable, not invented.

**Updated after QA review (finding #1):** `incident_id` is now also
bound as a **Dynamic variable**, never LLM Prompt — it's a custom
dynamic variable YOU set when placing the outbound call, via
`conversation_initiation_client_data.dynamic_variables` on ElevenLabs'
outbound-call API (confirmed real capability, not invented — see
`elevenlabs/skills` outbound-calls reference). `case_id` no longer
appears as a tool parameter anywhere — the backend resolves it
server-side from `incident_id`. The agent never sees, types, or chooses
a case identifier at any point.

**Chronology this requires on your side:** before placing the call, your
own backend calls `POST /api/fraud/events` on ResolveAI to create the
incident, gets back `incident_id`, then passes that as a dynamic
variable when triggering the ElevenLabs outbound call. The agent's
first tool call already has `incident_id` available — it never asks for
one or invents one.

---

## Tool 1 — verify_customer

| Field | Value |
|---|---|
| Name | `verify_customer` |
| Description | Verifies the customer's identity via a one-time code before any case data can be accessed. Call immediately after the customer agrees to continue and has read back the code. |
| Method | POST |
| URL | `https://<your-deployed-host>/tools/verify_customer` |

| Data Type | Identifier | Value type | Description |
|---|---|---|---|
| string | call_id | Dynamic variable → `system__conversation_id` | Current conversation ID |
| string | incident_id | Dynamic variable → your custom `incident_id` set at outbound-call time | Never LLM Prompt — the agent must not be able to type or guess this |
| string | spoken_verification_code | LLM Prompt | Exactly what the customer said, unmodified. Never invented, corrected, or guessed by the agent. |

---

## Tool 2 — get_fraud_case

| Field | Value |
|---|---|
| Name | `get_fraud_case` |
| Description | Retrieves the flagged transaction for the verified case: amount, merchant, masked card, fraud type. Only call after verify_customer has succeeded. |
| Method | POST |
| URL | `https://<your-deployed-host>/tools/get_fraud_case` |

| Data Type | Identifier | Value type | Description |
|---|---|---|---|
| string | call_id | Dynamic variable → `system__conversation_id` | Current conversation ID |

---

## Tool 3 — customer_disputes_fraud

| Field | Value |
|---|---|
| Name | `customer_disputes_fraud` |
| Description | Call the moment the customer says the transaction WAS theirs. Do not argue or double-check — this flags the case as a false positive for review and suppresses the freeze tool. |
| Method | POST |
| URL | `https://<your-deployed-host>/tools/customer_disputes_fraud` |

| Data Type | Identifier | Value type | Description |
|---|---|---|---|
| string | call_id | Dynamic variable → `system__conversation_id` | Current conversation ID |

---

## Tool 4 — confirm_fraud_and_freeze

| Field | Value |
|---|---|
| Name | `confirm_fraud_and_freeze` |
| Description | Freezes the card and blocks the pending transaction. Only call after the customer explicitly says the transaction was NOT theirs, in the current turn. May return G7_DUAL_AUTH_REQUIRED for high-value transactions (a human authorization gate, not a full second-signer workflow — see README) — this is expected, not an error to retry around. |
| Method | POST |
| URL | `https://<your-deployed-host>/tools/confirm_fraud_and_freeze` |

| Data Type | Identifier | Value type | Description |
|---|---|---|---|
| string | call_id | Dynamic variable → `system__conversation_id` | Current conversation ID |
| boolean | customer_confirmed | LLM Prompt | True only if the customer just explicitly said the transaction wasn't theirs. The backend strictly validates this is a real boolean — a string like "false" is rejected outright, not treated as falsy. |

**No case_id parameter** — removed per QA finding #1. The backend acts
only on the case bound to this call at verification time.

---

## Tool 5 — escalate_to_human

| Field | Value |
|---|---|
| Name | `escalate_to_human` |
| Description | Queues the case for human review. Call whenever verification fails, the customer disputes the flag, the fraud type is unsupported, the high-value authorization gate blocks a freeze, or the customer asks for something this agent cannot do. |
| Method | POST |
| URL | `https://<your-deployed-host>/tools/escalate_to_human` |

| Data Type | Identifier | Value type | Description |
|---|---|---|---|
| string | call_id | Dynamic variable → `system__conversation_id` | Current conversation ID |
| string | reason_code | LLM Prompt | Short reason, e.g. VERIFICATION_FAILED, CUSTOMER_DISPUTES_FLAG, HUMAN_AUTHORIZATION_REQUIRED, UNSUPPORTED_FRAUD_TYPE |

---

## Tool 6 — customer_opts_out

| Field | Value |
|---|---|
| Name | `customer_opts_out` |
| Description | Call the moment the customer declines to continue with an AI, or asks for a human — at any point in the call, verified or not. Do not gate this behind verification. Ends the automated portion of the call and connects them to a person. |
| Method | POST |
| URL | `https://<your-deployed-host>/tools/customer_opts_out` |

| Data Type | Identifier | Value type | Description |
|---|---|---|---|
| string | call_id | Dynamic variable → `system__conversation_id` | Current conversation ID |
| string | incident_id | Dynamic variable → your custom `incident_id` set at outbound-call time | Same dynamic variable as Tool 1 — never LLM Prompt. Works even if verification never happened. |
| string | reason_code | LLM Prompt | Short reason, e.g. CUSTOMER_REQUESTS_HUMAN, CUSTOMER_DECLINES_AI |

This is the one tool available before verification succeeds — every
other tool except `verify_customer` itself requires it first. The
backend also records a persistent do-not-call flag against the
customer this incident belongs to, so a future fraud case for them is
routed to a human channel instead of another AI call — see `fraud_events.py:record_opt_out`.

---

## Authentication (QA finding #4 — now implemented, not just noted)

`server.py` supports two modes via `RESOLVEAI_DEMO_MODE`:
- **Demo mode (default):** no auth required — matches the bundled demo
  frontend, which calls `/tools/*` directly for judge convenience.
- **Production mode** (`RESOLVEAI_DEMO_MODE=false`): every `/tools/*`
  and `/api/fraud/events` request must carry header
  `X-ResolveAI-Secret` matching `RESOLVEAI_WEBHOOK_SECRET`.

To wire this into ElevenLabs: add a Header parameter (Value type:
Secret) named `X-ResolveAI-Secret` to each tool above, sourced from a
Workspace Auth Connection holding the same value as your deployment's
`RESOLVEAI_WEBHOOK_SECRET` environment variable.

## Where this plugs into the workflow

See `agent_workflow_spec.md` for which node gets which tool(s) scoped
to it.
