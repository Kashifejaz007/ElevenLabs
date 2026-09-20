# STAGE2_ELEVENLABS_COMPONENT_AUDIT.md

Method: every row below was checked directly against the actual files in
this repo (`grep`-verified, not remembered/assumed) as of 19-Sep-2026.
No ElevenLabs account is connected to this sandbox — nothing below is
claimed as "implemented" unless it's real code/config sitting in the repo.
Anything that requires a live ElevenLabs connection to actually exist is
marked **Stage 2 planned**, even where a full spec for it already exists.

---

## 1. Agent design & behaviour

| Component | Required for ResolveAI? | Current status | Evidence / implementation needed |
|---|---|---|---|
| Agents Platform (the base conversational agent) | Yes — nothing runs without it | **Stage 2 planned** | No live agent created yet; everything below assumes one will be |
| Agent Workflows (visual branching builder) | Yes — the 5-step flow must be a hard state machine, not just prompt discipline | **Needs implementation** | Full 6-node spec already written (`agent_workflow_spec.md`) — needs to be built inside the live ElevenLabs builder |
| Sub-agents | **Not required** | Not required | No evidence the workflow needs a second specialized agent handoff; single agent + human escalation covers every branch |
| Per-node tool scoping | Yes — core security layer | **Needs implementation** | Fully specified per node in `agent_workflow_spec.md`; not yet configured in a live builder |

---

## 2. Voice & language

| Component | Required for ResolveAI? | Current status | Evidence / implementation needed |
|---|---|---|---|
| Eleven v3 TTS | Yes — the call has no voice without it | **Stage 2 planned** | No live agent/voice connected yet |
| Voice Library (voice selection) | Yes, at minimum a standard voice must be picked | **Needs implementation** | Not yet selected |
| Voice Design (custom voice creation) | **Not required** | Not required | No evidence a custom-built voice is needed over a library voice |
| Multilingual handling (incl. Arabic) | Yes — this is the product's central claim, "customer's own language" | **Needs implementation / Stage 2 planned** | System prompt already specifies English + Arabic switching (`system_prompt.md`, "Language" section) — never tested against a live voice model |

---

## 3. Listening

| Component | Required for ResolveAI? | Current status | Evidence / implementation needed |
|---|---|---|---|
| Scribe v2 Realtime STT | Yes — must accurately hear the spoken verification code and yes/no answers | **Stage 2 planned** | Not yet connected |
| Keyterm biasing | Yes, recommended — verification codes and merchant/product names are exactly the failure case biasing exists for | **Needs implementation** | No keyterm list built yet; would need real transaction/merchant vocabulary once connected |

---

## 4. Knowledge

| Component | Required for ResolveAI? | Current status | Evidence / implementation needed |
|---|---|---|---|
| Knowledge Base + RAG | Yes — system prompt requires the agent explain transactions "using only wording from the fraud response policy knowledge base," not improvise | **Needs implementation** | 4 real policy files exist and are substantive (`knowledge_base/`, 185 lines total: authentication, card-freeze, escalation, fraud-response policy) — but they are plain files in the repo, **not yet uploaded into ElevenLabs' actual Knowledge Base feature**. The system prompt references them conceptually; the live RAG connection doesn't exist yet. |
| Source attribution | Yes — needed so the agent's policy claims are traceable to a specific document | **Stage 2 planned** | Depends entirely on the Knowledge Base connection above existing first |

---

## 5. Tools & actions

| Component | Required for ResolveAI? | Current status | Evidence / implementation needed |
|---|---|---|---|
| Client tools | **Not required** | Not required | Everything runs server-side; no evidence of a need for client-executed logic |
| Webhook (server) tools | Yes — this is the entire enforcement mechanism | **Already implemented (backend half) / Needs implementation (ElevenLabs-side half)** | The 5 Flask endpoints (`verify_customer`, `get_fraud_case`, `confirm_fraud_and_freeze`, `customer_disputes_fraud`, `escalate_to_human`) are real, working code in `server.py`, fully specified for ElevenLabs binding in `tool_configuration.md`, and covered by passing tests. What's missing is wiring them into a live agent — that half hasn't happened. |
| MCP servers | **Not required** | Not required | No evidence the use case needs an external MCP integration beyond the 5 direct webhook tools |
| Core-banking / case-management mock | Yes — needed to demo without touching a real bank | **Already implemented** | `data/fraud_cases.py` — real mock case data, verified in repo |
| Privileged-action scoping (trust boundary for untrusted callers) | Yes — the customer must never be able to freeze an arbitrary card or bypass the high-value gate | **Already implemented (code level)** | `guardrails.py` enforces the value threshold and confirmation requirements — 36/36 guardrail tests pass. The second layer (ElevenLabs-side per-node scoping, see section 1) still needs live configuration to complete the full design. |

---

## 6. Deployment

| Component | Required for ResolveAI? | Current status | Evidence / implementation needed |
|---|---|---|---|
| Web/mobile SDKs (React, React Native, Swift, Kotlin) | **Not required** | Not required | ResolveAI is an outbound phone call to the customer's existing number, not an in-app embedded widget |
| WebRTC / WebSocket | **Not required** | Not required | Same reasoning — these serve embedded web/app voice, not outbound PSTN calls |
| Telephony — native Twilio integration or SIP trunking | Yes — the entire product is "the bank calls the customer" | **Needs implementation** | Assumed throughout the design (`README.md`, `agent_workflow_spec.md`) but no Twilio/SIP account has actually been connected or test-called |
| WhatsApp | **Not required** | Not required | No evidence in the interview or product spec that a text channel is needed; a proactive voice call is the whole point |
| Batch calling | **Not required** | Not required | ResolveAI reacts to individual real-time fraud alerts, not scheduled outbound campaigns |

---

## 7. Model layer

| Component | Required for ResolveAI? | Current status | Evidence / implementation needed |
|---|---|---|---|
| ElevenLabs LLM layer / BYO model | Yes, at a base level — some model has to run the conversation | **Stage 2 planned** | No model has been selected or connected; default platform model is likely sufficient, no evidence a BYO model is needed |
| Cascading / fallback | **Not required** | Not required | No evidence this use case needs multi-model fallback — the code-level guardrail response to any tool failure (`ok:false` → escalate) already handles failure modes, and it's a different mechanism from model cascading |

---

## 8. Evaluation

| Component | Required for ResolveAI? | Current status | Evidence / implementation needed |
|---|---|---|---|
| Agent Testing (ElevenLabs platform feature — tool-call tests, pass rates) | Yes — this is the evidence Stage 2 is explicitly assessed on | **Stage 2 planned — see important distinction below** | Not yet built as an ElevenLabs platform feature |
| Simulate Conversations | Yes, eventually, before any real customer is called | **Stage 2 planned** | Not implemented. `demo_output/*.json` exist but are **hand-authored example transcripts, not output from ElevenLabs' Simulate Conversations feature** — do not conflate the two in the canvas |
| Conversation analysis / evaluation criteria | Yes, eventually | **Stage 2 planned** | Not implemented |
| Analytics / versioning | Moderate — useful for iterating, not required to launch | **Not required for Stage 1 minimum** | Would become relevant only once a live agent exists to generate data |
| Post-call webhooks | **Not required** | Not required | The audit-trail design logs each action as it happens, in-call, via the same tool calls — no evidence a separate post-call summary webhook is needed |

**Important distinction, stated plainly:** what's actually already working is
**your own Python test suite** (`test_guardrails.py` — 36 tests, `test_server_auth.py`
— 7 tests, both passing, re-run fresh today) — this tests the backend guardrail
logic directly. It is real, and it is legitimate evidence of engineering
discipline. But it is **not** ElevenLabs' Agent Testing feature, and the canvas
should not describe it as such. Two different things; don't let them blur into
one claim.

---

## RECOMMENDED STAGE 2 MINIMUM COMPONENT SET

1. **Agents Platform + Agent Workflows** — the entire verify → resolve →
   escalate logic must be a structural state machine, not prompt discipline alone.
2. **Eleven v3 TTS** — no call happens without a voice.
3. **Scribe v2 Realtime (+ keyterm biasing)** — must accurately capture the
   spoken verification code; a mis-heard digit breaks the one security-critical
   step in the whole flow.
4. **Knowledge Base + RAG** — the agent must quote real policy wording, not
   improvise it, when explaining a flagged transaction.
5. **Webhook (server) tools** — the five backend actions are the entire
   mechanism by which anything actually happens; already built and tested,
   just needs live binding.
6. **Telephony — native Twilio integration** — the product's defining action
   is a real outbound call to the customer; nothing works without it.
7. **Per-node tool scoping + privileged-action scoping** — the security model
   depends on each workflow node exposing only the one tool it needs.
8. **Agent Testing** — this is the literal evidence category Stage 2 is
   assessed on; without it there's no way to demonstrate the guardrails work
   against the live agent, only against the backend in isolation.

Everything else audited above — sub-agents, MCP, client tools, WhatsApp,
batch calling, Voice Design, mobile SDKs, WebRTC/WebSocket, model cascading,
post-call webhooks, analytics/versioning — is marked **not required**, on
the same "appropriate use, not full coverage" principle both source
documents state.
