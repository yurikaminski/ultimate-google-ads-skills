# Claims ledger

Dated, mutable facts about platforms, APIs and policies. Each entry has an official
source and a retrieval date. Anything not checked against a source is "unverified"
and cannot be the sole evidence for a finding. Refresh before relying on any entry
older than 90 days.

| ID | Claim | Source | Retrieved | Status |
|---|---|---|---|---|
| C-001 | Google Ads API developer tokens were sunset on 2026-09-09. API access level now belongs to the Google Cloud project. The developer-token header is optional and ignored by the API servers; Google states a future major version will start rejecting it. | https://developers.google.com/google-ads/api/docs/api-policy/developer-token | 2026-11-06 | verified |
| C-002 | Current Google Ads API major version is v26, released 2026-10-14. | https://developers.google.com/google-ads/api/docs/release-notes | 2026-11-06 | verified |
| C-003 | Auction Insights metrics requested through the API return METRIC_ACCESS_DENIED (live query on v24, August 2026). Ingest Auction Insights from scheduled UI report exports (CSV/Drive/Sheets). | https://lucidvitals.com/blog/google-ads-auction-insights | 2026-11-06 | reported, unverified officially |
| C-004 | Exact-match Search keywords identical to the query take priority over Performance Max for that query. | none checked | n/a | unverified |
| C-005 | Account change history (change_event) is queryable only for a limited recent window. | none checked | n/a | unverified |
| C-006 | Search Console keeps a limited history of query data, so the intel plugin stores its own history. | none checked | n/a | unverified |

## How to add an entry

1. Find the official source (Google developer docs, Google Ads Help, official blog). Third-party reports are allowed only with status "reported".
2. Add a row with the next ID, the exact claim, URL, retrieval date, status.
3. Findings that depend on a claim cite its ID in evidence refs.
