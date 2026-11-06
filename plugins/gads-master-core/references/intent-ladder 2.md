# Intent ladder

Load when: the constraint is lead quality or demand, when structuring Search, or
when the user asks where to spend next.
Credit: concept adapted from public practitioner material (see NOTICE), reimplemented.

Search captures demand that already exists. Spend climbs the ladder one rung at a
time; a rung opens only after the one below proves it converts to the final stage
(SQL, won deal or purchase), not just to a form fill.

| Rung | Intent | Query signals | What "proven" means |
|---|---|---|---|
| 1. Brand | wants you | brand name, brand + pricing/login/reviews | defended at acceptable CPC; see brand rules below |
| 2. High intent non-brand | ready to buy a solution | category + software/tool/buy/price/near me, "best X for Y" | final-stage CVR with CI above break-even (S09) |
| 3. Competitor | evaluating alternatives | competitor + alternative/vs/pricing | pipeline per spend vs rung 2, measured in the CRM |
| 4. Problem aware | has the problem, not shopping | how to, fix, reduce, template | longer lag; judge only mature cohorts (S04) |
| 5. Demand gen | unaware | broad, Display, YouTube, Demand Gen | only with spare budget and patience for lag |

## Rules

- Classify search terms into rungs before judging them. Mixing rungs in one ad group hides which rung pays.
- Low volume is normal on rungs 2 and 3 in B2B. Use S09 shrinkage instead of a click count rule.
- Brand: organic rank 1 never justifies pausing brand by itself. Reduce brand only via a pre-registered incrementality test (experiments-incrementality.md). If a competitor bids on the brand, the verdict is defend.
- Competitor terms: respect trademark policy. No competitor trademarks in ad text unless the user confirms authorization. Never click competitor ads.
- Rung 4 and 5 traffic converts later and lower. Do not compare its CPA to rung 2 inside the same window.
- If the category has near-zero search volume, say so: Search is a small play and the demand link sits upstream (other channels).

## Use in diagnose

- Lead quality constraint: share of spend on rungs 4-5 and on unclassified terms is an operational corroboration signal.
- Demand constraint with rungs 1-2 saturated (high impression share, low lost IS): elevate means rung 3 or channels outside Search, gated.
