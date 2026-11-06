# API notes (scaffold, v0.2)

- Auth: Google Cloud project access level; developer token header optional and ignored since 2026-09-09 (claims-ledger C-001, verified).
- Version: v26 released 2026-10-14 (C-002). Pin the version in code and re-verify fields on each upgrade.
- Fields: verify every GAQL field against the active version reference before use (see core `gaql-notes.md`).
- Change history: `change_event` retention is limited (C-005, unverified): snapshot it into the decision log on every run.
- Quotas: TODO, verify current limits in official docs before v0.2 ships.
