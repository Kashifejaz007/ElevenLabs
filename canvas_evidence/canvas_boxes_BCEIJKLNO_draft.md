# ResolveAI — Boxes B, C, E, I, J, K, L, N, O
Drafted from verified code/README evidence only. D, F, G, H, M, P(track/use-case
naming), and Q remain blocked pending real inputs (see status note at bottom).
Everything here is [DEMO] or [DOCUMENTED] status, not [VERIFIED] institutional fact —
none of it depends on the missing F interview.

---

## B — Idea in one line
**24 words** · structure: "An agent that ___ for ___, so that ___" · no adjectives

> An agent that calls, verifies without a PIN, and freezes the card for customers
> facing card compromise, so that fraud stops before funds move.

---

## C — What currently breaks
**98/120 words** · existing workflow, not ResolveAI · channel + delay + person waiting + exact failure point

> Channel: outbound phone call from the fraud contact centre. When the fraud-detection
> system flags a transaction, the case joins a queue for a human agent; wait time
> tracks call-centre load. The customer is not yet contacted, unaware their card is
> flagged while the transaction is still pending or clearing. The exact failure point:
> the authorization window can close before an agent dials out, so contact often lands
> after settlement, turning a preventable loss into a dispute. Verification then still
> relies on static, PIN-adjacent security questions, which do not distinguish the bank
> from a fraudster running the same script.

Note: this describes the *generic* industry pattern your own draft already used —
it is not sourced to a specific institution. It should still be cross-checked against
the real F interview once you have it; if the interviewee describes a different
failure point (e.g. the queue itself, not the authorization window), C needs to move.

---

## E — Who buys it
**56/60 words** · Institution / signing title / budget line

> **Institution:** a UAE retail bank or card issuer running active fraud detection
> with human-dependent outbound response.
> **Signing title:** Head of Fraud Operations, Head of Cards, or CISO — the role
> owning fraud-loss exposure and response-time SLAs.
> **Budget line:** fraud operations or digital-channel transformation budget,
> justified against prevented loss and reduced contact-centre load, not core-banking
> capital spend.

This is a target-buyer statement, not a claimed relationship. Nothing here asserts
an actual bank partnership — don't let it read that way in final copy.

---

## I — Call flow (5 rows, ≤15 words each, Step 1 = opening disclosure, human handover marked)

1. **IDENTIFY** (14w) — Agent discloses it is an automated call from the bank's
   fraud team, states purpose.
2. **VERIFY** (12w) — Customer reads back a one-time code; never a PIN, CVV, or
   password.
3. **UNDERSTAND** (12w) — Agent retrieves and explains the flagged transaction,
   asks if it was theirs.
4. **RESOLVE** (11w) — Customer confirms unauthorized; idempotent freeze executes,
   or high-value gate blocks it.
5. **CONFIRM / ESCALATE (H)** (12w) — Agent confirms freeze and block, or hands
   off to human review queue.

---

## J — ElevenLabs components (unchanged from prior draft — already selective, already justified)

Selected: Agent Workflows, Eleven v3 voice, Scribe v2 Realtime, Knowledge Base/RAG,
scoped webhook tools, Agent Testing.

**52/60 words**, justifying the two least-obvious:

> Agent Workflows enforces branching state (verify → resolve → escalate)
> structurally, not just via prompting, so the authorization-gate and dispute paths
> are guaranteed, not hoped for. Agent Testing runs pre-launch against the full
> guardrail suite — 36 adversarial tests plus a dedicated 7-test webhook-auth suite —
> producing Box K's enforcement evidence directly.

---

## K — Six mechanisms, ≤20 words each, actual enforcement described

| Mechanism | Enforcement (≤20 words) | Status |
|---|---|---|
| Opening disclosure | System prompt Step 1 requires stating it's an automated fraud-team call before any account detail is revealed. (17w) | Implemented |
| Consent to continue | Step 1 confirms the customer is willing to continue; consent to be contacted at all is institutional, not agent-enforced. (19w) | Implemented (partial — see note) |
| Verification without secrets | `verify_customer` compares a one-time code server-side; no tool can accept or validate a PIN, CVV, or password. (17w) | Implemented |
| Human approval | `confirm_fraud_and_freeze` is blocked unconditionally above a value threshold; only a human-queue action can complete it. (15w) | Implemented |
| Opt-out | **NOT YET IMPLEMENTED** — hanging up ends the call, but no persistent do-not-call/opt-out list exists in this sandbox. (18w) | **GAP** |
| Escalation trigger | `escalate_to_human` fires on dispute, unsupported fraud type, failed verification, high-value gate, or any tool returning `ok:false`. (16w) | Implemented |

**Flagging this clearly rather than papering over it:** "Consent to be called" and
"Opt-out" are not the same thing as "consent to continue once already on the call,"
which is all the code currently does. A judge who knows banking compliance will ask
about outbound-contact consent and DNC (do-not-call) handling. Two honest options:
1. Submit K as-is with the gap marked, and list opt-out as a named Build Sprint
   deliverable in O.
2. Spend part of the remaining time actually adding a minimal opt-out flag/tool
   before submission, so K can say "implemented" truthfully.
Your call — I won't silently upgrade the status to make the box look stronger.

---

## L — Architecture diagram (text description; see `full_canvas_draft.md` for the
existing ASCII diagram, which already has three of the seven required elements)

Required elements and where each currently stands:

| Required in L | In existing diagram? |
|---|---|
| Caller/channel | Yes — "CUSTOMER" → voice/PSTN |
| J components (ElevenLabs Agent, Scribe) shown | Yes |
| Institution systems | Partial — labelled generically as "Fraud Case API / Card Freeze API (sandbox) / Human Escalation Queue," not named systems (no real institution to name yet) |
| Every arrow direction | Yes, arrows are directional |
| Personal-data boundary | Yes — boundary ② marked as the only point customer data reaches Zone 3, post-verification only |
| Human approval gate | Shown inside "Guardrail Engine," should be pulled out as its own labelled box for submission clarity |
| **Dependency-down behavior** | **Missing — needs to be added** |

**Dependency-down behavior, stated honestly from the code:** there's no
circuit-breaker or retry logic. The only mechanism is that any tool call failure
returns `ok:false`, and the system prompt instructs the agent to treat that as a
stop signal and escalate — not retry, not improvise. That's a real, working
behavior, but it's agent-level, not infrastructure-level resilience. State it that
way in L rather than implying automated failover exists.

**Action needed before Q:** redraw the existing ASCII diagram as a clean
submission-quality figure (image or clean box diagram) with the Human Approval Gate
as its own labelled node and a "tool call fails → ok:false → escalate" note on the
dependency-down path. I can build this as an actual diagram once you confirm you
want it in a specific format (image for the canvas upload vs. inline text).

---

## N — Three risks, ≤25 words each, with mechanisms

| Risk | Mitigation |
|---|---|
| Fraudster impersonates the bank's own outbound call | Customer can hang up and call the bank's official number back independently; stated explicitly during the call. (17w) |
| High-value transaction frozen without proper authority | Human-authorization gate blocks unilateral freeze above threshold regardless of confirmation confidence; escalates to human queue. (15w) |
| No persistent opt-out / do-not-call mechanism (compliance gap) | Currently unimplemented in the sandbox; flagged for Build Sprint as a required addition before any real customer contact. (18w) |

The third risk is new — added because K's audit surfaced it. Better to name it as
a known risk with a plan than to leave it undisclosed and have a judge find it.

---

## O — What works by 14 October
**56/60 words** · genuinely end-to-end vs. genuinely mocked

> By 14 October, end-to-end: simulated fraud signal, multilingual call, server-side
> verification, transaction explanation, idempotent freeze for standard cases, and
> escalation for disputed, unsupported, or high-value cases — fully audited. Still
> mocked: real core-banking integration, live telephony/PSTN, and a persistent
> opt-out list. Real ElevenLabs voice connection status to be confirmed during Build
> Sprint, not claimed live now.

---

## Status note
- **A**: waiting on your confirmation of exact Track/Use Case wording from the
  official canvas — not guessed.
- **D, F, G, M**: still blocked, as instructed. Not touched.
- **H**: also depends on real interview specifics (actual system names) — not
  attempted here even though it wasn't explicitly listed as blocked, because it has
  the same evidence dependency as F/G. Flagging this rather than guessing institution
  system names.
- **P**: team box — see separate note in main reply re: Kashif Ejaz / Project Director
  and the "No" on previous shipped work.
- **Q**: repo not yet presented as evidence — see repo packaging note in main reply.
