---
name: audit
description: "Planned for v0.3, not implemented: Full evidence-first account audit (Gate 0, search, structure, automation) fanned out to the audit-* subagents, merged into finding.v1 with no invented score."
disable-model-invocation: true
---

# audit (scaffold, v0.3)

Status: NOT IMPLEMENTED in v0.1. If invoked, say so in one line and offer `diagnose` or the specific stats CLI (`run.py stats S01|S04|S09|S15|S16`) instead. Do not improvise this module.

What it will do: Full evidence-first account audit (Gate 0, search, structure, automation) fanned out to the audit-* subagents, merged into finding.v1 with no invented score.

Stats it will call: S01 S09 S14 S15

TODO
- Reference file and input contract (CSV columns) in `references/`.
- Script under `scripts/` with JSON output and schema validation.
- Tests with synthetic fixtures.

Acceptance criteria: Every control in controls-registry.json evaluated or reported unknown; findings validate; no health score anywhere.
