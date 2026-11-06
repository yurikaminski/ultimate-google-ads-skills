# GAQL notes

Load when: the api plugin (v0.2) builds queries, or a user supplies GAQL exports.
Field names change between API versions. Verify every field against the current
version's reference (claims-ledger C-002) before running a query. An
`UNRECOGNIZED_FIELD` or `INVALID_ARGUMENT` error is a query to repair, never an empty dataset.

Record per query: customer ID, API version, resource, fields, date window, row grain.

## Core queries (read-only)

Campaign performance with impression share:

```sql
SELECT campaign.id, campaign.name, campaign.advertising_channel_type,
       metrics.impressions, metrics.clicks, metrics.cost_micros,
       metrics.conversions, metrics.conversions_value,
       metrics.search_impression_share,
       metrics.search_budget_lost_impression_share,
       metrics.search_rank_lost_impression_share,
       metrics.search_top_impression_share,
       metrics.search_absolute_top_impression_share
FROM campaign
WHERE segments.date BETWEEN '{start}' AND '{end}'
```

Search terms:

```sql
SELECT search_term_view.search_term, campaign.id, ad_group.id,
       metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions
FROM search_term_view
WHERE segments.date BETWEEN '{start}' AND '{end}'
```

Keyword quality (qs-breakdown.md):

```sql
SELECT ad_group.id, ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type,
       ad_group_criterion.quality_info.quality_score,
       ad_group_criterion.quality_info.search_predicted_ctr,
       ad_group_criterion.quality_info.creative_quality_score,
       ad_group_criterion.quality_info.post_click_quality_score,
       metrics.impressions, metrics.cost_micros
FROM keyword_view
WHERE segments.date BETWEEN '{start}' AND '{end}'
```

Conversion actions (Gate 0):

```sql
SELECT conversion_action.name, conversion_action.category, conversion_action.status,
       conversion_action.primary_for_goal, conversion_action.counting_type
FROM conversion_action
```

## Pitfalls

- Money is in micros: divide `cost_micros` by 1,000,000 in code, never by hand.
- Adding `segments.date` changes grain to one row per day. Keyword rows repeat per match type. Deduplicate by (ad_group_id, keyword text, match type) before aggregating.
- Quality score fields are snapshots; they do not take a date segment the way metrics do. Check compatibility in the field reference.
- Impression share metrics are ratios: aggregate from components or re-query at the needed grain, never average them.
- Change history (change_event) has limited retention and requires a date filter (claims-ledger C-005, unverified). Store your own decision log.
- Manager accounts: set login-customer-id correctly; record it with the query.
- Auction Insights: not available through the API at last check (C-003). Use CSV ingestion.
