# Box D — Baseline Methodology (Banking / Fraud)

No numbers invented. This defines exactly how the baseline should be
obtained so whatever you get — from the F conversation, a published
source, or a pilot — plugs into D and M with matching definitions.

## Step 1 — Try for a real, sourced number first

1. **The F conversation itself.** A rough estimate from someone with
   direct exposure ("most flagged cases get a callback within the
   hour") is usable, cited honestly — not stated as a hard statistic.
2. **Published sources.** UAE Central Bank (CBUAE) consumer protection
   guidance, card network fraud-loss reporting, or a bank's own public
   disclosures sometimes reference average fraud-response times or
   loss-prevention rates.
3. **Industry benchmark data.** General card-fraud response-time
   benchmarks (not UAE-specific) can support a bounded estimate if
   clearly labeled as such, not presented as this institution's number.

If any of these produce a real number, use it — labelled with source —
and skip to Step 3.

## Step 2 — If no real number is obtainable in time: pilot design

> Baseline will be established via a 4-week measurement pilot on one
> card portfolio, tracking: (1) time from fraud signal to customer
> contact, (2) time from contact to card freeze (where applicable),
> (3) rate of cases requiring human escalation, (4) average agent
> handling time per flagged case, across a sample of at least 50
> flagged transactions.

**Population definition (must match M exactly):**
- Only transactions flagged by the fraud detection system as
  potentially unauthorized — not all customer contacts.
- One card product / one issuing entity, to keep the population
  comparable to the Stage 2 pilot population in L/O.
- First contact attempt per case (avoid double-counting retries).

**Metrics and their exact definitions (lock these — M must reuse them
verbatim):**

| Metric | Definition |
|---|---|
| Contact delay | Minutes from fraud signal to customer being reached |
| Freeze delay | Minutes from customer contact to card freeze (supported cases only) |
| Escalation rate | % of flagged cases requiring human handoff (dispute, unsupported, auth-gate, failed verification) |
| Agent handling time | Minutes of human agent time per flagged case, where applicable |

## Step 3 — Feed forward into Box M

Box M's three KPIs must be the *same metrics above*, phrased as targets:

1. Reduced contact delay (baseline: pilot/sourced figure → target:
   customer contacted within approximately one minute of signal, per
   the challenge's own framing)
2. Reduced freeze delay (baseline → target: freeze completed within the
   same call, for supported and non-gated cases)
3. Appropriate escalation rate (baseline → target: cases requiring
   human review correctly identified and routed, not a raw minimization
   target — a higher escalation rate on ambiguous cases is not a
   failure)

## What NOT to do

- Don't write "prevents X% of fraud losses" without a defined baseline
  and population behind it.
- Don't measure a broader population in M than D defined (e.g. don't
  baseline "all flagged transactions" but target only "supported,
  standard-value cases").
- Don't present the pilot design as completed data — label it as
  proposed if no real number exists yet.
