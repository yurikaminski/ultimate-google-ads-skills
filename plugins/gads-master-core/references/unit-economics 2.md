# Unit economics

Load when: onboarding captures targets, diagnose lands on the economics link, or
the user asks "what CPA/ROAS can I afford".

All values live in `profile.yaml` (numbers) with provenance in `business-context.md`.
Read and write them only through:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/run.py" profile <get|set> --workspace W --account A
```

## Definitions

| Term | Formula | Notes |
|---|---|---|
| Gross margin (GM) | (revenue - COGS) / revenue | ecommerce: per category if margins differ |
| Contribution per conversion | AOV or first-period revenue x GM | before ad cost |
| Break-even ROAS | 1 / GM | ROAS below this loses money on the first order |
| Target ROAS | 1 / (GM - target profit share) | owner sets target profit share |
| Max CAC (payback) | monthly gross profit per customer x payback months | SaaS: owner sets payback months |
| LTV | gross profit per period x expected lifetime | only when retention data exists; otherwise unknown |
| Target CAC | min(max CAC from payback, LTV / target LTV:CAC ratio) | ratio is owner input, not a universal 3:1 |
| T\* | target throughput per period at the final stage | SQLs, wins or purchases |

## Rules

- Never assume a margin, payback or LTV ratio. Missing input = `unknown` and a question in the onboarding bank.
- Break-even and targets are deterministic arithmetic, but still run through the profile tool so every number has a source and a date.
- Use **marginal** CPA for budget decisions, not average CPA (bidding-budget.md).
- SaaS: price is per month or per seat; normalize to the period the owner uses for payback. Sales-led deals: use pipeline value x historical win rate only when win rate has its own CI (S01).
- Ecommerce: blended ROAS hides category mix. If GM differs by category, compute break-even ROAS per category and flag campaigns whose mix drifted (S12 planned v0.3).
- Returns and refunds reduce revenue before GM. Ask for the return rate; default "unknown", not zero.

## Economics as constraint

The economics link is the constraint when volume flows but each unit is unprofitable
(CPA above target CAC with CI, or ROAS below break-even with CI).
Exploit moves: cut spend on segments where P(CVR >= break-even CVR) is low (S09), shift
to higher-margin categories, fix the offer or AOV (bundles, thresholds).
Elevate: pricing changes, new offer, LTV improvements (outside Ads, gated).
