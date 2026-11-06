# Playbook: SaaS

Applies to business_model: `saas_plg`, `saas_sales_led`, `saas_hybrid`.
Chain file: `saas.chain.yaml`. Run with `--playbook saas`.

## Chain

```
Gate 0 > impressions > clicks > signups_or_leads > activated_or_mql > sql > won
```

| Link (upstream to downstream) | Rate | PLG meaning | Sales-led meaning |
|---|---|---|---|
| volume: impressions | count | demand, budget, rank | same |
| impressions to clicks | CTR | ad to query match | same |
| clicks to signups_or_leads | visit-to-signup / visit-to-lead | trial or free signup | demo request or contact form |
| signups_or_leads to activated_or_mql | activation / MQL rate | user reached the activation event (owner defines) | lead met MQL definition |
| activated_or_mql to sql | PQL-to-SQL / MQL-to-SQL | product-qualified account accepted by sales or self-serve paid | sales accepted the lead |
| sql to won | win rate | paid conversion | closed won |

Hybrid: map both paths into the same stages; the owner chooses whether a trial signup and a demo request both count as `signups_or_leads`. Record the choice in business-context `conversion_path`.

## Input

Funnel CSV, one row per week (or month), mature cohorts only:
`period, impressions, clicks, signups_or_leads, activated_or_mql, sql, won`
Stages after clicks usually come from the CRM or product analytics, matched to paid traffic by UTM, gclid or OCI. If a stage is missing, it is `unknown` and the chain stops there.

## Target-rate sources (r\*)

1. Owner-defined in profile (`targets.rates.<link>`): preferred for activation, MQL-to-SQL and win rate, since definitions vary by company.
2. Self-benchmark: P75 of mature weekly history (S16 computes).
3. Heuristics, sanity check only: H-001 (CTR), H-013 (visit-to-signup), H-018 (MQL-to-SQL). Confidence capped at low.

Lag: SQL and won mature slowly (H-012 as a pointer; S04 decides). Immature weeks are excluded, so a young account may have `unknown` on the last two links. Say so first.

## Operational corroboration signals

| Link | Signal (from account data, CRM or user report) |
|---|---|
| volume | lost IS budget on profitable terms (H-004), lost IS rank (H-005), low brand IS (H-006), category search volume near zero |
| CTR | CTR on rung 2 terms below account baseline; ad-to-query mismatch on top spend terms |
| visit-to-signup | landing page mismatch, form friction, slow mobile page, high share of spend on rungs 4-5 |
| activation / MQL | share of signups from junk terms (students, jobs, free tools); signups with personal emails when ICP is B2B |
| MQL-to-SQL | sales rejects with reason "not ICP"; no OCI so bidding optimizes to raw leads |
| win rate | lost-deal reasons (price, competitor, timing); long open-opportunity age |
| sales capacity | leads uncontacted beyond SLA (H-019), SQL backlog above rep capacity |

## Moves per constraint link

| Constraint | Exploit (zero new spend, max 3) | Subordinate (do NOT now) | Elevate (gated) |
|---|---|---|---|
| volume (demand) | expand to proven rung 2 terms not yet covered; fix ad schedule and geo exclusions that cut converting traffic | do not open rungs 4-5 to buy volume | competitor rung, new channels upstream |
| volume (budget) | move budget from below-break-even segments (S09) to budget-limited profitable campaigns | do not raise budget on campaigns whose downstream link is starved | raise budget at the rope pace |
| volume (rank) | QS fixes on top spend keywords (qs-breakdown.md), bid on profitable terms losing rank IS | do not chase top-of-page on low-intent terms | landing page rebuild |
| CTR | headlines matching query themes; split mixed-theme ad groups | do not rotate creative while the window is open | new offer angle |
| visit-to-signup | route high-intent ad groups to the best converting page; cut form fields | do not add traffic sources to the page | new landing pages, A/B (S02/S03) |
| activation / MQL | negatives through the gate on junk terms; import activation/MQL as secondary conversion | do not bid on raw signups if junk share grows | onboarding/product changes (outside Ads) |
| MQL-to-SQL | OCI of SQL; shift bidding to SQL when volume allows (H-007); tighten intent rung mix | do not scale lead volume | sales enablement, routing (outside Ads) |
| win rate | tag lost reasons by campaign; cut campaigns whose SQLs never win (S09 on win rate) | do not judge by platform CPA | pricing, packaging (outside Ads) |
| sales capacity | slow spend to the rate sales absorbs (rope); prioritize highest-intent rungs | do not raise budget: more leads only lengthen the queue | hire or add self-serve path |

## Follow-up onboarding questions (after the general bank)

- What is the activation event (PLG) or MQL definition? Who decided it?
- What makes an SQL or PQL? Is it recorded with a date in the CRM?
- Do SQL and won events flow back to Google Ads (OCI) with value?
- Average contract value or plan mix by acquisition source?
- Sales capacity: SQLs per rep per week, response SLA?
- Payback period accepted for CAC (unit-economics.md)?
- Trial length and the share of paid conversions that happen after trial end?

## Acceptance (v0.1)

Planted-constraint fixtures (one per link) are found by S16 with the expected runner-up; immature SQL/won weeks are excluded; missing CRM stages produce `unknown`, not a guess.
