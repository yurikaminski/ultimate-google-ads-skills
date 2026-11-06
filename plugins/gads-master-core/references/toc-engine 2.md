# TOC engine

Load when: mode `diagnose` runs, or a user asks "what is holding this account back".
Backbone rule: one constraint at a time, max 3 actions on it, everything else goes to the parking lot.

## 1. The chain

The chain is parametric. Each business-model playbook defines its links in
`references/business-model-playbooks/<name>.chain.yaml`. Generic shape:

```
Gate 0 (measurement integrity, policy risk)
visibility > demand > budget > rank > click > on-site conversion > lead quality > sales capacity > economics
```

v0.1 chains:

| Playbook | Stages (counts per period) |
|---|---|
| saas | impressions > clicks > signups_or_leads > activated_or_mql > sql > won |
| ecommerce | impressions > clicks > sessions > add_to_cart > checkout > purchase |

A **link** is the conversion between two adjacent stages (rate = downstream / upstream).
The first stage (impressions) is a **volume** link: its starvation means demand, budget or rank.

## 2. Gate 0 (always first)

Gate 0 findings block the diagnosis regardless of the constraint:

- Measurement integrity: primary conversion missing, duplicated, or not matching the CRM within tolerance (S14 when available, S15 always).
- Data quality: S15 `insufficient` or failing plausibility checks on the funnel input.
- Policy risk: disapproved ads or suspended assets on core campaigns (reported by user or account data).

If Gate 0 fails, the Constraint Brief names Gate 0 as the constraint and the
only actions are fixes to measurement or policy. Nothing downstream is analyzed.

## 3. Queue / starvation test (S16)

Implemented in `adsstats` S16 and wrapped by:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/run.py" diagnose --workspace W --account A --funnel funnel.csv --playbook <saas|ecommerce> [--signals ops.json] [--commit]
```

Steps:

1. **Target throughput T\***: from `profile.yaml` (owner-defined, e.g. SQLs or purchases per period). Missing T\* means the test cannot run: return `unknown` with the question to ask.
2. **Target rate per link r\***, first available source wins:
   1. owner-defined in profile (`targets.rates.<link>`),
   2. account self-benchmark: P75 of the link's weekly history over mature weeks (stable segment only),
   3. external benchmark from `heuristics-registry.json`, labeled sanity check only, confidence capped at low.
3. **Required volume** at stage k: `V*_k = T* / product(r*_j for every link j downstream of k)`.
4. **Classify** each stage with a confidence interval (Poisson for counts, Wilson for rates, from S01):
   - `starvation`: upper CI < V\*
   - `ok` (queue): lower CI > V\*
   - `inconclusive`: CI crosses V\*
   - `unknown`: sample insufficient or cohort immature (S04)
5. **Constraint** = first stage, going downstream, in starvation whose predecessor is ok. The link between them converts below target. If starvation starts at the first stage, the constraint is volume (demand, budget or rank; split with operational signals).
6. **Corroborate** with one operational signal per link (see playbook). Two independent signals (statistical + operational) = high confidence. One = medium. Inconclusive boundary = propose the cheapest disambiguating test instead of picking.
7. **Guards**: mature cohorts only (age >= this account's conversion lag P90 from S04); day-of-week adjustment on weekly windows; ties broken by estimated delta T / (cost and time to fix); always report a runner-up.
8. **Gate 0 exception**: measurement and policy blockers outrank any constraint (section 2).

The model never computes any of this by hand. Every number in the brief cites a stats-result ID.

## 4. Five focusing steps (as sub-modes of diagnose)

| Step | Output | Rule |
|---|---|---|
| Identify | constraint + runner-up + falsifier | evidence and confidence per section 3 |
| Exploit | max 3 actions | zero new spend; act only on the constraint link |
| Subordinate | "do NOT do X now" list | everything that would push more volume into a starved link waits |
| Elevate | investment options | gated: needs approval, goes through the mutation gate (api plugin) |
| Repeat | next review date, baseline reset | close windows with S06/S07 (v0.3), log to constraint-history |

**Rope**: release spend at the pace the constraint absorbs. If sales capacity is the
constraint, budget increases are subordinated: more leads only lengthen the queue.

## 5. Constraint Brief (output contract)

```
VALIDITY: <first line, only when any stats-result is not "valid">
Constraint: <link> | evidence: <stats IDs, signal refs> | confidence: high|medium|low
Runner-up: <link> | why it lost
Falsifier: <observation that would prove this wrong>
Exploit (max 3): action | expected delta (stats ID, estimated) | window | rollback
Subordinate: do NOT <x> now, because <link>
Parking lot: one line each, no recommendation
Elevate (gated): option | cost | approval needed
Next review: <date> (end of the measurement window)
```

## 6. Constraint-to-instrument map

| Constraint | Instruments (run only when called for) |
|---|---|
| Visibility / Gate 0 | measurement-signal.md, S14, S15 |
| Demand | intel plugin: seo-paid-synergy, competitive-intel (if installed) |
| Budget | bidding-budget.md, S10 |
| Rank | qs-breakdown.md, competitive-intel |
| Click | creative-lp.md, qs-breakdown.md, S03 |
| On-site conversion | creative-lp.md, experiments-incrementality.md |
| Lead quality | measurement-signal.md (OCI), search-terms-negatives.md, intent-ladder.md |
| Sales capacity | action outside Ads; state that more spend will not help |
| Economics | unit-economics.md, seo-paid (intel), experiments-incrementality.md |

Specific user requests ("check my search terms") run the module directly, no diagnosis required.

## 7. Memory hooks

- Read before diagnosing: constraint-history, baselines, parking lot, open windows (memory-protocol.md).
- `--commit` writes the brief to constraint-history and parking-lot through ledger.py. Without it, the run is a dry read.
- If the constraint moved since last run, refresh baselines (anti-inertia) and resurface the parking lot.
- If a change on the same link is inside its measurement window, the brief says "frozen until <date>" instead of proposing a new change.
