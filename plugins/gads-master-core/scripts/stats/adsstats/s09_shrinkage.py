"""S09: empirical-Bayes beta-binomial shrinkage. P(true CVR >= break-even | data) per entity.

Replaces rules like "50 clicks and no conversion = pause".
"""
from __future__ import annotations

import numpy as np
from scipy import stats

from .core import result


def fit_prior(x: np.ndarray, n: np.ndarray, min_entities: int) -> tuple[float, float, str]:
    m = n > 0
    pooled = x[m].sum() / max(n[m].sum(), 1)
    if m.sum() < min_entities:
        s = 2.0  # weak prior: two pseudo-clicks
        return max(pooled * s, 1e-3), max((1 - pooled) * s, 1e-3), "weak_pooled"
    p = x[m] / n[m]
    mu, var = np.average(p, weights=n[m]), np.average((p - pooled) ** 2, weights=n[m])
    binom_var = mu * (1 - mu) / np.mean(n[m])
    if var <= binom_var or mu <= 0:
        s = max(n[m].sum() / m.sum(), 2.0) * 10  # little heterogeneity: strong pooling
    else:
        s = max(mu * (1 - mu) / (var - binom_var) - 1, 1.0)
    return max(mu * s, 1e-3), max((1 - mu) * s, 1e-3), "method_of_moments"


def run(df, cfg, h):
    need = {"entity", "clicks", "conversions"}
    if not need <= set(df.columns):
        raise ValueError(f"S09 needs columns {sorted(need)} (+ cost when using target_cpa)")
    c9, a = cfg["s09"], cfg["alpha"]
    x, n = df.conversions.to_numpy(float), df.clicks.to_numpy(float)
    if "break_even_cvr" in c9:
        be = np.full(len(df), float(c9["break_even_cvr"]))
        be_src = "break_even_cvr"
    elif "target_cpa" in c9 and "cost" in df.columns:
        cpc = np.where(n > 0, df.cost.to_numpy(float) / np.maximum(n, 1), np.nan)
        be, be_src = cpc / float(c9["target_cpa"]), "cpc / target_cpa"
    else:
        raise ValueError("S09 needs s09.break_even_cvr, or s09.target_cpa plus a cost column")
    a0, b0, prior_method = fit_prior(x, n, c9["min_entities_for_prior"])
    rows = []
    for i, ent in enumerate(df.entity.astype(str)):
        post = stats.beta(a0 + x[i], b0 + n[i] - x[i])
        p_above = float(post.sf(be[i])) if np.isfinite(be[i]) else None
        verdict = ("unknown" if p_above is None else "likely_above" if p_above >= c9["decide_high"]
                   else "likely_below" if p_above <= c9["decide_low"] else "undecided")
        rows.append({"entity": ent, "clicks": int(n[i]), "conversions": int(x[i]),
                     "posterior_mean": float(post.mean()),
                     "ci": [float(post.ppf(a / 2)), float(post.ppf(1 - a / 2))],
                     "break_even_cvr": None if not np.isfinite(be[i]) else float(be[i]),
                     "p_cvr_at_or_above_break_even": p_above, "verdict": verdict})
    warn = []
    if prior_method == "weak_pooled":
        warn.append(f"fewer than {c9['min_entities_for_prior']} entities with clicks; prior is weak")
    if n.sum() == 0:
        validity = "insufficient"
        warn.insert(0, "no clicks in input")
    elif prior_method == "weak_pooled" or x.sum() < 5:
        validity = "low_power"
        if x.sum() < 5:
            warn.insert(0, f"only {int(x.sum())} conversions across all entities")
    else:
        validity = "valid"
    return result("S09", n=int(n.sum()), estimate={"prior_alpha": a0, "prior_beta": b0,
                  "entities": rows}, ci=None, method=f"beta-binomial EB ({prior_method})",
                  assumptions_checked=["entities exchangeable within the input",
                                       f"break-even from {be_src}"],
                  warnings=warn, validity=validity, inp_hash=h, seed=cfg["seed"])
