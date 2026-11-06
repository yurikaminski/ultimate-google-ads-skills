# Playbook: Local (scaffold, planned v0.3)

Applies to business_model: local.
Chain file: `local.chain.yaml` (to be written in v0.3).

## Status

Scaffold only. diagnose with this playbook returns `unknown` and asks to run with the closest
v0.1 playbook (saas or ecommerce) as an explicitly labeled approximation.

## Planned chain

impressions > clicks_or_calls > leads_or_visits > booked > completed

## TODO

- Define every link, its rate and the data source for each stage.
- Target-rate sources: owner input, self-benchmark, labeled heuristics (add to heuristics-registry.json).
- Operational corroboration signal per link. Model-specific: calls and direction requests as conversions, service area geo, Business Profile signals, capacity per location.
- Exploit / subordinate / elevate moves per constraint link.
- Follow-up onboarding questions.

## Acceptance criteria (v0.3)

- `local.chain.yaml` validates and S16 runs on it.
- One planted-constraint fixture per link; constraint_finder finds the planted link and names the right runner-up.
- Missing stages produce `unknown`, never a guessed value.
