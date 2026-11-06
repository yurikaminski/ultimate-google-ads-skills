# Experiments and incrementality

Load when: an exploit or elevate action needs proof, the user asks for an A/B test,
brand reduction is proposed, or a window closes.

## Pre-registration (required before launch)

Write a decision-log entry (status proposed) with:
- hypothesis and the constraint link it targets,
- primary metric on the final stage and guardrail metric (e.g. total brand conversions in the CRM),
- MDE, power and duration from S02 (planned v0.3; until then, mark duration "estimated"),
- analysis method (S03 for A/B, S07 or S08 for geo/causal),
- stop rule and rollback.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/run.py" ledger append --workspace W --account A --log decision
```

## Methods

| Question | Design | Stats |
|---|---|---|
| Does ad/page A beat B | campaign experiment or ad variation split | S02 size, S03 readout with multiple-comparison correction |
| Is brand spend incremental | geo holdout or pause with synthetic control | S08 design, S07 readout, guardrail on total brand conversions |
| Did my change move the metric | before/after with control | S06 change point plus S07 |
| Is PMax/AI Max incremental | experiment vs control campaign | S03 on final-stage conversions |

## Rules

- Warn-first: if the planned test cannot reach the MDE in a reasonable window, say so on the first line. The user may still run it; the readout is then indicative.
- One change per link per window. Overlapping changes on the same link make the readout unknown.
- Close the loop: at window end, record realized delta vs expected delta (memory-protocol.md calibration).
- No peeking-based stops unless the method supports sequential analysis.
