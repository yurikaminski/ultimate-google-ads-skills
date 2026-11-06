---
name: attribution
description: "Planned for v0.3, not implemented: Attribution and conversion definition review: windows, models, platform vs GA4 vs CRM."
disable-model-invocation: true
---

# attribution (scaffold, v0.3)

Status: NOT IMPLEMENTED in v0.1. If invoked, say so in one line and offer `diagnose` or the specific stats CLI (`run.py stats S01|S04|S09|S15|S16`) instead. Do not improvise this module.

What it will do: Attribution and conversion definition review: windows, models, platform vs GA4 vs CRM.

Stats it will call: S03 S12 S14

TODO
- Reference file and input contract (CSV columns) in `references/`.
- Script under `scripts/` with JSON output and schema validation.
- Tests with synthetic fixtures.

Acceptance criteria: Reconciliation ratio with CI (S14); rate x mix decomposition (S12) for CPA moves.
