# ResolveAI — Master Canvas Draft (v2 — real 14-box A–N structure)

**Structure confirmed** directly from the live Ignyte challenge page
(user-provided copy-paste, cross-checked category-by-category against
`Ignyte_Rules.md` — both agree exactly on weights and box count). The earlier
17-box docx is **not** the authoritative template — it added three boxes
(interview record, what-you-got-wrong, workflow-today diagram) that don't
exist in the real submission. That work isn't wasted; it's folded in below as
supporting evidence behind C and D, where it belongs.

---
## A — Submission details *(Structured · Eligibility, pass/fail)*

| Field | Value | Field | Value |
|---|---|---|---|
| Team name | Kashif Ejaz team | Contact email | utubemonetize@gmail.com |
| Track | **1 — Banking & Insurance** ✅ | Based in | Pakistan (Karachi) |
| Use case | Real-time fraud intervention through immediate multilingual customer verification — **free-text description, not a numbered field**: confirmed both by your own portal check and by the live page's own "Step 1: choose one use case" wording, which never mentions a 1–8 list | Stage | **Stage 1 — The Idea Canvas** ✅ |
| Languages covered | English (Arabic per system prompt — see F) | Prior ElevenLabs use (Y/N) | Y |
| Team size | 1 | Website or repo | https://github.com/Kashifejaz007/ElevenLabs *(not yet populated with the actual files)* |

**Status: all fields resolved.** Nothing guessed — Track, Stage, and Use case
were each confirmed against real checked sources, not assumed.

---
## B — The idea in one line *(25 words max · Problem fit 25%)*
> An agent that calls, verifies without a PIN, and freezes the card for
> customers facing card compromise, so that fraud stops before funds move.
**24/25 words.**

---
## C — What breaks today *(120 words max · Problem fit 25%)*
> Channel: outbound phone call from the fraud contact centre. When the
> fraud-detection system flags a transaction, the case joins a queue for a
> human agent; wait time tracks call-centre load. The customer is not yet
> contacted, unaware their card is flagged while the transaction is still
> pending or clearing. The exact failure point: the authorization window can
> close before an agent dials out, so contact often lands after settlement,
> turning a preventable loss into a dispute. Verification then still relies on
> static, PIN-adjacent security questions, which do not distinguish the bank
> from a fraudster running the same script.
**98/120 words.**

*Grounding evidence (not a separate scored box):* directly consistent with
Sumeira Noman's (Personal Banking Officer, 19-Sep-2026) description of alert
review, customer contact by registered mobile, and "customer reachability" as
the main delay — see the full interview record kept in
`canvas_boxes_ADFGH_official_draft.md`.

---
## D — Today's baseline *(Numbers only · Problem fit 25% · must match J exactly)*

| What you measured | Value today | Where the number comes from |
|---|---|---|
| Alert-to-initial-verification time (customer answers) | 5–15 minutes | Interview, Sumeira Noman, Personal Banking Officer, 19-Sep-2026 |
| Contact attempts before an unanswered case escalates | 2–4 attempts | Interview, Sumeira Noman, Personal Banking Officer, 19-Sep-2026 |
| Confirmed-fraud-to-initial-escalation time | 5–15 minutes (conditional on info/systems available) | Interview, Sumeira Noman, Personal Banking Officer, 19-Sep-2026 |

No invented total — she explicitly said the full resolution time is longer
and unquantified. These three numbers must reappear identically in **J**.

---
## E — Who buys this *(60 words max · Commercial 20%)*
> **Institution:** a UAE retail bank or card issuer running active fraud
> detection with human-dependent outbound response.
> **Signing title:** Head of Fraud Operations, Head of Cards, or CISO — the
> role owning fraud-loss exposure and response-time SLAs.
> **Budget line:** fraud operations or digital-channel transformation budget,
> justified against prevented loss and reduced contact-centre load.
**56/60 words.**

---
## F — The call flow *(15 words per step · Agent design 25%. Was docx-I.)*
Step 1 = opening disclosure. Human handover marked (H).

1. **IDENTIFY** — Agent discloses it is an automated call from the bank's fraud team, states purpose.
2. **VERIFY** — Customer reads back a one-time code; never a PIN, CVV, or password.
3. **UNDERSTAND** — Agent retrieves and explains the flagged transaction, asks if it was theirs.
4. **RESOLVE** — Customer confirms unauthorized; idempotent freeze executes, or high-value gate blocks it.
5. **CONFIRM / ESCALATE (H)** — Agent confirms freeze and block, or hands off to human review queue.

---
## G — ElevenLabs components *(Tick + 60 words · Agent design 25%. Was docx-J.)*
Ticked against the real 8-category menu confirmed on the live page
(Agent design & behaviour / Voice & language / Listening / Knowledge / Tools
& actions / Deployment / Model layer / Evaluation):

**Ticked (7 of 8):** Agent design & behaviour (Agent Workflows) · Voice &
language (Eleven v3 TTS) · Listening (Scribe v2 Realtime) · Knowledge
(Knowledge base + RAG) · Tools & actions (webhook/server tools) · Deployment
(native Twilio integration) · Evaluation (Agent Testing)
**Not ticked:** Model layer — no LLM-cascading/fallback logic exists in the
code; not included just to look thorough.

> Knowledge: the agent must quote exact policy wording — freeze thresholds,
> escalation triggers — from real bank documents rather than improvise, so RAG
> over the four files in knowledge_base/ with source attribution keeps every
> claim traceable to a specific SOP. Evaluation: Agent Testing runs the full
> guardrail suite — 36 tool-call tests plus 7 webhook-auth tests — before
> release.
**59/60 words**, justifying the two least obvious (Knowledge, Evaluation).

---
## H — How it integrates *(Diagram · Agent design 25%. Was docx-L.)*
Three zones: Caller & channel / ElevenLabs platform / Institution systems.
See `box_L_architecture.png` (filename kept as-is; content is Box H now).
Shows: all 7 ticked G components, arrow directions, personal-data boundary
(filled dot), human-approval gate, dependency-down behaviour (`ok:false` →
escalate, no auto-retry).

**Two disclosed gaps, not papered over:**
1. **Tool/privilege boundary isn't drawn as its own visual element** —
   discovered during the Step 11 mapping audit, still unfixed.
2. **Institution systems shown by category only** (fraud/transaction
   monitoring, card-management, CRM, contact-centre/dialer, case-management)
   — Sumeira Noman withheld exact vendor/system names as confidential.

---
## I — Guardrails *(20 words per row · Guardrails 20%. Was docx-K.)*

| Requirement | How your design enforces it |
|---|---|
| Opening disclosure | System prompt Step 1 requires stating it's an automated fraud-team call before any account detail is revealed. |
| Consent to be called | Step 1 confirms the customer is willing to continue; consent to be contacted at all is institutional, not agent-enforced. |
| Verification without secrets | `verify_customer` compares a one-time code server-side; no tool can accept or validate a PIN, CVV, or password. |
| Human approval point | `confirm_fraud_and_freeze` is blocked unconditionally above a value threshold; only a human-queue action can complete it. |
| Opt-out path | **IMPLEMENTED (Step 16).** `customer_opts_out` works before or after verification and escalates immediately; when the incident can be securely bound it also persistently flags the customer (`fraud_events.record_opt_out`) so a future incident for them is routed to a human, not another AI call. Covered by 8 new tests (44/44 in `test_guardrails.py`). Honest scope note: this is a code-level and workflow-spec mechanism, verified in the isolated backend — it has never been exercised against a live ElevenLabs agent, since no live agent exists yet. |
| Escalation trigger | `escalate_to_human` fires on dispute, unsupported fraud type, failed verification, high-value gate, or any tool returning `ok:false`. |

---
## J — Success metrics *(Max 3 KPIs · Commercial 20% · baseline must match D exactly. Was docx-M.)*

| KPI | Baseline (from D) | Target | How it is measured |
|---|---|---|---|
| Alert-to-initial-verification time | 5–15 minutes | Under 5 minutes, including out-of-hours | Timestamp: alert received → verification completes, per case, pilot period |
| Contact attempts before escalation on no-answer | 2–4 attempts | 1 attempt, via immediate multilingual outbound call | Count of outbound call attempts logged per case, pilot period |
| Confirmed-fraud-to-escalation time | 5–15 minutes (conditional) | Under 2 minutes, unconditional on staff availability | Timestamp: fraud confirmed → escalation logged, per case, pilot period |

Targets are proposed pilot goals, not measured results — label them that way.

---
## K — Risks *(25 words per row · Guardrails 20%. Was docx-N.)*

| Risk | How you handle it |
|---|---|
| Fraudster impersonates the bank's own outbound call | Customer can hang up and call the bank's official number back independently; stated explicitly during the call. |
| High-value transaction frozen without proper authority | Human-authorization gate blocks unilateral freeze above threshold regardless of confirmation confidence; escalates to human queue. |
| No persistent opt-out / do-not-call mechanism (compliance gap) | **Fixed Step 16** — `customer_opts_out` now records a persistent flag per customer; future incidents for them are routed to a human channel instead of another AI call. |

---
## L — What will be working by 14 October *(60 words max · Commercial 20%. Was docx-O.)*
> By 14 October, end-to-end: simulated fraud signal, multilingual call,
> server-side verification, transaction explanation, idempotent freeze for
> standard cases, and escalation for disputed, unsupported, or high-value
> cases — fully audited. Still mocked: real core-banking integration, live
> telephony/PSTN, and a persistent opt-out list. Real ElevenLabs voice
> connection status to be confirmed during Build Sprint, not claimed live now.
**56/60 words.**

---
## M — Team *(Structured · Team 10%. Was docx-P.)*

| Name | Role on this build | Shipped previously (link) |
|---|---|---|
| Kashif Ejaz | Project Director | No |

---
## N — Proof of build *(Team 10%. Was docx-Q. Rule tightened — see note.)*
**Live page's exact wording:** *"Box N requires a working link. A live
product, repository or previously deployed demo. Submissions without a
working link score zero for this box."* — this describes **one** required
working link (repo/live product/demo), not explicitly "two links including a
60-second recording" as the old docx claimed. Safer reading: get one working
link at minimum; the H-diagram walkthrough recording is good practice on top
of that, not confirmed mandatory.

**Status: BLOCKED.** The repo (https://github.com/Kashifejaz007/ElevenLabs)
is not yet populated. This is a hard zero-score box until that happens —
nothing else in the canvas can compensate for it.

---
## FINAL STATUS — honest, box by box, real letters

| Box | Status |
|---|---|
| A | Complete, all fields confirmed |
| B | Complete |
| C | Complete |
| D | Complete, sourced |
| E | Complete |
| F | Complete |
| G | Complete, corrected against real component menu |
| H | Diagram exists, 2 disclosed gaps (tool/privilege boundary not drawn; system names withheld as confidential) |
| I | Complete — all 6 rows, opt-out path implemented Step 16 |
| J | Drafted — targets are proposed, not measured |
| K | Complete |
| L | Complete |
| M | Complete |
| N | **BLOCKED — hard zero without a working link.** Highest-priority remaining task. |

**Twelve of fourteen boxes genuinely done.** I is one row short of solid. N
is the one real hard blocker — and per the live rules, it's not a
"nice to have," it's a zero if missed. That's the next real priority, above
everything else left on this project.
