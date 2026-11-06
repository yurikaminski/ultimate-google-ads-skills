"""Pick only the questions investigation could not answer. Max 7 per round, ranked by impact."""
from __future__ import annotations

# target: ("context", field, sources_that_resolve) | ("profile", dotted_key) | None (owner input only)
USER = ("user", "account_data")
ANY = ("user", "account_data", "inferred")
BANK = [
    {"id": "Q01", "impact": 1, "playbooks": "all", "target": ("context", "conversion_path", USER),
     "q": "What is the one conversion that counts as a real result for the business?", "default": "the deepest visible conversion path"},
    {"id": "Q02", "impact": 1, "playbooks": "all", "target": ("profile", "targets.throughput"),
     "q": "What is the target per week for that result (T*)?", "default": "unknown: diagnose cannot run S16 without it"},
    {"id": "Q03", "impact": 1, "playbooks": "all", "target": ("profile", "unit_economics.gross_margin"),
     "q": "Gross margin (or margin by category)?", "default": "unknown"},
    {"id": "Q04", "impact": 2, "playbooks": "all", "target": ("context", "sales_cycle_days", ANY),
     "q": "Typical time from first click to closed deal or purchase?", "default": "unknown"},
    {"id": "Q05", "impact": 2, "playbooks": ["saas", "lead-gen"], "target": ("context", "tracking_maturity", USER),
     "q": "Do later-stage results (SQL, won, revenue) reach Google Ads through offline conversion import?", "default": "no"},
    {"id": "Q06", "impact": 2, "playbooks": "all", "target": None,
     "q": "Any capacity limit (sales team, inventory, support) that caps volume?", "default": "none known"},
    {"id": "Q14", "impact": 2, "playbooks": ["saas"], "target": ("profile", "unit_economics.payback_months_target"),
     "q": "What CAC payback period do you accept (months)?", "default": "unknown"},
    {"id": "Q16", "impact": 2, "playbooks": ["saas"], "target": ("profile", "targets.rates.sql"),
     "q": "How do you define an MQL/PQL and an SQL, and what share of MQLs become SQLs?", "default": "self-benchmark from your own history"},
    {"id": "Q17", "impact": 2, "playbooks": ["ecommerce"], "target": None,
     "q": "Margin by product category, and is the Merchant Center feed healthy (disapprovals)?", "default": "single margin, feed unchecked"},
    {"id": "Q07", "impact": 3, "playbooks": "all", "target": ("context", "owner_hypothesis_constraint", USER),
     "q": "Where do you think the bottleneck is today? (stored as a hypothesis, tested, never used as evidence)", "default": "none"},
    {"id": "Q08", "impact": 3, "playbooks": "all", "target": ("context", "do_not_touch", USER),
     "q": "Who approves changes, and what must never be touched?", "default": "owner approves everything; nothing off-limits"},
    {"id": "Q09", "impact": 3, "playbooks": "all", "target": None,
     "q": "Changes or tests in the last 90 days?", "default": "unknown"},
    {"id": "Q10", "impact": 3, "playbooks": "all", "target": ("context", "goal", USER),
     "q": "Goal this quarter: growth, efficiency or profit?", "default": "efficiency"},
    {"id": "Q15", "impact": 3, "playbooks": ["ecommerce"], "target": None,
     "q": "Return or refund rate?", "default": "unknown"},
    {"id": "Q11", "impact": 4, "playbooks": "all", "target": ("context", "markets", ANY),
     "q": "Markets by priority?", "default": "site markets, equal priority"},
    {"id": "Q12", "impact": 4, "playbooks": "all", "target": ("context", "seasonality", ANY),
     "q": "Seasonality you plan around?", "default": "none known"},
    {"id": "Q13", "impact": 4, "playbooks": "all", "target": ("context", "regulatory_flags", ANY),
     "q": "Regulated category (health, finance, gambling, etc.)?", "default": "inferred from site"},
]


def _profile_value(prof: dict, key: str):
    cur = prof
    for k in key.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def select(context_fields: dict, profile: dict, playbook: str, answered: set[str] | None = None,
           max_q: int = 7) -> list[dict]:
    answered = answered or set()
    out = []
    for q in sorted(BANK, key=lambda q: (q["impact"], q["id"])):
        if q["id"] in answered or (q["playbooks"] != "all" and playbook not in q["playbooks"]):
            continue
        t = q["target"]
        if t and t[0] == "context":
            f = context_fields.get(t[1]) or {}
            if f.get("source") in t[2] and f.get("value") not in (None, [], ""):
                continue
        elif t and t[0] == "profile" and _profile_value(profile, t[1]) is not None:
            continue
        out.append({"id": q["id"], "question": q["q"], "default": q["default"], "impact": q["impact"],
                    "allow_dont_know": True})
    return out[:max_q]
