# Quality Score breakdown (instrument)

Load when: the constraint is rank or click, or the user asks for a QS review.
QS is a diagnostic, not a goal. There is no "QS < 7 = fail" rule.

## Data

GAQL (api plugin, v0.2) or CSV export with these columns:

```
ad_group_criterion.quality_info.quality_score
ad_group_criterion.quality_info.search_predicted_ctr
ad_group_criterion.quality_info.creative_quality_score      (ad relevance)
ad_group_criterion.quality_info.post_click_quality_score    (landing page experience)
metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions
```

Verify field names against the current API version before use (gaql-notes.md).

## Method

1. Weight QS and each component by impressions (rank questions) or spend (cost questions).
2. Compare against this account's own distribution: flag keywords in the lowest weighted quartile, not below a fixed number.
3. Low-volume keywords: QS is unstable or null. Mark `unknown`; use S09-style pooling at ad group level instead.
4. Map component to cause to fix:

| Component below account norm | Likely cause | Fix |
|---|---|---|
| Expected CTR | weak ad for the query, wrong rung in the ad group | tighter theme, query-matching headline |
| Ad relevance | keywords and ad text diverge | split theme, rewrite headline 1 |
| Landing page experience | mismatch, slow mobile page | message match, page speed (creative-lp.md) |

5. CPC savings from QS gains are always "estimated", from S13 (planned v0.3) robust regression of CPC on QS with CI. Until S13 exists, do not quote a savings figure.

## Output

Keyword or ad group | weight | QS | weakest component | cause | fix | evidence status.
