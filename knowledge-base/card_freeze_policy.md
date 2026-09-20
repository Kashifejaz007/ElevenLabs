# Card Freeze Policy — ResolveAI (Sandbox)

## When a freeze is permitted

All of the following must be true, checked by the backend, not asserted
by the agent:

1. The call is verified against this specific case.
2. The customer has not disputed the fraud flag.
3. The fraud type has an approved automated policy (`supported: true`).
4. The customer has explicitly confirmed, in the current turn, that the
   transaction was not theirs.
5. The transaction does not trigger the high-value human
   authorization gate — or if it does, a second authorized reviewer
   has separately approved it via a real approval mechanism (NOT
   modeled in this sandbox; the sandbox always escalates these to a
   human queue instead, since no approve_freeze() endpoint exists yet
   — see README roadmap).

## High-value human authorization gate

Transactions above the bank's set threshold cannot be frozen on the
agent's action alone, however confident the customer's confirmation.
**Naming note:** this is a one-sided gate — the agent is blocked, full
stop — not a completed two-person "four-eyes" workflow, since no
second-reviewer approval endpoint exists in this sandbox yet. The
agent's job here is to explain clearly that a human reviewer is
required and escalate — not to imply the freeze has happened, and not
to keep trying alternate phrasing to get the tool to succeed.

## Idempotency

Freezing an already-frozen card must never be treated as an error or
retried destructively — it returns `already_frozen: true` with no
further state change. This matters because a real call can glitch, drop,
or be retried by the platform; freezing must behave identically whether
it's the first attempt or the fifth.

## What freeze does NOT do

Freezing a card is not a financial decision — it does not approve or
deny a chargeback, dispute, or claim, and does not move, refund, or
transfer any money. No such tool exists in this system.
