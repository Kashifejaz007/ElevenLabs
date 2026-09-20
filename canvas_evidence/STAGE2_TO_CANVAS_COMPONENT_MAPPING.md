# STAGE 2 → OFFICIAL CANVAS MAPPING

Built directly from `STAGE2_ELEVENLABS_COMPONENT_AUDIT.md`. No new claims of
implementation are made here beyond what that audit already verified against
the repo. Where a status doesn't fit cleanly into one of the three requested
labels, it's stated as a hybrid rather than forced into the wrong single label
— see the Knowledge Base row.

---

## G — ElevenLabs Components

### 1. Agents Platform + Agent Workflows
- **Why ResolveAI genuinely needs it:** the verify → resolve → escalate flow
  must be a structural state machine, not prompt discipline alone — the whole
  security model depends on branching being enforced, not just described.
- **Stage 1 status:** Planned (full 6-node spec written in
  `agent_workflow_spec.md`; no live agent or workflow built)
- **What must actually exist by Stage 2:** A live Agents Platform agent with
  Agent Workflows configured to match the 6-node spec exactly, node-by-node.

### 2. Eleven v3 (TTS)
- **Why:** the call has no voice without it; multilingual delivery
  (English/Arabic) is the product's central claim.
- **Stage 1 status:** Not implemented
- **What must exist by Stage 2:** A selected voice wired to the live agent,
  tested speaking in both supported languages.

### 3. Scribe v2 Realtime + keyterm biasing
- **Why:** must accurately capture the spoken one-time verification code and
  yes/no confirmation — the single most security-critical input in the flow.
- **Stage 1 status:** Not implemented
- **What must exist by Stage 2:** STT connected to the live agent; a keyterm
  list built from real transaction/merchant vocabulary and code formats,
  tuned against test calls.

### 4. Knowledge Base / RAG
- **Why:** system prompt requires the agent explain transactions "using only
  wording from the fraud response policy knowledge base," not improvise.
- **Stage 1 status:** Hybrid — **Existing backend** (4 real policy files, 185
  lines total, in `knowledge_base/`) but **Not implemented** on the
  ElevenLabs side (files aren't uploaded to the live Knowledge Base feature,
  no RAG connection exists yet).
- **What must exist by Stage 2:** Those 4 files uploaded into ElevenLabs'
  actual Knowledge Base, RAG retrieval tested, source attribution confirmed.

### 5. Webhook (server) tools
- **Why:** the entire enforcement mechanism — the 5 backend actions are how
  anything actually happens.
- **Stage 1 status:** Hybrid — **Existing backend** (5 Flask endpoints, real,
  tested, 43/43 passing) but **Not implemented** on the ElevenLabs side (no
  live tool binding exists yet).
- **What must exist by Stage 2:** Each tool registered in a live agent per
  the field shapes in `tool_configuration.md`, production auth header wired,
  tested against the deployed backend.

### 6. Telephony — native Twilio integration
- **Why:** the product's defining action is a real outbound call to the
  customer's phone; nothing else in the design works without this.
- **Stage 1 status:** Not implemented — **no Twilio/SIP account is
  connected; no test call has been made**
- **What must exist by Stage 2:** A connected Twilio account and one
  successfully completed end-to-end outbound call through the live agent.

### 7. Tool scoping (per-node + privileged-action scoping)
- **Why:** the security model depends on each workflow node exposing only
  its one tool, and on the customer (an untrusted caller) never reaching a
  privileged action outside their verified case.
- **Stage 1 status:** Hybrid — **Existing backend** (code-level guardrails —
  value threshold, case-binding — 36/36 tests pass) + **Planned**
  (ElevenLabs-side per-node tool visibility; can't be configured until the
  live workflow in item 1 exists).
- **What must exist by Stage 2:** Per-node tool visibility configured in the
  live builder, then actually tested — confirming a node genuinely cannot
  call a tool outside its scope, not just documented as unable to.

### 8. Agent Testing
- **Why:** this is the literal evidence category Stage 2 is assessed on —
  needed to prove the guardrails work against the live agent, not only the
  backend in isolation.
- **Stage 1 status:** Not implemented as an ElevenLabs feature. (Backend
  equivalent — 43/43 Python tests — exists and is kept explicitly separate,
  per your standing instruction.)
- **What must exist by Stage 2:** Tool-call tests and multi-run pass rates
  executed inside ElevenLabs' actual Agent Testing feature, against the live
  agent and workflow.

---

## I — Guardrails

### 1. Opening disclosure
- **Concrete mechanism:** System prompt Step 1 requires stating it's an
  automated, recorded call from the bank's fraud team before any account
  detail is revealed.
- **Existing implementation:** Written into `system_prompt.md`; enforced
  today only as instruction text.
- **Missing implementation:** Never run against a live model — no evidence
  yet that the model actually follows it on every call, not just in the
  written spec.
- **Stage 2 implementation required:** Live agent running the real prompt;
  Agent Testing runs confirming disclosure happens on 100% of a sampled set.

### 2. Consent to be called
- **Concrete mechanism:** Step 1 confirms the customer is willing to
  continue before verification proceeds. Consent to be contacted *at all* is
  an institutional/regulatory precondition, outside the agent's control.
- **Existing implementation:** Same as above — prompt-level only.
- **Missing implementation:** No code-level guardrail equivalent to
  Verification's server-side check exists for this row — it's currently
  pure prompt trust, with no backend enforcement backing it up.
- **Stage 2 implementation required:** Confirm in Agent Workflows that Node
  1 structurally cannot proceed without an explicit "continue" response;
  test that declining ends the call cleanly and logs correctly.

### 3. Verification without secrets
- **Concrete mechanism:** `verify_customer` compares a one-time code
  server-side; the tool schema has no field that could carry a PIN, CVV, or
  password.
- **Existing implementation:** **Already implemented and tested** — real
  code, covered in the 36-test guardrail suite, schema verified to have no
  such field.
- **Missing implementation:** Never tested against a live model — no
  evidence yet the model itself won't improvise around this (e.g. accepting
  a spoken PIN and passing it through as `spoken_verification_code`).
- **Stage 2 implementation required:** Live tool binding; adversarial Agent
  Testing runs specifically probing for PIN/CVV/password leakage attempts.

### 4. Human approval point
- **Concrete mechanism:** `confirm_fraud_and_freeze` is blocked
  unconditionally above a value threshold (`G7_DUAL_AUTH_REQUIRED`); only a
  human-queue action can complete it.
- **Existing implementation:** **Already implemented and tested** — the
  strongest-evidenced row in the whole table, 36/36 guardrail tests cover it.
- **Missing implementation:** Never wired to a live tool — no evidence the
  model correctly *voices* this to a real customer rather than implying the
  freeze already happened.
- **Stage 2 implementation required:** A live test call that deliberately
  triggers a high-value case and confirms the agent states the human-review
  requirement accurately.

### 5. Opt-out path
- **Concrete mechanism:** None exists.
- **Existing implementation:** **None.** Hanging up ends the call; there is
  no persistent do-not-call/opt-out list anywhere in the sandbox.
- **Missing implementation:** The entire mechanism — no design, no code, no
  workflow node.
- **Stage 2 implementation required:** This has to be *designed* before
  Stage 2 work can even start on it — right now there's nothing to build
  toward. This is the single highest-risk row on the whole canvas.

### 6. Escalation trigger
- **Concrete mechanism:** `escalate_to_human` fires on dispute, unsupported
  fraud type, failed verification, the high-value gate, or any tool
  returning `ok:false`.
- **Existing implementation:** **Already implemented and tested** at the
  code/workflow-spec level (Node 6, covered by guardrail tests).
- **Missing implementation:** Live binding — never tested that a real live
  agent calls this tool at the right moment rather than retrying or
  improvising around a failure.
- **Stage 2 implementation required:** Live tool binding; Agent Testing runs
  checking escalation fires correctly across each of the trigger conditions.

---

## H — Technical Architecture ("How it integrates")

Every required element, and its current status against the existing draft
diagram (`box_L_architecture.png`):

| Required element | Currently shown? |
|---|---|
| Caller/channel | Yes |
| Every selected J component | Partial — shown as a text list inside the ElevenLabs-platform zone; Knowledge Base, keyterm biasing, and Agent Testing aren't individually labelled |
| Institution systems | Yes, by category only (same confidentiality constraint noted in H) |
| Direction of every arrow | Yes |
| Personal-data boundary | Yes — marked with a filled dot |
| Human approval gate | Shown inside the backend box, not pulled out as its own labelled node |
| Dependency-down behaviour | Yes — described (`ok:false` → escalate, no auto-retry) |
| **Tool/privilege boundaries** | **Missing** — the diagram doesn't visually show per-node tool scoping (K row 4/6, J item 7) as its own boundary; this is a real gap, not yet drawn |

---

## COMPONENTS EXPLICITLY EXCLUDED

Audited and deliberately not selected for J, each with the reason already
established in the Step 10 audit:

- **Sub-agents** — no evidence the flow needs a second specialized agent
  handoff; one agent + human escalation covers every branch
- **MCP servers** — the 5 direct webhook tools fully cover the tool surface
- **Client tools** — everything runs server-side; no client-executed logic
- **Voice Design** — a standard Voice Library voice is sufficient; no
  evidence a custom-built voice is needed
- **Web/mobile SDKs, WebRTC/WebSocket** — this is an outbound phone call
  product, not an embedded app/web widget
- **WhatsApp** — no evidence a text channel is needed; the product is
  specifically a proactive voice call
- **Batch calling** — reacts to individual real-time fraud alerts, not
  scheduled outbound campaigns
- **Model cascading/fallback** — the code-level `ok:false` → escalate
  pattern already handles failure modes; no evidence multi-model fallback
  is needed
- **Post-call webhooks** — the audit-trail design logs each action in-call,
  as it happens; no separate post-call summary step is evidenced as needed
- **Analytics/versioning** — only becomes relevant once a live agent exists
  to generate data; not part of the Stage 1 minimum

---

## STAGE 2 EVIDENCE REQUIRED

| Component | Evidence to capture during Build Sprint |
|---|---|
| Agents Platform + Agent Workflows | Screenshot/export of the live workflow graph matching the 6-node spec |
| Eleven v3 TTS | Recording of the agent speaking in both English and Arabic |
| Scribe v2 Realtime + keyterm biasing | Transcript log showing correct capture of a spoken verification code |
| Knowledge Base / RAG | Log or screenshot showing a policy answer with its source document cited |
| Webhook (server) tools | Live call log showing each of the 5 tools invoked with real request/response payloads |
| Telephony (Twilio) | Call log or recording of one completed real outbound call |
| Tool scoping | A negative test — an attempted out-of-scope tool call from a node, and confirmation it's rejected |
| Agent Testing | Exported pass-rate report from ElevenLabs' own Agent Testing run |

---

## Note on box lettering — RESOLVED
Originally built under J/K/L (the docx's lettering). The live Ignyte page,
copy-pasted directly by the founder, confirmed the real 14-box A–N structure
and cross-verified exactly against `Ignyte_Rules.md`'s category weights. This
file has been relettered accordingly: **G** (ElevenLabs components), **I**
(Guardrails), **H** (Technical architecture / "How it integrates"). No
content changed — only the section headers, to match the confirmed real
canvas.
