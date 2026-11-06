---
name: forecast
description: "Planned for v0.3, not implemented: Conversion forecast with intervals, lag-aware (nowcast immature days)."
disable-model-invocation: true
---

# forecast (scaffold, v0.3)

Status: NOT IMPLEMENTED in v0.1. If invoked, say so in one line and offer `diagnose` or the specific stats CLI (`run.py stats S01|S04|S09|S15|S16`) instead. Do not improvise this module.

What it will do: Conversion forecast with intervals, lag-aware (nowcast immature days).

Stats it will call: S04 S11

TODO
- Reference file and input contract (CSV columns) in `references/`.
- Script under `scripts/` with JSON output and schema validation.
- Tests with synthetic fixtures.

Acceptance criteria: Rolling-origin backtests reported; intervals calibrated on simulations.
