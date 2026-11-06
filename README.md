# google-ads-master

An evidence-first Google Ads skill for Claude Code, shipped as a plugin marketplace with three plugins:

| Plugin | Status | What it does |
|---|---|---|
| `gads-master-core` | v0.1, working | Onboarding by investigation, Theory of Constraints diagnosis, local statistics (`adsstats`), per-account memory. Read-only. Input: CSV/exports. |
| `gads-master-api` | scaffold (v0.2 to v0.3) | Google Ads API read access, then writes gated by the mutation gate. |
| `gads-master-intel` | scaffold (v0.4) | Auction insights ingest, SERP sampler adapter, Search Console, SEO x Paid. |

Core works alone. Without api or intel installed, those capabilities are reported as unavailable and core falls back to CSV/exports.

## What makes it different

- **One constraint at a time.** "Optimize my account" runs a queue/starvation test (S16) over your funnel and returns a Constraint Brief: one constraint with evidence and confidence, a runner-up, what would falsify it, max 3 zero-spend actions, what NOT to touch now, and a parking lot.
- **Statistics run locally, warn first.** Every number comes from a local Python stats result with an id. When data is thin, the first line says so; the analysis still runs, marked indicative, confidence capped at low.
- **No universal thresholds.** "QS < 7" or "CTR < 1.5%" never fails anything alone. Heuristics are labeled and compared to the account's own baseline.
- **Onboarding by investigation.** It reads your site and competitors first, drafts the business context with provenance on every field, and asks only what it could not deduce (max 7 questions).
- **Memory per account.** Decisions, measurement windows, constraint history and baselines live in your workspace. Changes inside an open measurement window are frozen; flip-flops are flagged.

## Install

Requirements: Claude Code and Python 3.10+ (or [uv](https://docs.astral.sh/uv/), which also provides Python).

Python packages install themselves: on first use the skill asks once and runs `run.py setup`, which creates a private venv at `~/.gads-master/venv` (or `$CLAUDE_PLUGIN_DATA/venv`), outside the plugin folder so updates keep it. Nothing is installed into your system Python.

From the GitHub repo (after it is published):

```
/plugin marketplace add <owner>/google-ads-master
/plugin install gads-master-core@google-ads-master
```

From a local clone:

```bash
claude plugin marketplace add ./google-ads-master
claude plugin install gads-master-core@google-ads-master
```

Development (no install):

```bash
claude --plugin-dir ./plugins/gads-master-core
```

Then ask: "optimize my Google Ads account". The `gads-master` skill runs `doctor`, then `onboard` (if there is no context), then `diagnose`. Explicit entry points: `/gads-master-core:onboard`, `/gads-master-core:diagnose`.

## Data flow (what stays local)

| Data | Where it goes |
|---|---|
| Your CSV exports, funnel data, stats | Read and computed locally by Python. The stats package has no network code. |
| Business context, profile, decision log, baselines | `<workspace>/.gads-master/<account_id>/`, plain files, deletable. Outside the plugin folder, so updates never overwrite them. |
| Public web pages (onboarding) | Fetched from the sites you name, robots.txt respected. Only structured signals and URLs are kept, never page text. Google SERPs are never fetched. |
| Credentials | Never stored. `doctor` only checks whether they are present. |
| Third-party hosted MCP servers | None by default. |

Everything Claude reads from pages, ads, search terms or competitor copy is treated as untrusted data. Instructions inside it are ignored, and raw external text is never written into state files.

## Limits (v0.1)

- Input is CSV/exports. API access arrives in v0.2.
- No writes to Google Ads. Changes are drafts that you apply; the gate precondition is in place for v0.3.
- Implemented stats: S01 (CIs), S04 (conversion lag), S09 (empirical-Bayes shrinkage), S15 (data quality), S16 (constraint finder). S02, S03, S05 to S08 and S10 to S14 are planned for v0.3.
- Full playbooks: SaaS and ecommerce. App, marketplace, lead gen and local are scaffolds (diagnose returns `unknown`).
- On-demand modules (audit, weekly, monitor, pacing, forecast, creative, experiment, attribution, report) are invocation-disabled scaffolds.
- Heuristics in `references/heuristics-registry.json` are practitioner-sourced and labeled; dated platform facts live in `references/claims-ledger.md` with verification status.

## Hard stops

No generic negative-keyword lists. No Google SERP scraping. Never click competitor ads. No invented health score. Trademark policy respected in competitor conquesting. New campaigns (v0.3) are created PAUSED.

## Tests

```bash
python3 plugins/gads-master-core/scripts/run.py setup
~/.gads-master/venv/bin/python -m pip install pytest
cd plugins/gads-master-core/tests && ~/.gads-master/venv/bin/python -m pytest -q
```

They cover planted-constraint fixtures for every chain link in both playbooks, statistical calibration by simulation (CI coverage, type-I error, power), contract tests (schemas, evidence types, stats id citations, the warn-first line, no write without an approved draft), and onboarding from saved HTML fixtures with no live network.

## Pre-submission checklist mapping

| Checklist area | Status |
|---|---|
| Repository and folder layout | `.claude-plugin/marketplace.json` at root; each plugin has `.claude-plugin/plugin.json` only in that folder; components at plugin root. |
| Manifest and plugin name | Kebab-case permanent names, `displayName`, semver versions. `claude plugin validate --strict` passes for the marketplace and all three plugins. |
| README and license | README at root and in each plugin; MIT `LICENSE` at root and in each plugin; `NOTICE` credits prior art. |
| Files in the plugin folder | No binaries, no secrets, no `.env`; `.gitignore` excludes venvs and runtime state. |
| What the plugin runs and connects to | Local Python only. Network: only the onboarding fetcher, to sites the user names. No MCP servers, no hooks. |
| Hooks, skills, commands, agents | Skills under `skills/<name>/SKILL.md`; scaffold skills set `disable-model-invocation: true`; agents are read-only (`Read, Grep, Glob, Bash`). No hooks. |
| Security scan | No credential handling, no remote code download, no shell interpolation of external content. |
| Behavior test | `pytest` suite; `claude plugin eval` suite: TODO before directory submission. |
| `homepage` / `repository` fields | TODO: add after the GitHub repo is published. |

## Credits

See `NOTICE`. Concepts studied from AgriciDaniel/claude-ads, irinabuht12-oss/marketing-skills and ivangfalco/ads-skills; reimplemented, nothing copied.

## License

MIT
