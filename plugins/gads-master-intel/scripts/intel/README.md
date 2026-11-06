# scripts/intel (scaffold, v0.4)

- `auction_insights_ingest.py`: UI export CSV (Drive/Sheets/local) to competitor-observation rows.
- `serp_sampler.py`: provider adapter interface (ToS-compliant SERP API only; never scrape Google). N samples per keyword x geo x device x window; tags queries to account for own-ad impressions.
- `gsc_pull.py`: Search Console query x page with own history (retention is limited).
- `kp_bid_ranges.py`: Keyword Planner bid ranges as CPC-pressure proxy (labeled estimated).
- `query_join.py`: normalized query key join with coverage report.
