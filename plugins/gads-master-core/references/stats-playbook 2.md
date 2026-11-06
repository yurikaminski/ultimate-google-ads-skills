# Statistics playbook

Load when: any module needs a number. The model never does arithmetic by hand:
every number in a recommendation comes from a stats-result with its ID cited.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/run.py" stats <S01|S04|S09|S15|S16> --in data.csv --cfg cfg.yaml --out result.json
```

Local Python only, no network, deterministic seeds, input hash for lineage.
Risk parameters (alpha, loss tolerance, windows) come from profile.yaml; defaults are
flagged "to calibrate" in the result.

## stats-result.v1

```
{id, n, estimate, ci, method, assumptions_checked, warnings,
 validity: valid | low_power | insufficient, status}
```

## Warn-first policy

- `valid`: proceed normally.
- `low_power`: the FIRST line of the response states the problem (e.g. "Only 14 conversions in the window: results are indicative"). Proceed if the user wants, mark findings "indicative", cap confidence at low.
- `insufficient`: same first line, the finding becomes indicative with confidence low, or `unknown` only if there is no data at all.
- Validity never blocks the user.

## Catalog

| ID | Analysis | Status | Used by |
|---|---|---|---|
| S01 | Confidence intervals: Wilson (rates), Poisson (counts), bootstrap (ratios) | implemented v0.1 | diagnose, search-terms, intel |
| S02 | Power, sample size, MDE | planned v0.3 | experiments, bidding-budget, seo-paid |
| S03 | A/B: Bayesian expected loss or frequentist, Holm/BH correction | planned v0.3 | experiments, creative, attribution |
| S04 | Conversion lag distribution, maturity cutoff, nowcasting | implemented v0.1 | diagnose, forecast |
| S05 | Baseline and seasonality: day-of-week, robust z, EWMA/CUSUM | planned v0.3 | diagnose (DOW adjust is inside S16 in v0.1), pacing, monitor |
| S06 | Change-point detection, cross-checked with decision log | planned v0.3 | monitor, intel, decision review |
| S07 | Causal impact: synthetic control, diff-in-diff, placebo | planned v0.3 | seo-paid, decision review |
| S08 | Geo-lift design: matched markets, power by simulation | planned v0.3 | seo-paid, brand tests |
| S09 | Empirical-Bayes shrinkage (beta-binomial): P(true CVR >= break-even) | implemented v0.1 | search-terms, qs-breakdown |
| S10 | Response curves (Hill/power), marginal CPA, allocation | planned v0.3 | bidding-budget |
| S11 | Forecasting with intervals, rolling-origin backtests | planned v0.3 | pacing, forecast |
| S12 | Rate x mix decomposition, Simpson's paradox check | planned v0.3 | report, attribution |
| S13 | Robust regression (QS to CPC, CTR x position) with CI | planned v0.3 | qs-breakdown |
| S14 | Platform vs CRM reconciliation (ratio with CI, volume tolerance) | planned v0.3 | Gate 0, report |
| S15 | Data quality: plausibility, duplicates, drift between exports | implemented v0.1 (basics) | diagnose, Gate 0 |
| S16 | Queue/starvation boundary (toc-engine.md section 3) | implemented v0.1 | diagnose |

## Method notes

- **S01**: Wilson for proportions (stable at small n and near 0 or 1). Poisson exact (chi-square) interval for counts. Bootstrap percentile for ratios such as CPA, seeded.
- **S04**: empirical CDF of click-to-conversion lag; maturity cutoff = configurable quantile (default P90, "to calibrate"). Nowcast = observed / F(age) per cohort, flagged estimated. Fewer lag observations than the config minimum: validity low_power.
- **S09**: fit beta prior by method of moments across segments (campaign or ad group pool); posterior Beta(a + conv, b + clicks - conv); report P(CVR >= break-even CVR). Replaces rules like "50 clicks and no conversion".
- **S15**: negative values, conversions > clicks, clicks > impressions, duplicate keys, missing dates, sudden drift between two exports of the same window.
- **S16**: V\* per stage from T\* and r\*, Poisson CI per stage count, classification starvation/ok/inconclusive/unknown, constraint and runner-up.

## Guarantees tested

- CI coverage near nominal by simulation (S01).
- Type-I error of the starvation call near alpha under the null (S16).
- Planted constraints are found with the correct runner-up (tests/fixtures).
