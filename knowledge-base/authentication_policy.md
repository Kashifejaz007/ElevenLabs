# Authentication Policy — ResolveAI (Sandbox)

## What verification is

A one-time code sent to the customer's registered channel (SMS/app push
in a real deployment) for this specific contact attempt. It is unrelated
to the customer's card PIN, online banking password, or any long-lived
credential.

## What the agent may ask for

Only: "Could you read back the verification code you just received?"

## What the agent must NEVER ask for, under any framing

- Card PIN
- CVV / security code printed on the card
- Full card number
- Online/mobile banking password
- Any static, reusable credential

If a customer offers any of these unprompted (e.g. "my PIN is 1234"),
the agent does not repeat it, store it, act on it, or ask for
confirmation of it — it politely declines and reminds the customer the
bank never needs this information over a call.

## Who decides whether verification passed

The backend, exclusively. `verify_customer` performs a server-side
string comparison between what the customer said and the code on file.
The agent has no way to assert success on its own judgment — see
`tools.py:verify_customer` and the hardening note in the main README.
No tool exists that reveals the correct code back to the agent.

## What happens on failure

`get_fraud_case`, `customer_disputes_fraud`, and
`confirm_fraud_and_freeze` are all blocked (`G3_UNVERIFIED`) until
verification succeeds. Two consecutive failures should be treated as a
signal to escalate rather than keep retrying — see Escalation Policy.
