# ResolveAI — Proactive Voice Fraud Intervention

**Ignyte × ElevenLabs Future of Voice AI Challenge — Banking & Insurance
track — Real-Time Fraud Intervention**

> "A card gets compromised at 2am. The bank's agent calls within the
> minute, in the customer's language, proves the call is genuine
> without asking for a PIN, and freezes the card before the money
> moves." — this repository is a sandboxed, tested proof of exactly
> that mechanism.

**AI handles the conversation. ResolveAI handles the authorization.**

---

## 1. What this is

A working sandbox for the security-critical half of a voice fraud
agent: the deterministic backend that decides whether a verification
succeeded, whether a card gets frozen, and when a human must take over
— none of which is ever left to the model's own judgment. It does
**not** include ElevenLabs voice/STT/telephony config itself (that
needs a platform account) — it's the incident engine, guardrail engine,
tool layer, mock banking API, and a real demo frontend that would sit
behind an ElevenLabs agent, wired via documented webhook tools.

**Project history:** started as a Government Services concept, pivoted
to this Banking & Insurance use case once the official challenge
brief's two-track structure was confirmed. Then underwent a second,
external QA pass that found and fixed two real architectural gaps —
documented in full below, not glossed over.

## 2. The central architectural principle

```
NATURAL LANGUAGE → ELEVENLABS AGENT → TOOL REQUEST → RESOLVEAI BACKEND
                                                              │
                                                    POLICY / GUARDRAIL
                                                              │
                                                     AUTHORIZED ACTION
                                                              │
                                                        BANKING API
                                                              │
                                                           AUDIT
```

The AI can understand, communicate, and request. **It does not decide
whether a security-sensitive action is allowed** — the deterministic
backend does, every time, checked in code.

## 3. Security hardening — two rounds of real fixes, not just claims

**Round 1 (internal):** an earlier verification tool accepted a boolean
the agent asserted directly. Fixed — `verify_customer` now performs a
server-side comparison against a code the agent never sees.

**Round 2 (external QA review), two real gaps found and fixed:**

**Finding #1 — no server-side fraud-event → call binding.** Previously,
`case_id` was a parameter the agent supplied directly to `verify_customer`
— meaning an agent bug, or a manipulated webhook payload, could target
*any* case, not necessarily the one the call was actually about. Fixed
by adding `fraud_events.py`: a fraud incident is now created
server-side (simulating the bank's detection system notifying
ResolveAI), producing an unguessable `incident_id`. That incident binds
to exactly one `call_id` on first use — a second, different call
attempting to claim the same incident is rejected
(`INCIDENT_ALREADY_BOUND`), which is real replay/hijack protection, not
just a validation check. Incidents also expire after 15 minutes if
never used. **`case_id` is no longer a parameter on any tool at all** —
removed entirely, not just checked, which closes the gap structurally
rather than defensively. Verified by
`test_confirm_freeze_has_no_case_id_parameter`,
`test_incident_cannot_be_hijacked_by_a_different_call`, and a live HTTP
test that reproduces the exact hijack attempt and confirms it's blocked.

**Finding #2 — `customer_confirmed` only checked truthiness.** The code
originally did `if not customer_confirmed:` — which correctly rejects
Python `False`, but a malformed or manipulated JSON payload sending the
*string* `"false"` is truthy in Python and would have passed. Fixed:
`confirm_fraud_and_freeze` now requires a strict `bool` via
`isinstance()` before any truthiness check runs at all. Verified by
`test_freeze_rejects_string_false_specifically` and a live HTTP test
sending exactly that payload.

**Five more findings from the same review, also fixed:**
- **#3 — Gunicorn workers:** in-memory session/case/audit state can't
  be shared across processes; `Dockerfile`/`Procfile` now run a single
  worker, documented inline rather than silently wrong.
- **#4 — webhook authentication:** was entirely absent; now implemented
  via `RESOLVEAI_DEMO_MODE`/`RESOLVEAI_WEBHOOK_SECRET`, with 7
  dedicated integration tests hitting the real Flask `before_request`
  gate (see Section 4 below for the demo/production distinction).
- **#5 — verification codes visible in frontend JS:** addressed by
  making the demo/production distinction explicit rather than hiding
  it — see Section 4.
- **#6 — "dual authorization" was mis-named:** there is no second-
  reviewer approval endpoint in this sandbox, so calling it "dual
  authorization" overclaimed. Renamed throughout to **"high-value
  human authorization gate"** — an honest description of what's
  actually implemented (agent unconditionally blocked, escalated to a
  human queue), with a note that a real two-person control is a Stage
  2 enhancement, not something built here.
- **#7 — the demo UI didn't show the fraud-signal-to-call story:** the
  frontend now prints an explicit timeline (FRAUD SIGNAL RECEIVED →
  INCIDENT CREATED → OUTBOUND CALL INITIATED → CUSTOMER ANSWERED →
  VERIFICATION PASSED → CARD FROZEN → ...) and a banner distinguishing
  this scripted demo page from an actual ElevenLabs voice call.

**Seven guardrails, all implemented as code in `guardrails.py`, checked
before every tool executes:**

| # | Guardrail | Mechanism |
|---|---|---|
| 1 | No unilateral financial decision-making | No `approve_transaction`, `transfer_funds`, or similar tool exists — enforced by absence |
| 2 | No unauthorized freeze target | `case_id` is not a tool parameter at all; case resolved server-side from a single-use, hijack-protected incident |
| 3 | Verification required, hardened | Server-side code comparison, never an agent-asserted boolean |
| 4 | Dispute handling | Customer says transaction is theirs → freeze suppressed, escalate, no argument |
| 5 | Unsupported fraud-type fallback | No approved policy → escalate, not improvise |
| 6 | Full auditability | Every call, success or denial, logs to `guardrails.AUDIT_LOG` |
| 7 | **High-value human authorization gate** | Above a value threshold, agent unconditionally blocked from freezing — escalated to a human queue, not a completed two-signer workflow |
| 8 | **Opt-out path** *(fixed Step 16 — see Section 3b)* | `customer_opts_out` works before OR after verification; escalates the call immediately and, when the incident can be securely bound, persistently flags the customer via `fraud_events.record_opt_out` — a future incident for them returns `customer_opted_out: true` rather than routing to another AI call |

## 3b. Opt-out path (Step 16 fix — was a genuine, disclosed gap)

An external audit during canvas preparation found Guardrail Box K row 5
("opt-out path") had no implementation at all — hanging up ended a
call, but there was no way for a customer to decline AI interaction
mid-call and reach a human without it looking like just another
verification failure, and no persistent record that a customer had
opted out at all.

Fixed with two separate mechanisms, deliberately kept apart:

- **In-call (`tools.customer_opts_out`):** callable from every
  pre-terminal workflow node (see `agent_workflow_spec.md` Node 7),
  before OR after verification. A customer should not have to prove
  their identity to the AI they've just said they don't want to talk
  to. Escalates the call immediately either way.
- **Persistent (`fraud_events.record_opt_out` / `is_customer_opted_out`):**
  resolved securely through the same `incident_id` binding
  `verify_customer` already uses — never from an agent-supplied
  identifier, so it can't be spoofed the same way the original
  case_id-hijack gap could have been. A future `create_incident` for
  that customer returns `customer_opted_out: true`. This does **not**
  block the incident — a customer declining the AI channel still has a
  real fraud case that needs handling, just by a human, not silently
  dropped.

8 new tests cover both layers plus two adversarial cases: opting out
with an expired/unknown incident (must still escalate the call, just
skip the persistent flag), and attempting to piggyback a second call on
an incident already bound to a different one (must be rejected, same
hijack protection `verify_customer` gets).

## 4. Demo mode vs. production mode — the honest split (findings #4 + #5)

Two things in this sandbox are intentionally visible for judges that
would never be visible in production, and the server now makes that
split explicit rather than just hoping it's understood:

- **Verification codes** are shown in the frontend (`VERIFICATION_CODES`
  in `frontend/index.html`), labeled "DEMO MODE only" — standing in for
  an SMS a real customer's phone would receive. No tool available to
  the agent can retrieve this value either way.
- **Webhook authentication** is off by default (`RESOLVEAI_DEMO_MODE=true`),
  so the bundled demo frontend can call `/tools/*` directly without
  needing a secret wired into its own JavaScript (which would just move
  the same problem, not solve it).

Setting `RESOLVEAI_DEMO_MODE=false` + `RESOLVEAI_WEBHOOK_SECRET=<value>`
switches the server to production mode: every `/tools/*` and
`/api/fraud/events` request must carry a matching
`X-ResolveAI-Secret` header, or it's rejected with 401. **The bundled
demo frontend does not work in this mode as-is** — it would need to
call through an authenticated proxy route instead of `/tools/*`
directly. That's flagged honestly as a roadmap item, not built here.

## 5. What's real vs. simulated (read this before citing anything)

**Real, tested, running:**
- Incident engine (`fraud_events.py`) — unguessable IDs, single-use
  binding, expiry, all tested including a reproduced hijack attempt
- Guardrail logic (`guardrails.py`) — 7 mechanisms, all code
- Tool layer (`tools.py`) — verify, get case, dispute, freeze, escalate;
  `case_id` removed entirely; strict boolean validation
- **Idempotent freeze**: freezing an already-frozen card returns
  `already_frozen: true` with zero duplicate state change
- Mock banking data (`data/fraud_cases.py`) — 5 cases, 5 cards, fictional
- Webhook server (`server.py`) — live-tested end to end: create incident
  → verify → get case → freeze → repeat freeze (idempotent) →
  authorization-gate block → hijack attempt (blocked) → audit → reset
- **Webhook authentication** — real `before_request` gate, both modes
  live-tested with Flask's test client (7/7 tests) and manual curl
- Demo frontend (`frontend/index.html`) — calls the real backend, shows
  the fraud-signal-to-call timeline, no fake UI state
- 5 end-to-end demo transcripts (`simulate.py` → `demo_output/`)
- 36-test adversarial suite (`test_guardrails.py`) + 7-test webhook-auth
  integration suite (`test_server_auth.py`), all passing

**Configuration required (you provide):**
- ElevenLabs account, agent, voice, and webhook wiring (spec is ready
  in `elevenlabs_config/`, verified against current ElevenLabs docs,
  including the real `conversation_initiation_client_data.dynamic_variables`
  mechanism used to bind `incident_id` at outbound-call time — not
  invented)
- Public deployment (Render/Railway — config is ready, single-worker
  fixed, deploy is yours)
- `RESOLVEAI_WEBHOOK_SECRET` if running in production mode

**Not implemented, and not claimed to be:**
- Real core-banking or card-network integration
- Real customer data or real financial transactions
- A genuine second-reviewer approval endpoint for the high-value
  authorization gate (it blocks and escalates; nothing implements the
  human's side of that approval yet — Stage 2 item)
- Production-durable audit/session storage (in-memory Python
  structures — a real deployment needs Redis/a database, and needs it
  *before* running more than one worker, not after)
- Any live phone call — this is the backend + a demo UI that
  *simulates* the conversation with scripted "customer" lines

## 6. How authentication works (and why no PIN)

A PIN is the one thing a real bank never asks for over an unsolicited
call. This agent has **no tool capable of collecting, checking, or
storing a PIN, CVV, or password**, structurally
(`test_no_pin_cvv_password_collection_tools_exist`). Verification uses
a one-time code, compared server-side, resolved from an incident the
agent never chose. Full detail: `knowledge_base/authentication_policy.md`.

## 7. How card freeze works

`confirm_fraud_and_freeze` requires: verified session (bound to a
single-use incident, not an agent-supplied case), no dispute, a
supported fraud type, a strict-boolean explicit confirmation, and no
outstanding high-value authorization gate. Idempotent. Full detail:
`knowledge_base/card_freeze_policy.md`.

## 8. Run it locally

```bash
# Run the five demo scenarios — writes transcripts + audit log,
# including the fraud-signal → incident → call timeline
python3 simulate.py

# Run the 36-test adversarial guardrail suite
python3 -c "
import sys, test_guardrails as t
tests = [n for n in dir(t) if n.startswith('test_')]
ok = 0
for n in tests:
    getattr(t, n)(); ok += 1
print(f'{ok}/{len(tests)} passed')
"

# Run the 7-test webhook-auth integration suite
python3 -c "
import sys, test_server_auth as t
tests = [n for n in dir(t) if n.startswith('test_')]
ok = 0
for n in tests:
    getattr(t, n)(); ok += 1
print(f'{ok}/{len(tests)} passed')
"

# Run the server (serves both the API and the demo frontend)
python3 server.py
# then open http://localhost:8080 for the live demo page, or call the
# API directly — note the incident step is now required first:
curl -X POST localhost:8080/api/fraud/events \
  -H "Content-Type: application/json" -d '{"case_id":"CASE-2001"}'
# -> {"ok": true, "incident_id": "INC-..."}
curl -X POST localhost:8080/tools/verify_customer \
  -H "Content-Type: application/json" \
  -d '{"call_id":"c1","incident_id":"INC-...","spoken_verification_code":"4471"}'
```

## 9. Deploy it (this is your real Q link #1)

1. Push this repo to GitHub.
2. **Render:** connect the repo — `render.yaml` configures it
   automatically (Docker, single worker, free tier, health check at
   `/health`, `RESOLVEAI_DEMO_MODE=true` by default).
   **Railway/Heroku-style:** connect the repo — `Procfile` +
   `requirements.txt` configure it automatically.
3. You get a public URL serving both the API and the demo frontend at
   `/`. That's your first Q link.
4. Before any real use: set `RESOLVEAI_DEMO_MODE=false` and
   `RESOLVEAI_WEBHOOK_SECRET=<a real secret>`, and adapt the frontend
   to call through an authenticated route (not built yet — see Section
   5's roadmap items).

**Honesty check:** the Flask dev server and the full incident/auth flow
were tested live over real HTTP during development. `gunicorn` (used in
`Dockerfile`/`Procfile`) could not be installed or run in this sandbox
(no network access) — that exact production command is standard but
untested here.

## 10. Build the actual ElevenLabs agent

1. Paste `elevenlabs_config/system_prompt.md` as the agent's system
   prompt.
2. Configure the five webhook tools per
   `elevenlabs_config/tool_configuration.md` — `incident_id` is now a
   **Dynamic variable** (not LLM Prompt), sourced from
   `conversation_initiation_client_data.dynamic_variables` set when
   *you* trigger the outbound call — the agent never sees or types a
   case identifier at any point.
3. Build the six-node Agent Workflow per
   `elevenlabs_config/agent_workflow_spec.md`, including the new "Step
   0" describing the pre-call incident-creation sequence.
4. Upload `knowledge_base/*.md` to the agent's Knowledge Base.
5. Record a 60-second walkthrough of the L diagram alongside a real
   call — that's Q link #2.

## 11. Test results (actually run, not asserted)

```
36/36 adversarial guardrail tests passed
7/7 webhook-auth integration tests passed
5/5 demo scenarios completed without assertion failure
```

Coverage: every exposed tool, every mock case's full path, verification
bypass, incident hijack/replay (reproduced and blocked), strict-boolean
bypass (including the exact string-`"false"` case QA flagged),
no-PIN structural guarantee, dispute bypass, unsupported-fraud bypass,
high-value-authorization-gate bypass, idempotent freeze, audit-event
generation on success and denial, and both webhook-auth modes against
the real server.

**Still not covered, flagged honestly:** signature-based webhook
verification (currently a shared secret, not HMAC-signed payloads);
full session-expiry sweep beyond incident expiry; a real second-
reviewer approval flow for the authorization gate. Roadmap, not claimed
as done.

## 12. Demo scenarios

All five generate real transcripts in `demo_output/` by actually
running the guardrail code, now including the fraud-signal-to-call
timeline as part of the transcript:

1. **Successful intervention (English)** — CASE-2001, standard freeze
2. **Arabic customer** — CASE-2002, full flow in Arabic, same guardrails
3. **Failed verification** — CASE-2001, wrong code, blocked, escalated
4. **Customer disputes the flag** — CASE-2004, no freeze, escalated
5. **High-value authorization gate** — CASE-2003, blocked despite full
   customer confirmation, escalated for human review

Direct adversarial attempts (skip verification, hijack an incident,
send a malformed confirmation payload) live in `test_guardrails.py` and
`test_server_auth.py` instead of as scripted demos — stricter evidence,
since it asserts the block programmatically on every run.

## 13. Production hardening roadmap (explicitly out of scope here)

- HMAC-signed webhook payloads (currently a shared secret)
- A real second-reviewer approval endpoint, making the high-value gate
  an actual two-person control rather than block-and-escalate
- Durable, access-controlled audit and session storage (replacing the
  in-memory structures) — required before running more than one worker
- Real core-banking and card-network integration
- Authenticated proxy route so the demo frontend can run against a
  production-mode (`RESOLVEAI_DEMO_MODE=false`) deployment
- PII minimization review against actual regulatory requirements

## 14. File map

| File | What it proves |
|---|---|
| `fraud_events.py` | Server-side incident binding; hijack/replay protection; expiry |
| `guardrails.py` | All 7 guardrails as executable checks |
| `tools.py` | No case_id parameter anywhere; strict boolean validation; idempotent freeze |
| `data/fraud_cases.py` | 5 test cases incl. high-value gate; reset support |
| `server.py` | Incident endpoint, webhook auth (both modes), live-tested tool routes |
| `simulate.py` + `demo_output/*.json` | 5 real transcripts with fraud-to-call timeline |
| `test_guardrails.py` | 36 real adversarial tests |
| `test_server_auth.py` | 7 real webhook-auth integration tests against the live Flask app |
| `frontend/index.html` | Live webhook API + honest demo UI, incident flow wired, simulated-vs-real banner |
| `elevenlabs_config/*` | Verified-accurate ElevenLabs build spec, incident_id as Dynamic variable |
| `knowledge_base/*` | RAG source, restricts agent to approved wording, honest gate naming |
| `canvas_evidence/*` | Canvas draft + evidence-gathering guides for D and F |
