# Box F — Interview Guide (Banking / Fraud)

One real conversation with someone who has direct exposure to
card-fraud response at a bank, insurer, or payments/fraud-ops team.
Designed to do double duty: it gets you the F conversation AND raw
material for D's baseline, in one 15-minute call.

## Who counts as a valid F conversation

Ranked by directness of relevance:
1. Someone on a bank/card issuer's fraud operations or contact-centre
   team (sees compromise-response volume directly)
2. A fraud analyst, risk officer, or someone in card operations
3. Someone in customer experience/digital banking who handles fraud
   escalations
4. Failing the above: someone who has personally been called about
   suspected fraud on their own card recently (weaker, use only if
   1–3 aren't reachable in time)

## Questions to ask (15 minutes)

**Framing**
"I'm looking at what happens right after a bank's system flags a
possible card compromise — before any human gets involved. I want to
understand the real process, not the official version."

**Process questions**
1. "When a transaction gets flagged as suspicious, what actually
   happens first — is it automatic, or does someone review it?"
2. "How is the customer usually contacted, and how fast, typically?"
3. "What's the actual conversation like — what does the agent need to
   verify, and how?"
4. "Roughly how often does a flagged transaction turn out to be
   genuine fraud versus the customer's own legitimate purchase?"
5. "What happens if the customer can't be reached quickly — does the
   transaction still get blocked, or does it depend?"

**Baseline-oriented questions (this is your D material)**
6. "Roughly how long does it take from the system flagging something to
   a customer actually being reached — minutes, longer?"
7. "Is that tracked anywhere, even roughly — average contact time,
   resolution time?"
8. "What's the mix of languages your customer base needs support in day
   to day? Is that ever a bottleneck?"

**Closing (also feeds K/N)**
9. "If an AI called customers automatically after a suspected
   compromise, what's the one thing you would absolutely not want it
   authorized to do on its own?"

## What to do with the answers

- Any number, even a rough one ("most flagged transactions get a call
  within the hour, but it varies") → `D_baseline_methodology.md`, cited
  honestly: "per conversation with [role], Sept 2026."
- Process/friction answers → check against Box C and the H diagram;
  correct either if reality differs from what's drafted.
- Q9's answer → Box N (risks) and Box K (guardrails) as a real, sourced
  concern — this is exactly why the high-value authorization gate exists
  in the sandbox; a real answer might sharpen or add to it.

## Honesty rule

If the conversation contradicts anything already drafted (H, C, an
assumed guardrail), the conversation wins. Update the draft rather than
keeping the more polished-sounding but unverified version.
