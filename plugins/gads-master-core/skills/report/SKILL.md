---
name: report
description: "Planned for v0.3, not implemented: Client-ready report rendered from run bundles: what changed and why (rate x mix), reconciliation."
disable-model-invocation: true
---

# report (scaffold, v0.3)

Status: NOT IMPLEMENTED in v0.1. If invoked, say so in one line and offer `diagnose` or the specific stats CLI (`run.py stats S01|S04|S09|S15|S16`) instead. Do not improvise this module.

What it will do: Client-ready report rendered from run bundles: what changed and why (rate x mix), reconciliation.

Stats it will call: S12 S14

TODO
- Reference file and input contract (CSV columns) in `references/`.
- Script under `scripts/` with JSON output and schema validation.
- Tests with synthetic fixtures.

Acceptance criteria: Every number in the report traces to a run bundle stats id.
