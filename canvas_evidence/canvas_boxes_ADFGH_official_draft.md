# ResolveAI — Canvas boxes A (partial), D, F, G, H — rebuilt against the
# REAL official template, with real interview quotes

Source of truth from here on: `ElevenLabs_Idea_Canvas.docx`, read directly —
not inferred. Word limits, table columns, and scoring weights below are copied
from that file. F/G/D/H below use only Sumeira Noman's verbatim quoted answers.

---

## F — Who you spoke to *(Structured · Problem fit · 25%)*
*"Real conversations with people inside the institution type you are building
for. We may contact them. Desk research alone scores in the bottom band."*

| Name and role | Organisation type | Date | The one thing they said that changed your idea |
|---|---|---|---|
| Sumeira Noman — Personal Banking Officer | Bank | 19-Sep-2026 | "I would make the customer-verification step much faster... preferably 24/7, and if the AI can't confidently handle the conversation, it should immediately connect the customer to a trained officer." |

This now clears the bar — real name, real role, real institution type, real
date, direct quote. Status: **[INTERVIEW] — verified.**

---

## G — What you got wrong *(50 words max · Problem fit · 25%)*
*"An assumption you held going in that turned out to be false... If nothing
changed, you have not spoken to enough people."*

> We assumed the main opportunity was automating fraud calls. The interview
> showed that faster customer verification is the key need, with immediate
> human escalation when AI cannot confidently handle the conversation.

**31/50 words.** Traces directly to the F quote above — same sentence, not a
different claim smuggled in.

---

## D — Today's baseline *(Numbers only · Problem fit · 25%)*
*"These exact numbers must reappear in box M — they will be cross-checked."*

| What you measured | Value today | Where the number comes from |
|---|---|---|
| Alert-to-initial-verification time (customer answers) | 5–15 minutes | Interview, Sumeira Noman, Personal Banking Officer, 19-Sep-2026 |
| Contact attempts before an unanswered case escalates | 2–4 attempts | Interview, Sumeira Noman, Personal Banking Officer, 19-Sep-2026 |
| Confirmed-fraud-to-initial-escalation time | 5–15 minutes (conditional — "assuming required information and systems are available") | Interview, Sumeira Noman, Personal Banking Officer, 19-Sep-2026 |

Deliberately **not** included: a "total resolution time." Her own words: *"It
should not be taken as the complete fraud-resolution time... the investigation
or dispute resolution is a separate process and can take considerably longer."*
Inventing a total here would contradict the source directly.

One methodology note worth being upfront about, not hiding: the Step 8
clarifying questions were somewhat leading (they proposed the alert-vs-escalation
split explicitly). Her answers confirmed that split in her own words rather than
just repeating the question back, which is why I'm comfortable calling this
[INTERVIEW]-status rather than founder-synthesized — but a sharp judge could
ask about it, so it's better you know that going in than get surprised by the
question later.

---

## H — The workflow today *(Diagram · Problem fit · 25%)*
Required lanes per the real template: Customer or applicant / Front-line staff
/ Back office or approver / Systems touched / Elapsed time.

| | Stage 1 | Stage 2 | Stage 3 | Stage 4 | Stage 5 | Stage 6 |
|---|---|---|---|---|---|---|
| **Customer or applicant** | — | — | Receives call | Confirms / denies / doesn't answer | (if denies) waits for escalation | (if fraud) card secured, contacted re: investigation |
| **Front-line staff** | — | Officer reviews transaction + recent activity | Officer calls registered mobile | Officer re-attempts if unanswered (2–4x) | Escalates to fraud/card-ops/dispute team | — |
| **Back office or approver** | — | — | — | — | Fraud / card operations / dispute team receives case | Card secured; investigation/dispute process begins |
| **Systems touched** | Fraud/transaction-monitoring system *(category — name withheld as confidential)* | + customer information/CRM | + contact-centre/dialer | — | + case-management (where used), card-management | Card-management; case-management |
| **Elapsed time** | — | — | 5–15 min total (Stages 2–3, if answered) | Longer if unanswered — attempts, not minutes, is the only quantified figure | 5–15 min (conditional on info/systems availability) | **Not established** — her words: "can take considerably longer," no figure given |

**Where the process fails most often:** customer reachability — her words:
*"Usually, customer reachability is the biggest one... After that, manual
review or escalation... can add time."*

**Where the customer has to chase:** not established, and I'd argue this
isn't a gap so much as a real finding — the entire process as described is
bank-initiated outbound contact. Nothing in the interview suggests the customer
proactively chases the bank at any point in this workflow. Worth writing that
directly into the box rather than leaving it blank: *"Not applicable — this is
a bank-initiated process; the customer does not chase, they are chased."*

**Total elapsed time, start to finish:** genuinely can't be filled in. We have
two partial figures (5–15 min twice, for two different stages) and an explicit
statement from Sumeira that the gap between them is unquantified and the final
stage (investigation/dispute) is open-ended. Writing a total would fabricate
a number she specifically declined to give.

### Two checkbox requirements this doesn't fully satisfy — your call needed
The template requires:
- ☐ **Each system by its actual name** — we only have categories
  (fraud/transaction-monitoring, card-management, CRM, contact-centre/dialer,
  case-management). Sumeira offered these explicitly *because* exact names are
  confidential. Options: (a) submit with categories and a one-line note that
  names are withheld per interviewee confidentiality, (b) ask her if she can
  name the *type* more specifically without naming her employer's actual
  vendor (e.g. "a cloud contact-centre platform" vs. just "contact-centre
  system") — still not a product name, but slightly more specific. I'd go
  with (a) and be upfront about it rather than push her for more than she's
  comfortable giving.
- ☐ **Total elapsed time, start to finish** — see above, genuinely not
  available from this interview. Same two options as D: state it as
  "not established beyond partial figures" or get one more follow-up.

---

## One correction to Box J, now that I've checked the real component menu
The official list is: Agents Platform, Agent Workflows, Sub-agents, Eleven v3
TTS, Voice Design, Scribe v2 STT, Knowledge base + RAG, Server/client tools,
MCP servers, Telephony (Twilio/SIP), Batch calling, Agent Testing, Post-call
webhooks, WhatsApp, Web/mobile SDKs, Bring-your-own LLM.

Two things in the earlier J draft don't match real names/real evidence:
1. I'd previously called your tool endpoints "scoped webhook tools" — checking
   `server.py`, your five `/tools/*` routes (`verify_customer`,
   `get_fraud_case`, `confirm_fraud_and_freeze`, `customer_disputes_fraud`,
   `escalate_to_human`) fire *during* the call, not after it. That's
   **Server / client tools**, not Post-call webhooks (which fire once a call
   ends — you don't have one of those).
2. **Telephony (Twilio/SIP)** should be ticked and wasn't. Your own config
   docs describe triggering an outbound call to the customer's real phone
   number — that requires a telephony component; it can't run on webhooks
   and voice alone.

Recommended tick list now: Agent Workflows, Eleven v3 TTS, Scribe v2 STT,
Server/client tools, Telephony (Twilio/SIP), Agent Testing. That's six, all with
direct code evidence. Knowledge base + RAG has some evidence too (the policy
wording constraint in the system prompt) — include it if you want a seventh,
but six well-justified beats padding.

---

## Still open — needs you, not guesswork
- **Team name** — still unresolved anywhere in the files.
- **A — Track / Use case (1–8) / Stage / contact email / based in / team
  size / prior ElevenLabs use / website-or-repo** — all structured fields I
  can't fill without you. Use case is numbered 1–8 in the real template but
  the list of what those 8 options *are* isn't in this docx — that likely
  lives on the Ignyte portal itself. If you can get me that list, I'll match
  "proactive multilingual fraud intervention" to the right number rather than
  guessing.
- **Q** — note the real requirement is narrower than what I assumed earlier:
  the 60-second recording must specifically walk through the **Box L diagram**,
  not a general product demo. Worth re-scripting the walkthrough once L is
  finalized.
