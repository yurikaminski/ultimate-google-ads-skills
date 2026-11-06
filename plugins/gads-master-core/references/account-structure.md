# Account structure

Load when: audit, structure questions, or diagnose points at click/rank links and
structure is a suspected cause.

## Principles

- **Themed ad groups, not SKAGs.** Group keywords by one theme and one landing page. Single-keyword ad groups starve smart bidding of signal and multiply maintenance.
- **Consolidate for signal.** Smart bidding needs conversion volume per campaign. Splitting campaigns below the volume the bid strategy needs (heuristics-registry H-007, H-008) trades signal for control. Split only when budget, geo, margin or intent rung genuinely differs.
- **Brand vs non-brand always split.** Brand CPA flatters blended numbers. Separate campaigns, separate targets, brand excluded from non-brand (negative or brand exclusion).
- **One intent rung per campaign** where volume allows (intent-ladder.md).
- **Geo and language** follow markets in business-context; currency per account is fixed, so multi-currency needs separate accounts.

## PMax / AI Max overlap

- Performance Max and Search can serve the same query. The commonly cited rule is that identical exact-match Search keywords win over PMax and other overlaps go to ad rank (claims-ledger C-004, unverified). Verify before relying on it.
- Check: brand terms leaking into PMax (brand exclusions), PMax cannibalizing remarketing, search-term share visible in PMax insights.
- AI Max for Search expands matching and rewrites assets. Treat it as a test with its own window, not a default.

## Controls (evidence required, no score)

| Check | Evidence | Pass | Fail | Unknown |
|---|---|---|---|---|
| Brand split | campaign list + search terms | brand and non-brand separate, brand excluded from non-brand | brand terms > baseline share in non-brand spend | no search-term data |
| Signal per campaign | conversions per campaign per 30d | volume fits the bid strategy's heuristic, compared to account history | tCPA/tROAS campaigns far below the heuristic with volatile CPA | conversions not imported |
| Landing page per theme | ad group to final URL map | one theme, one page | generic homepage for high-intent themes | URLs not provided |

The model reports pass/fail/unknown per control with evidence refs. No aggregate health score.
