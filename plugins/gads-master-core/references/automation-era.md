# Automation-era governance (PMax, AI Max, Demand Gen)

Load when: the account runs Performance Max, AI Max for Search, or Demand Gen, or
the audit asks about automation.

Automated campaign types trade control for reach. Governance means you still decide
inputs, guardrails and measurement, and you read what the system did.

## Inputs you control

| Input | Why it matters |
|---|---|
| Conversion goal and values | the system optimizes exactly this; Gate 0 first |
| Brand exclusions | stops automation from buying cheap brand conversions |
| Audience signals | starting hints, not targeting limits |
| Asset groups by theme | one theme per asset group, like ad groups |
| Final URL expansion | on = system may send traffic to any page; check which pages got it |
| Feed quality (ecommerce) | titles, GTINs, prices, disapprovals drive Shopping inventory |

## Guardrails

- New automated campaigns are created PAUSED and launched through the mutation gate (api plugin).
- Each launch is an experiment with a window and a pre-registered success metric on the final stage (experiments-incrementality.md).
- Watch cannibalization: compare total final-stage conversions, not campaign-reported conversions.
- AI Max for Search: treat broad matching and asset rewriting as a test against the Search control; review the search terms it added.

## What to read after launch

- Search-term insights and placement reports (where available).
- Channel and asset-group breakdowns (availability changes: claims-ledger, mark unverified until checked).
- Brand share of conversions inside PMax.

## Dated facts

Feature names, reporting availability and controls for these campaign types change often.
Every such fact used in a finding must have a claims-ledger entry or be marked "unverified".
