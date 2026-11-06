---
name: pacing
description: "Planned for v0.3, not implemented: Budget pacing with intervals: projected month-end spend and conversions vs plan."
disable-model-invocation: true
---

# pacing (scaffold, v0.3)

Status: NOT IMPLEMENTED in v0.1. If invoked, say so in one line and offer `diagnose` or the specific stats CLI (`run.py stats S01|S04|S09|S15|S16`) instead. Do not improvise this module.

What it will do: Budget pacing with intervals: projected month-end spend and conversions vs plan.

Stats it will call: S05 S11

TODO
- Reference file and input contract (CSV columns) in `references/`.
- Script under `scripts/` with JSON output and schema validation.
- Tests with synthetic fixtures.

Acceptance criteria: Backtest coverage of pacing intervals within tolerance on synthetic months.
