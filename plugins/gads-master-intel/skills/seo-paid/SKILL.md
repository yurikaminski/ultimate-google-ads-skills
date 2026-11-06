---
name: seo-paid
description: "Planned for v0.4, not implemented: SEO x Paid matrix."
disable-model-invocation: true
---

# seo-paid (scaffold, v0.4)

Status: NOT IMPLEMENTED. Report intel instruments as unavailable. Never substitute guesses. Hard stops: no Google SERP scraping, never click competitor ads, respect trademark policy.

What it will do: SEO x Paid matrix: join Ads search terms, Search Console, GA4/CRM and SERP samples on a normalized query key; verdicts per query; top 5 opportunities in value terms.

TODO
- Scripts in `scripts/intel/` (see README there), schemas in `schemas/`.
- Tests with saved fixtures, no live network.

Acceptance criteria: Join coverage (% spend and clicks) always reported; organic position 1 never justifies pausing paid alone; brand reductions only via pre-registered incrementality tests (S07/S08).
