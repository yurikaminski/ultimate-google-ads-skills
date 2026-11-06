# Measurement and signal

Load when: Gate 0 runs (every diagnose), the constraint is lead quality, or the
user asks about tracking, OCI, conversion lag or consent.

Bad measurement makes every downstream finding wrong. This is why it is Gate 0.

## Gate 0 checks

| Check | Evidence type | Pass | Fail | Unknown |
|---|---|---|---|---|
| Primary conversion defined | observed (account data) or reported | one primary action per goal, matching the business conversion | form view, page view or micro-event as primary for bidding | no conversion list |
| No double counting | observed | count setting fits the action (one per click for leads) | duplicate tags or GA4 import plus native tag on the same event | cannot see tags |
| Platform vs CRM reconciliation (S14, planned v0.3) | observed | ratio within volume-based tolerance | ratio outside tolerance with CI | no CRM export |
| Data quality of input (S15) | observed | plausibility, duplicates, drift pass | any S15 check fails | no data |
| Conversion lag known (S04) | observed | lag distribution estimated, maturity cutoff set | n/a | too few conversions: use reported lag, confidence low |

## Signal quality ladder (SaaS and lead gen)

1. Form fill or signup only (weakest: optimizes for volume, invites junk).
2. Qualified event imported: MQL, activated or PQL.
3. Offline conversion import (OCI) of SQL and won with value.
4. Value-based bidding on pipeline or revenue.

Recommend climbing one step at a time. Moving the bid target to a deeper event
needs enough volume of that event (heuristic H-007); otherwise import it as a
secondary conversion first and observe.

## Enhanced conversions and consent

- Enhanced conversions improve match rates; check status, do not assume.
- Consent: if the site shows a consent banner (onboarding observed signal), ask whether consent mode is implemented. Modeled conversions change the meaning of the counts; record it in business-context `tracking_maturity`.

## Conversion lag

- Run S04 on click-to-conversion lag. The maturity cutoff (P90 lag of THIS account) decides which cohorts diagnose can use.
- Recent weeks always look worse before they mature. Never call a drop inside the immature window.

## Rules

- Tag observations from page source (GTM, GA4, pixels) as hints, evidence type observed but confidence low: presence of a tag is not proof of a working conversion.
- Never ask for or store credentials to verify tracking.
