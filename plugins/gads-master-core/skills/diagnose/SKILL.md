---
name: diagnose
description: Theory of Constraints diagnosis for a Google Ads account. Default for "optimize my account", "what is holding us back", "where is the bottleneck". Finds one constraint with evidence and returns a Constraint Brief with max 3 actions. Requires onboarding context; runs onboard first if missing.
---

# Diagnose (TOC)

CLI = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/run.py"`. Detail: `${CLAUDE_PLUGIN_ROOT}/references/toc-engine.md`.

## Preconditions
1. `CLI context stale --workspace W --account A`: if missing or review due, run skill `onboard` first.
2. `CLI profile get`: needs `targets.throughput` (T*) and ideally `targets.rates.<stage>` and `lag_days`. Missing T* = no verdict: ask Q02 and stop.
3. Playbook = from `business_model` (saas_* -> `saas`, ecommerce -> `ecommerce`). Other models: chain is a scaffold in v0.1, say so.

## Inputs (ask for exactly these, CSV)
- Funnel, one row per week: `period` (week start) + one column per stage of `references/business-model-playbooks/<playbook>.chain.yaml`, optional `cohort_age_days`. Stages after the click usually come from GA4/CRM: ask the user to export them.
- Optional account export (daily: `date, campaign, impressions, clicks, cost, conversions`) for Gate 0 (S15).
- Optional conversion lag rows (`lag_days`) for S04 maturity.
- Optional operational signals JSON, one entry per stage: `{"<stage>": {"supports_constraint": true, "signal": "<what was observed, with source>"}}`, plus `lost_is_budget` / `lost_is_rank` for volume. Build it only from evidence you can cite (export columns, user statements marked reported).

## Run
`CLI diagnose --workspace W --account A --funnel f.csv --playbook <p> [--export e.csv] [--lag-file l.csv] [--signals s.json]`
Show `markdown` from the output verbatim in structure. Its first line is the warn-first line when validity is not valid: keep it first.
Instruments: run only those listed in `brief.instruments` for the constraint, or what the user asks. Bounded audits: subagents `audit-measurement` (Gate 0, OCI), `audit-search`, `audit-structure`, `audit-automation`, each returning `finding.v1` JSON.

## After the user reviews
- Accepted: re-run with `--commit` (writes constraint-history, parking lot, baselines on constraint move, run bundle). Then log each accepted action: `CLI ledger append --log decision --record '{"hypothesis": ..., "constraint_link": ..., "entity": ..., "direction": ..., "stats_ids": [...], "window": {"start": ..., "end": ...}, "status": "proposed"}'`.
- Changes are drafts. Applying them needs plugin `gads-master-api` (v0.3) and its mutation gate; until then the user applies them by hand and you set status `applied` then `measuring`.
- At window end (`CLI ledger due`), close the loop: compare expected vs realized with the same stats, set `closed` or `reverted`.

## Rules
One constraint. Max 3 exploit actions on it. Everything else is parking lot, one line each, no recommendations. Never contradict a frozen window. The owner's hypothesis is tested, never evidence.
