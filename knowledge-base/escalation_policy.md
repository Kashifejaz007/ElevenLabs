# Escalation Policy — ResolveAI (Sandbox)

Every condition under which the agent must stop and hand off to a human
reviewer. These triggers are also enforced in code (`guardrails.py`),
so this document and the code must stay in sync.

## Mandatory escalation triggers

| Trigger | Code path | Agent's spoken handoff |
|---|---|---|
| Customer disputes the fraud flag (transaction is theirs) | `customer_disputes_fraud()` | "Thank you for confirming — I won't take any action on your card." |
| Verification fails | `verify_customer()` returns `ok: false` | "That doesn't match what we have on file — I'll arrange a callback so you can be verified a different way." |
| Transaction hits the high-value authorization gate | `confirm_fraud_and_freeze()` returns `G7_DUAL_AUTH_REQUIRED` | "This needs an authorized reviewer before I can freeze it — escalating now." |
| Fraud type has no approved policy | `confirm_fraud_and_freeze()` returns `G5_UNSUPPORTED` | "This needs specialist review — connecting you with a colleague." |
| Customer asks the agent to approve/deny a claim, dispute, or transfer money | No such tool exists | "That's a decision for our claims/disputes team, not something I can do on this call — I'll flag it for them." |
| Customer offers a PIN, CVV, or password unprompted | Agent policy (not a tool call) | Politely decline, remind the customer the bank never needs this. |

## What escalation does NOT mean

Escalation is a normal, expected outcome — not a failure to hide. Every
escalation logs a `reason_code` in `guardrails.AUDIT_LOG` and counts as
the guardrail working correctly, not the agent falling short.

## What the agent must never do instead of escalating

- Never improvise a freeze for an unsupported fraud type.
- Never argue with a customer who disputes the flag.
- Never imply a freeze has happened when the authorization gate actually
  blocked it.
- Never keep retrying a blocked tool call with slightly different
  arguments to see if it goes through.
