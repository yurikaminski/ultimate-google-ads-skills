---
name: connect
description: "Planned for v0.2, not implemented: read-only Google Ads API connection (OAuth with a Google Cloud project) and report pulls into the CSV contracts used by gads-master-core."
disable-model-invocation: true
---

# connect (scaffold, v0.2)

Status: NOT IMPLEMENTED. Until v0.2, use CSV exports, or the official Google Ads MCP tools if they are present in the session (read-only `search` with GAQL).

Plan (v0.2)
- Auth: OAuth 2.0 user flow on the user's own Google Cloud project. Developer tokens were sunset on 2026-09-09 (claims-ledger C-001): access level belongs to the Cloud project; do not ask for a developer token.
- Credentials stay in the user's own config (google-ads.yaml or env vars). Never stored by this plugin. doctor.py only checks presence.
- Read-only GAQL pulls mapped to core inputs: funnel top stages (impressions, clicks, conversions by week), account export for S15, search terms for S09, conversion lag for S04.
- Change history (limited retention) reconciled with decision-log to catch outside edits.

Acceptance criteria: pulls validate against the core CSV contracts; no mutate calls exist in the codebase; doctor reports `api: available` only with credentials present and a successful read.
