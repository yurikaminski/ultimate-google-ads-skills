---
name: monitor
description: "Planned for v0.3, not implemented: Anomaly and change-point monitoring cross-checked with the decision log (common vs special cause)."
disable-model-invocation: true
---

# monitor (scaffold, v0.3)

Status: NOT IMPLEMENTED in v0.1. If invoked, say so in one line and offer `diagnose` or the specific stats CLI (`run.py stats S01|S04|S09|S15|S16`) instead. Do not improvise this module.

What it will do: Anomaly and change-point monitoring cross-checked with the decision log (common vs special cause).

Stats it will call: S05 S06

TODO
- Reference file and input contract (CSV columns) in `references/`.
- Script under `scripts/` with JSON output and schema validation.
- Tests with synthetic fixtures.

Acceptance criteria: Planted anomalies detected with controlled false-alarm rate; each alert linked to a decision id or flagged unexplained.
