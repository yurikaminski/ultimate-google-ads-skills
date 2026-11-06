# gads-master-core

Core plugin of google-ads-master (v0.1). See the repository README for install, data flow and limits.

- Skills: `gads-master` (router), `onboard`, `diagnose`; v0.3 scaffolds (invocation disabled): audit, weekly, monitor, pacing, forecast, creative, experiment, attribution, report.
- Agents: `audit-measurement`, `audit-search`, `audit-structure`, `audit-automation` (read-only, return finding.v1).
- CLI: `python3 scripts/run.py <doctor|stats|context|profile|ledger|onboard|diagnose>`.
- Stats: `python -m adsstats <S01|S04|S09|S15|S16> --in data.csv --cfg stats-config.yaml --out result.json` (from `scripts/stats`).
- Python deps: `python3 scripts/run.py setup` (private venv, one time).
