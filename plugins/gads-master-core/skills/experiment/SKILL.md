---
name: experiment
description: "Planned for v0.3, not implemented: Experiment design and readout: hypothesis, power and MDE, duration, pre-registration, readout."
disable-model-invocation: true
---

# experiment (scaffold, v0.3)

Status: NOT IMPLEMENTED in v0.1. If invoked, say so in one line and offer `diagnose` or the specific stats CLI (`run.py stats S01|S04|S09|S15|S16`) instead. Do not improvise this module.

What it will do: Experiment design and readout: hypothesis, power and MDE, duration, pre-registration, readout.

Stats it will call: S02 S03 S07 S08

TODO
- Reference file and input contract (CSV columns) in `references/`.
- Script under `scripts/` with JSON output and schema validation.
- Tests with synthetic fixtures.

Acceptance criteria: Designs include MDE and duration from S02; readouts cite S03/S07 ids.
