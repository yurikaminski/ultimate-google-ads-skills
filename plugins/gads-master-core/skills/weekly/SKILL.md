---
name: weekly
description: "Planned for v0.3, not implemented: Weekly ritual: scorecard vs own baselines, search-term review (S09), open windows due to close, parking-lot resurfacing."
disable-model-invocation: true
---

# weekly (scaffold, v0.3)

Status: NOT IMPLEMENTED in v0.1. If invoked, say so in one line and offer `diagnose` or the specific stats CLI (`run.py stats S01|S04|S09|S15|S16`) instead. Do not improvise this module.

What it will do: Weekly ritual: scorecard vs own baselines, search-term review (S09), open windows due to close, parking-lot resurfacing.

Stats it will call: S01 S05 S09

TODO
- Reference file and input contract (CSV columns) in `references/`.
- Script under `scripts/` with JSON output and schema validation.
- Tests with synthetic fixtures.

Acceptance criteria: Scorecard compares to baselines.json with CIs; windows due are listed with close-the-loop results.
