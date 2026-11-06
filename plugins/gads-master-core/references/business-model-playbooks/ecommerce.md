# Playbook: Ecommerce

Applies to business_model: `ecommerce`.
Chain file: `ecommerce.chain.yaml`. Run with `--playbook ecommerce`.

## Chain

```
Gate 0 > impressions > clicks > sessions > add_to_cart > checkout > purchase
```

| Link | Rate | Meaning |
|---|---|---|
| volume: impressions | count | demand, budget, rank, feed coverage (Shopping/PMax) |
| impressions to clicks | CTR | ad, price and image competitiveness |
| clicks to sessions | landing ratio | tracking loss, consent, slow pages, redirects (H-016) |
| sessions to add_to_cart | ATC rate | product page, price, stock, relevance of traffic |
| add_to_cart to checkout | checkout start rate | cart friction, shipping cost surprise |
| checkout to purchase | checkout completion | payment, account walls, errors (H-015 for ATC to purchase) |

Economics sits after purchase: purchases can flow while each one loses money
(ROAS below break-even per category, unit-economics.md).

## Input

Funnel CSV, one row per week, paid traffic only:
`period, impressions, clicks, sessions, add_to_cart, checkout, purchase`
Optional columns used by economics checks: `revenue, cost, gross_margin`.
Sessions and cart events come from analytics filtered to Google Ads traffic. If analytics is unavailable, the chain jumps clicks to purchase and middle links are `unknown`.

## Target-rate sources (r\*)

1. Owner-defined in profile.
2. Self-benchmark: P75 of mature weekly history (S16).
3. Heuristics, sanity only: H-014 (session to purchase), H-015 (ATC to purchase), H-016 (click to session). Confidence capped at low.

Lag is short for low AOV (H-011 as pointer; S04 decides). High AOV or considered purchases behave closer to SaaS lag.

## Operational corroboration signals

| Link | Signal |
|---|---|
| volume | lost IS budget on profitable categories, feed disapprovals (H-020), products with zero impressions, out of stock on top sellers |
| CTR | price above competitors on the same products (reported by price benchmarks), missing images or ratings, title without key attributes |
| clicks to sessions | consent mode gaps, redirects dropping gclid, page load time on mobile |
| ATC rate | traffic to out-of-stock or wrong-variant pages, price surprise vs ad, PMax final URL expansion sending traffic to blog pages |
| checkout start | shipping cost revealed late, forced account creation |
| checkout completion | payment errors, missing local payment methods, checkout errors logged |
| economics | category mix drift toward low margin, return rate by category, discount-driven conversions |

## Moves per constraint link

| Constraint | Exploit (zero new spend, max 3) | Subordinate (do NOT now) | Elevate (gated) |
|---|---|---|---|
| volume (feed) | fix disapprovals on top sellers; complete titles, GTINs, attributes | do not add budget while inventory is disapproved | feed management tooling |
| volume (budget) | move budget from below-break-even categories (S09, per-category break-even ROAS) to budget-limited profitable ones | do not raise budget on starved downstream links | budget increase at rope pace |
| volume (rank) | bid up profitable products losing rank IS; QS fixes on Search | do not chase low-margin volume | price changes |
| CTR | improve titles and images on top spend products; promotions and ratings where eligible | do not change prices for CTR without margin math | price repositioning |
| clicks to sessions | fix redirect and tracking loss, consent setup | do not judge downstream rates until fixed (it is measurement, close to Gate 0) | site speed work |
| ATC rate | exclude out-of-stock items; send traffic to the right variant; turn off URL expansion to non-product pages | do not scale traffic to weak product pages | product page redesign, A/B |
| checkout | report friction to the site owner with evidence; exclude affected products or markets temporarily | do not raise spend while checkout leaks | checkout rebuild, new payment methods |
| economics | cut or lower targets on low-margin categories; tROAS per category from break-even | do not judge by blended ROAS | bundles, free-shipping thresholds, pricing |

## Follow-up onboarding questions

- Gross margin by category (or at least top categories)?
- Return or refund rate by category?
- AOV and share of repeat customers? Is LTV tracked?
- Merchant Center feed: who manages it, how often does it update, current disapproval share?
- Stock constraints or seasonal inventory?
- Shipping cost policy and where it is shown?
- Are conversion values gross revenue, net of tax, or margin?

## Acceptance (v0.1)

Planted-constraint fixtures (one per link) are found by S16 with the expected runner-up; a fixture with clicks to sessions starving routes to measurement first; missing analytics columns produce `unknown` middle links.
