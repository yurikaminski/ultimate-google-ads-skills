---
name: intel
description: "Planned for v0.4, not implemented: Competitive intel."
disable-model-invocation: true
---

# intel (scaffold, v0.4)

Status: NOT IMPLEMENTED. Report intel instruments as unavailable. Never substitute guesses. Hard stops: no Google SERP scraping, never click competitor ads, respect trademark policy.

What it will do: Competitive intel: own impression share layers, Auction Insights from UI exports (API access reported denied, claims-ledger C-003), ToS-compliant SERP sampler adapter, Transparency Center and ad libraries.

TODO
- Scripts in `scripts/intel/` (see README there), schemas in `schemas/`.
- Tests with saved fixtures, no live network.

Acceptance criteria: Share-of-paid-SERP from N samples per keyword x geo x device x window, never one snapshot; competitor claims labeled reported; decision tree (rank vs budget vs brand hijack) cites stats ids.
