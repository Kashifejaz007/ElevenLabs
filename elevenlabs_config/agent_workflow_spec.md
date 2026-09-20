# ElevenLabs Agent Workflow — Node Spec (Fraud Domain)

Build spec for the ElevenLabs Agent Workflows builder (visual/UI-based).
Each node maps to one step of the five-step flow and binds to one
webhook tool from `tool_configuration.md`.

## Step 0 — Before the workflow even starts (QA finding #1 fix)

This happens on YOUR backend, before ElevenLabs places the call, and
never inside the agent's conversation:

1. Your fraud detection system calls `POST /api/fraud/events` on
   ResolveAI with the case details. ResolveAI creates an incident and
   returns `incident_id`.
2. Your backend triggers the ElevenLabs outbound call, passing
   `incident_id` as a custom dynamic variable in
   `conversation_initiation_client_data.dynamic_variables`.
3. Only now does the agent workflow below begin — with `incident_id`
   already available to it as a bound dynamic variable, never typed or
   chosen by the model.

## Workflow nodes

**Node 1 — Identify** (conversation node)
- Scoped tools: `customer_opts_out`
- Opening disclosure per system prompt Step 1. → Node 2 once customer
  agrees to continue. → Node 7 at any point if the customer declines
  or asks for a human.

**Node 2 — Verify** (conversation + tool node)
- Scoped tools: `verify_customer`, `customer_opts_out`
- Reads back the code, calls `verify_customer`.
  - `ok: true` → Node 3
  - `ok: false` → Node 6 (Escalate), reason_code=`VERIFICATION_FAILED`
  - customer declines/asks for human at any point → Node 7

**Node 3 — Understand** (tool node)
- Scoped tools: `get_fraud_case`, `customer_opts_out`
- Retrieves case info, explains using the knowledge base, asks "did you
  make this purchase?"
  - Customer says no → Node 4
  - Customer says yes → calls `customer_disputes_fraud` → Node 6,
    reason_code=`CUSTOMER_DISPUTES_FLAG`
  - customer declines/asks for human at any point → Node 7

**Node 4 — Resolve** (conversation + tool node)
- Scoped tools: `confirm_fraud_and_freeze`, `customer_opts_out`
- Calls the tool with `customer_confirmed: true`.
  - `ok: true` → Node 5
  - `reason: G7_DUAL_AUTH_REQUIRED` (human authorization gate, see README) → Node 6, reason_code=`HUMAN_AUTHORIZATION_REQUIRED`
  - `reason: G5_UNSUPPORTED` → Node 6, reason_code=`UNSUPPORTED_FRAUD_TYPE`
  - any other `ok: false` → Node 6, reason_code = the returned code
  - customer declines/asks for human at any point → Node 7

**Node 5 — Confirm** (conversation node, terminal)
- Scoped tools: none
- States the completed freeze, blocked transaction, and next steps.
  Ends call.

**Node 6 — Escalate** (tool node, terminal)
- Scoped tools: `escalate_to_human` only
- Calls `escalate_to_human` with the reason_code carried from the
  triggering node. States the case is queued for human review. Ends call.

**Node 7 — Opted Out** (tool node, terminal)
- Scoped tools: `customer_opts_out` only
- Reachable from Nodes 1–4, at any point, overriding whatever step the
  conversation was on. Calls `customer_opts_out` with the reason the
  customer gave. Tells the customer plainly they're being connected to
  a person now. Ends call. Distinct from Node 6: Node 6 is the agent
  escalating because something failed; Node 7 is the customer
  affirmatively choosing not to continue with an AI at all — same
  underlying human queue, different trigger, and Node 7 additionally
  records a persistent opt-out against the customer (see
  `fraud_events.record_opt_out`), which Node 6 does not.

## Per-node tool scoping — why it matters

Each node exposes only the tools it needs. Even if the model were
somehow persuaded to attempt an out-of-flow action, the tool wouldn't
be callable from that node — a layer on top of the code-level
guardrails in `guardrails.py`, and on top of the fact that no
approve/transfer/PIN-collection tool exists on the surface at all.
Three independent layers: workflow scoping, code-level guardrails, and
absence of dangerous tools entirely.
