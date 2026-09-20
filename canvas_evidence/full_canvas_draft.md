# ResolveAI — Idea Canvas Draft (A–Q)

Banking & Insurance track · Real-Time Fraud Intervention

**How to use this file:** each box is DRAFT (ready to copy in, word-count
checked) or 🔴 EVIDENCE REQUIRED (do not submit a placeholder — fill
with something real first). See the earlier revision's note: this
canvas supersedes the Government Services draft — this project pivoted
tracks based on the actual official brief listing both tracks, with
Banking & Insurance chosen deliberately for this submission.

---

## SECTION 1 — THE OPPORTUNITY

### A — Submission details
- Track: Banking & Insurance
- Use case: Real-Time Fraud Intervention
- Product name: ResolveAI
- Team name: 🔴 EVIDENCE REQUIRED
- Submission date: [before 23 Sep 2026]

### B — Idea in one line (25 words max)
**DRAFT — 22 words**

> ResolveAI calls customers within minutes of a suspected card
> compromise, verifies them without a PIN, and freezes the card before
> losses occur.

### C — What currently breaks (120 words max, problem only)
**DRAFT — 118 words**

> When a bank's fraud system flags a suspicious card transaction, the
> gap between detection and customer contact is where losses occur.
> Today, flagged transactions often wait in a queue for a human agent
> to call, and outbound contact can take considerably longer than the
> window in which a fraudulent transaction can still be stopped. When a
> customer is finally reached, verification frequently still relies on
> static credentials like security questions or, in weaker processes, a
> request for a PIN — creating both a security risk and a genuine
> customer-trust problem, since legitimate banks are also impersonated
> by fraudsters using the same techniques. Non-English-speaking
> customers face additional delay if language coverage is limited to
> business hours or specific agents.

🔴 Cross-check against your F conversation before finalizing.

### D — Today's baseline (numbers only)
🔴 **EVIDENCE REQUIRED** — see `D_baseline_methodology.md`. Do not fill
until you have a real sourced figure or the pilot design, labelled
accordingly.

```
Contact delay (signal → customer reached): [X min] — source: [ ]
Freeze delay (contact → card frozen): [X min] — source: [ ]
Escalation rate: [X%] — source: [ ]
Agent handling time per case: [X min] — source: [ ]
```

### E — Who buys it (60 words max)
**DRAFT — 56 words**

> Institution: a UAE retail bank or card issuer with active fraud
> detection but human-dependent outbound response. Buyer: Group Head of
> Fraud, Head of Cards, or CISO — the role owning fraud-loss exposure
> and response-time SLAs. Budget would sit within fraud operations or
> digital-channel transformation, justified against prevented-loss and
> reduced contact-centre load, not new core-banking capital spend.

---

## SECTION 2 — THE AGENT

### F — Who you spoke to (real conversations required)
🔴 **EVIDENCE REQUIRED** — see `F_interview_guide.md`.

```
Spoke with: [role], [institution type], [date]
Key things confirmed: [ ]
Key things corrected from our assumptions: [ ]
```

### G — What we got wrong (50 words max)
🔴 **EVIDENCE REQUIRED** — only has content once F happens.

### H — Current workflow (diagram, before the agent exists)
**DRAFT — verify against F, then finalize**

```
FRAUD DETECTION SYSTEM FLAGS TRANSACTION
            │
            ▼
      CASE QUEUED FOR HUMAN REVIEW
            │
            ▼
      ┌──────────────┐
      │ AGENT FREE?  │
      └───────┬──────┘
        NO    │    YES
        │     │     └──→ AGENT REVIEWS CASE DETAILS
        ▼                        │
   WAITS IN QUEUE                ▼
   (delay accumulates,    AGENT CALLS CUSTOMER
    transaction may              │
    still be pending)            ▼
        │              CUSTOMER REACHED?
        │                NO  │    YES
        │                │   │     └──→ VERIFICATION
        │                ▼                (static Q&A, sometimes
        │           RETRY LATER             PIN-adjacent questions)
        │           (delay compounds)        │
        │                                     ▼
        │                           CUSTOMER CONFIRMS / DENIES
        │                                     │
        │                                     ▼
        │                          MANUAL FREEZE ACTION BY AGENT
        │                                     │
        └─────────────────────────────────────┤
                                               ▼
                                        CASE CLOSED / LOGGED
```

### I — Call flow, 5 steps (15 words per step, Step 1 = opening disclosure)
**DRAFT — all under limit**

1. **IDENTIFY** (13 words) — Agent discloses it's an AI, states the
   bank and reason without revealing details yet.
2. **VERIFY** (11 words) — Customer reads back a one-time code; never a
   PIN, CVV, or password.
3. **UNDERSTAND** (10 words) — Agent retrieves and explains the
   flagged transaction, asks if it was theirs.
4. **RESOLVE** (12 words) — Customer confirms unauthorized; schema-locked
   freeze executes, or human-authorization gate blocks it.
5. **CONFIRM/ESCALATE** (10 words) — Agent confirms freeze and blocked
   transaction, or hands off to human review.

### J — ElevenLabs components (selected, justify two least obvious in 60 words)
**DRAFT — 52 words for justification**

Selected: Agent Workflows, Eleven v3 voice, Scribe v2 Realtime,
Knowledge Base/RAG, scoped webhook tools, Agent Testing.

> Agent Workflows enforces branching state (verify → resolve →
> escalate) structurally, not just via prompting, so the authorization-gate
> and dispute paths are guaranteed, not hoped for. Agent Testing runs
> pre-launch against the full guardrail suite — 36 adversarial tests
> plus a dedicated 7-test webhook-auth suite — producing Box K's
> enforcement evidence directly.

### K — Guardrails (20 words per row, mechanism required)
**DRAFT — 7 rows; see note below if the template caps this at 6**

| Guardrail | Mechanism (word count) |
|---|---|
| No PIN/CVV/password collection | No tool exists that can collect, verify, or process these; structurally absent, not just prompted against (11) |
| No unauthorized freeze target | case_id is not a tool parameter at all; case resolved server-side from a single-use, hijack-protected incident (18) |
| Verification required, hardened | Server-side code comparison, never an agent-asserted boolean; no tool exposes the correct code back (14) |
| Dispute handling | Customer says transaction is theirs → freeze tool suppressed, case flagged for human review, no argument attempted (16) |
| Unsupported fraud-type fallback | Fraud types with no approved policy trigger escalation, not improvisation; enforced before any freeze attempt (15) |
| **High-value human authorization gate** | Transactions above threshold cannot be frozen by agent alone; blocked unconditionally and escalated for human review (16) |
| Full auditability + idempotency | Every call logs success/denial; freezing an already-frozen card returns ALREADY_FROZEN with zero duplicate side effects (16) |

🔴 **Note:** if the official template limits K to 6 rows, merge "No
unauthorized freeze target" into "Verification required" (both concern
the same access-control boundary) and keep the High-Value Authorization
Gate as its
own row — it is the guardrail most directly answering the challenge's
own "before the money moves" framing and the strongest evidence against
"the AI must never independently approve a financial decision."

---

## SECTION 3 — THE CASE

### L — Technical architecture (diagram, labelled arrows, boundary marked)
**DRAFT**

```
 ZONE 1: VOICE & AGENT              ZONE 2: LOGIC & POLICY           ZONE 3: BANKING SYSTEMS
┌────────────────────┐             ┌───────────────────────┐       ┌───────────────────────────┐
│     CUSTOMER         │             │                       │       │                           │
└─────────┬────────────┘             │                       │       │                           │
          │ voice/PSTN                │                       │       │                           │
          ▼                          │                       │       │                           │
┌────────────────────┐   text  ①───▶│  INTENT / STATE       │       │                           │
│ ElevenLabs Agent    │────────▶│    │  MANAGER              │       │                           │
│ (Workflow + Voice)  │         │    └──────────┬────────────┘       │                           │
└─────────┬────────────┘         │               │                   │                           │
          ▼                     │    ┌──────────▼────────────┐       │                           │
┌────────────────────┐          │    │ GUARDRAIL ENGINE       │       │                           │
│ Scribe v2 Realtime  │──────────┘    │ (7 mechanisms, incl.   │       │                           │
│ (STT)               │               │  auth. gate)            │       │                           │
└────────────────────┘               └──────────┬────────────┘       │                           │
                                                  │                   │                           │
                                       ┌──────────▼────────────┐  ②◀── │                           │
                                       │ TOOL / WEBHOOK LAYER   │───────▶ Fraud Case API            │
                                       │ (scoped, schema-locked)│───────▶ Card Freeze API (sandbox) │
                                       └──────────┬────────────┘───────▶ Human Escalation Queue     │
                                                  │                   │                           │
                                       ┌──────────▼────────────┐  ③◀── │                           │
                                       │ AUDIT LOG (append-only)│───────▶ Audit/Analytics Store      │
                                       └────────────────────────┘       └───────────────────────────┘
```

Three marked boundaries: ① voice/transcript entry (spoken content
becoming structured text), ② tool layer → banking systems (the only
point customer data reaches Zone 3, post-verification only), ③
record → audit store (in-memory in this sandbox; production would
persist durably).

**Not pictured, to keep the diagram legible:** an Incident Engine sits
in front of Zone 2 — before any call happens, it binds the call to
exactly one case server-side via a single-use, expiring, unguessable
`incident_id`. The agent never sees or supplies a case identifier at
any point. See `fraud_events.py` and README §3.

### M — Success metrics (max 3 KPIs, baseline must match D exactly)
🔴 **EVIDENCE REQUIRED** — depends on D.

```
KPI 1: Reduced contact delay
  Baseline (from D): [ ] → Target: customer reached within ~1 minute of signal

KPI 2: Reduced freeze delay
  Baseline (from D): [ ] → Target: freeze completed within the same call (supported, non-gated cases)

KPI 3: Appropriate escalation rate
  Baseline (from D): [ ] → Target: correctly routed, not minimized — ambiguous cases SHOULD escalate
```

### N — Risks (25 words per row)
**DRAFT — under limit**

| Risk | Mitigation (word count) |
|---|---|
| Fraudster impersonates the bank's own outbound call | Customer can always hang up and call the bank's official number back to verify independently — stated explicitly in the call (21) |
| High-value transaction frozen without proper authority | Human-authorization-gate guardrail blocks unilateral freeze above threshold regardless of confirmation confidence (11) |
| Tool/API failure mid-call | Failure triggers scripted fallback and automatic human escalation, not a silent retry or false success (15) |
| Language misdetection | Customer can explicitly request a language switch at any point during the call (13) |
| Leaked or guessed case identifier redirects a call | case_id removed entirely; unguessable incident_id is single-use, hijack-protected, and time-limited (13) |

### O — What works by 14 October (60 words max)
**DRAFT — 58 words**

> By 14 October: a sandboxed agent that receives a simulated fraud
> signal, places a multilingual call, verifies the customer via
> server-side code comparison, explains the flagged transaction,
> executes an idempotent freeze for supported/standard cases, and
> escalates disputed, unsupported, or high-value cases requiring human
> authorization — fully recorded and audited. Real core-banking
> integration remains out of scope for this build.

### P — Team
🔴 **EVIDENCE REQUIRED** — real members and shipped work only.

### Q — Proof of build (2 links required)
🔴 **EVIDENCE REQUIRED**, path is ready:

```
Link 1 (deployed project):
  Deploy server.py to Render/Railway per the sandbox README —
  now serves both the backend API AND the demo frontend from one URL.

Link 2 (60-second walkthrough):
  Record narrating the L diagram while demonstrating the live demo
  page — verify → explain → freeze → (or authorization-gate block) → audit.
```

---

## Final pre-submission audit

- [ ] Every box under its word limit (recount after any edit)
- [ ] D and M use the exact same metric definitions and population
- [ ] G reports a real correction from F, not a generic statement
- [ ] K's mechanisms match what's actually implemented (check row count
      against the real template — see note under K)
- [ ] N includes the risk sourced from the F conversation
- [ ] Both Q links are live and open correctly
- [ ] English + Arabic stated somewhere (I, L, system prompt)
- [ ] No box says "the agent will..." without a mechanism
- [ ] Team name and use case correct on every page
- [ ] One canvas, one use case (Real-Time Fraud Intervention), one team
