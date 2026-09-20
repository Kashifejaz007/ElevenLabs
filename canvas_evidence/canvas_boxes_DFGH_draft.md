# ResolveAI — Boxes D, F, G, H (interim draft)

**Status: [INTERVIEW-REPORTED, per founder summary] — not [INTERVIEW] or [VERIFIED].**
Everything below traces only to your message in this chat, not to a transcript,
recording, or notes file I've seen directly. This is usable as a working draft
and gets D/M consistency locked in early, but it does not yet meet the
evidentiary bar your own Phase 3/4 rules set for F (no confirmed role, institution
type, or date). Upgrade path is the gap checklist at the bottom.

---

## D — Baseline (numbers only)

**Metric 1 — Alert-to-verification time**
5–15 minutes
Definition: time from fraud alert generation to completed initial customer
verification. Does **not** include escalation, freeze execution, or full
resolution.
Source: interview, as summarized by founder.

**Metric 2 — Confirmed-fraud-to-escalation time**
5–15 minutes
Definition: time from confirmed unauthorized activity to escalation being
initiated. Conditional — reported as normal "assuming information and systems
are available"; no figure given for cases where they aren't.
Source: interview, as summarized by founder.

**Total time-to-freeze/block: NOT ESTABLISHED.**
Do not sum Metric 1 + Metric 2 to produce a total — they were not reported as
sequential non-overlapping durations, downstream freeze-execution time isn't
covered at all, and Metric 2 is explicitly conditional. Any "total resolution
time" claim would be invented, not sourced.

---

## F — Interview record (interim)

| Field | Value |
|---|---|
| Interviewee | Sumeira Noman |
| Role / title | **NOT PROVIDED** |
| Institution type | **NOT PROVIDED** |
| Date | **NOT PROVIDED** |
| Workflow discussed | Fraud-alert review, customer verification, escalation timing |
| Direct quotes | **NONE PROVIDED** |
| Key findings used in D/G/H | (1) 5–15 min covers alert review + initial verification, not total resolution. (2) Escalation after confirmed fraud can normally happen in 5–15 min, conditional on info/systems availability. (3) Systems involved fall into five categories: fraud/transaction monitoring, card-management, customer information/CRM, contact-centre/dialer, case-management (where used). |

This table is intentionally incomplete. It's here so G and H have something to
point back to, not because it satisfies the "real F interview" requirement as
originally specified.

---

## G — What we got wrong (50/50 words)

> We assumed one blended response-time number covering the whole fraud response.
> The interview shows two distinct stages instead: alert review plus initial
> customer verification, and separately, escalation after confirmed unauthorized
> activity — each independently reported at 5-15 minutes, so total time-to-freeze
> is not established and may exceed either figure alone.

---

## H — Current-state diagram (six stages, categories only, no vendor names,
no invented customer-chasing behavior, no invented total elapsed time)

| # | Stage | Lane(s) | System category | Timing |
|---|---|---|---|---|
| 1 | Alert generated | System | Fraud/transaction monitoring | Not reported |
| 2 | Alert reviewed | Back-office | Fraud/transaction monitoring; case-management (where used) | Included in 5–15 min (Metric 1, with stage 3) |
| 3 | Initial customer verification | Front-line + Customer | Contact-centre/dialer; customer information/CRM | Included in 5–15 min (Metric 1, with stage 2) |
| 4 | Unauthorized activity confirmed | Back-office | Case-management (where used); CRM | Not reported |
| 5 | Escalation initiated | Back-office | Case-management; card-management | 5–15 min (Metric 2) *if* info/systems available — no figure for the "not available" case |
| 6 | Freeze / block executed | Back-office / System | Card-management | **Not reported — not in scope of either baseline figure** |

Explicitly omitted because not evidenced:
- Any specific vendor/product name for any system category
- Any customer-chasing / follow-up-contact behavior (customer calling back,
  repeated attempts, abandonment) — none was reported, so none is shown
- A total elapsed time across all six stages
- What happens differently when "information and systems are **not** available"
  for escalation (Metric 2's stated condition implies a slower or blocked path
  exists, but no detail was given)

---

## Remaining evidence gaps — checklist

- [ ] Sumeira Noman's role/title
- [ ] Institution type (bank / issuer / payments processor / other)
- [ ] Interview date
- [ ] Any direct quote usable for F, if permission allows
- [ ] Whether Metric 1 and Metric 2 are sequential (verification finishes, *then*
      escalation starts) or can overlap — affects whether M can ever show a
      combined figure
- [ ] What happens when info/systems are *not* available for escalation (the
      condition attached to Metric 2) — is there a slower fallback, or does it
      stall?
- [ ] Stage 6 (freeze/block execution) timing — currently a total blind spot
- [ ] Confirmation that "case-management" is actually used at this institution,
      or whether it should be dropped from H as a category
- [ ] Official box word limits for D/F/G/H specifically (still unverified — no
      docx, no accessible Ignyte template)

Until the first four are filled, F stays below the bar your Phase 3 rules set,
even though D/G/H can now be drafted around what you've given me. I'd treat this
whole file as a placeholder that's honest about being a placeholder, not as
submission-ready text.
