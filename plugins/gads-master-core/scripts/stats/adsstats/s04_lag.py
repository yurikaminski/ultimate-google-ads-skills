"""S04: conversion lag distribution, maturity cutoff, nowcasting."""
from __future__ import annotations

import numpy as np

from .core import result


def maturity_cutoff(lags: np.ndarray, coverage: float) -> float:
    return float(np.quantile(lags, coverage, method="higher"))


def run(df, cfg, h):
    if "lag_days" not in df.columns:
        raise ValueError("S04 needs a lag_days column (one row per conversion, optional weight)")
    lags = df.lag_days.to_numpy(float)
    if "weight" in df.columns:
        lags = np.repeat(lags, df.weight.round().astype(int).clip(lower=0))
    lags = lags[np.isfinite(lags) & (lags >= 0)]
    n, cov, a = len(lags), cfg["lag_coverage"], cfg["alpha"]
    if n == 0:
        return result("S04", n=0, estimate=None, ci=None, method="empirical_cdf",
                      assumptions_checked=[], warnings=["no conversion lag data"],
                      validity="insufficient", inp_hash=h, seed=cfg["seed"])
    cut = maturity_cutoff(lags, cov)
    rng = np.random.default_rng(cfg["seed"])
    boots = [maturity_cutoff(rng.choice(lags, n), cov) for _ in range(cfg["bootstrap_iterations"] // 4)]
    ci = [float(np.quantile(boots, a / 2)), float(np.quantile(boots, 1 - a / 2))]
    q = {f"p{int(p*100)}": float(np.quantile(lags, p)) for p in (0.5, 0.75, 0.9, 0.95)}
    nowcasts = []
    for c in cfg.get("nowcast", []) or []:
        age, obs = float(c["cohort_age_days"]), float(c["observed"])
        f = float((lags <= age).mean())
        fb = [float((rng.choice(lags, n) <= age).mean()) for _ in range(200)]
        nowcasts.append({
            "cohort": c.get("cohort"), "cohort_age_days": age, "observed": obs,
            "share_matured": f,
            "expected_final": obs / f if f > 0 else None,
            "ci": [obs / max(np.quantile(fb, 1 - a / 2), 1e-9), obs / max(np.quantile(fb, a / 2), 1e-9)]
                  if f > 0 else None,
        })
    validity = "valid" if n >= 30 else ("low_power" if n >= 5 else "insufficient")
    warn = [] if validity == "valid" else [f"only {n} conversions with known lag"]
    return result("S04", n=n, estimate={"maturity_cutoff_days": cut, "coverage": cov, **q},
                  ci=ci, method="empirical_cdf + bootstrap", warnings=warn, validity=validity,
                  assumptions_checked=["lag distribution stable over the window"], inp_hash=h,
                  seed=cfg["seed"], details={"nowcast": nowcasts})
