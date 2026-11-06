# Bidding and budget

Load when: the constraint is budget, the user asks about bid strategy or budget
allocation, or pacing runs.

## Bid strategy by conversion volume (labeled heuristics)

Volume thresholds below are heuristics from heuristics-registry.json, compared to
this account's own stability (CPA variance week to week), never applied as pass/fail alone.

| Conversions per campaign per 30d (vs H-007/H-008) | Typical fit |
|---|---|
| very low | Manual CPC or Maximize Clicks with CPC cap; consolidate first |
| low to moderate | Maximize Conversions without target, observe stability |
| stable volume | tCPA, set near the observed CPA, then move in small steps |
| stable volume with values | Maximize Conversion Value / tROAS from break-even ROAS (unit-economics.md) |

Rules:
- Change target in small steps and respect the learning window (H-010). Log every change in decision-log so overlapping windows are visible.
- Never switch strategy and target in the same window on the same campaign.

## Marginal CPA

Average CPA hides the cost of the last conversion. Budget decisions use marginal CPA:
the extra cost of one more conversion at the current spend level.

- S10 (planned v0.3) fits response curves (Hill/power) per campaign and returns marginal CPA with CI.
- Until S10 exists: use lost IS (budget) plus average CPA as a labeled proxy, confidence low.
- Allocation rule: move budget from campaigns with high marginal CPA to those with low marginal CPA until they are equal, within the rope (toc-engine.md).

## Budget as constraint

Budget is the constraint when the volume stage starves, lost IS (budget) is material on
terms whose CVR is at or above break-even (S09), and downstream stages have slack.
- Exploit: move budget from below-break-even segments to budget-limited profitable ones (zero new spend).
- Elevate: raise budget, gated, released at the pace the next link absorbs.
- If the next link is sales capacity, budget is subordinated, not raised.

## Pacing (on-demand)

Expected spend to date from S05 baseline with day-of-week shape; flag deviation beyond
the baseline band, not beyond a fixed percent. S11 forecast planned v0.3.
