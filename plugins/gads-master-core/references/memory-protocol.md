# Memory protocol

Load when: any mode starts (read), or a write event happens.

State lives outside the plugins, per account, so plugin updates never overwrite it:

```
<workspace>/.gads-master/<account_id>/
  business-context.md     read at the start of EVERY mode
  profile.yaml            numbers: unit economics, T*, targets, lag, guardrails, risk params
  decision-log.jsonl      append-only
  constraint-history.jsonl
  parking-lot.jsonl
  baselines.json
  capabilities.json       written by doctor
  intel/                  intel plugin data
  stats-cache/            stats-result files by input hash
```

## Read

Every mode loads, in order:

1. business-context (`run.py context get`)
2. profile (`run.py profile get`)
3. open measurement windows (`run.py ledger open-windows --log decision`)
4. last N decisions (`run.py ledger list --log decision`)

diagnose also loads constraint-history, baselines and parking lot.

## Write

Only on events, only through the tools, structured fields only. The LLM never hand-edits state files.

| Event | Tool |
|---|---|
| onboarding confirmed | `run.py context merge-draft`, `run.py profile set` |
| end of diagnose | `run.py diagnose ... --commit` (constraint-history, parking-lot) |
| draft proposed / approved / applied | `run.py ledger append --log decision` |
| window closed | `run.py ledger append --log decision` (status closed, realized delta) |

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/run.py" ledger <append|list|status|open-windows|freeze-check|flipflops> --workspace W --account A --log <decision|constraint|parking>
```

## decision-log fields

`id, ts, constraint_link, hypothesis, change_id or draft_id, evidence_refs, stats_ids,
window {start, end}, expected_delta, status (proposed | approved | applied | measuring | closed | reverted), realized_delta`

## Uses

- Skip re-intake when context is fresh (`run.py context stale` checks TTLs).
- Freeze: `freeze-check` blocks a new change on a link with an open window; the response says "frozen until <date>".
- Flip-flops: `flipflops` detects A then not-A on the same object inside a short span; report it before proposing.
- Close the loop at window end (S06/S07, planned v0.3; until then, before/after with CI and label indicative).
- Anti-inertia: when the constraint moves, refresh baselines and resurface parking-lot items.
- Calibration: compare expected vs realized delta to adjust confidence labels over time.
- Reconcile with the account change history (limited retention, see gaql-notes.md) to catch edits made outside the skill.

## Hygiene

- Namespace per account. Never mix accounts in one file.
- Never store credentials, tokens or raw external text (page copy, ad text from competitors, search-term dumps). Store structured fields and cited URLs.
- Everything is local and deletable: removing the account folder removes all memory.
