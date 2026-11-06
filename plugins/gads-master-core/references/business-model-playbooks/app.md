# Playbook: App (scaffold, planned v0.3)

Applies to business_model: app.
Chain file: `app.chain.yaml` (to be written in v0.3).

## Status

Scaffold only. diagnose with this playbook returns `unknown` and asks to run with the closest
v0.1 playbook (saas or ecommerce) as an explicitly labeled approximation.

## Planned chain

impressions > clicks > install > activation > subscription > retention

## TODO

- Define every link, its rate and the data source for each stage.
- Target-rate sources: owner input, self-benchmark, labeled heuristics (add to heuristics-registry.json).
- Operational corroboration signal per link. Model-specific: MMP source of truth, SKAN/privacy limits, retention cohorts (D1/D7/D30), store listing conversion.
- Exploit / subordinate / elevate moves per constraint link.
- Follow-up onboarding questions.

## Acceptance criteria (v0.3)

- `app.chain.yaml` validates and S16 runs on it.
- One planted-constraint fixture per link; constraint_finder finds the planted link and names the right runner-up.
- Missing stages produce `unknown`, never a guessed value.
