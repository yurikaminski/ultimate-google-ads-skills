"""S01: confidence intervals. Wilson (rates), exact Poisson (counts), bootstrap (ratios)."""
from __future__ import annotations

import numpy as np
from scipy import stats


def wilson(k: float, n: float, alpha: float = 0.10) -> tuple[float, float]:
    if n <= 0:
        return (0.0, 1.0)
    z = stats.norm.ppf(1 - alpha / 2)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def poisson_rate(count: float, exposure: float = 1.0, alpha: float = 0.10) -> tuple[float, float]:
    """Exact (Garwood) CI for a Poisson rate = count / exposure."""
    lo = 0.0 if count == 0 else stats.chi2.ppf(alpha / 2, 2 * count) / 2
    hi = stats.chi2.ppf(1 - alpha / 2, 2 * count + 2) / 2
    return (lo / exposure, hi / exposure)


def bootstrap_ratio(num, den, alpha: float = 0.10, iters: int = 2000, seed: int = 0):
    """Percentile bootstrap CI for sum(num)/sum(den), resampling rows."""
    num, den = np.asarray(num, float), np.asarray(den, float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(num), size=(iters, len(num)))
    with np.errstate(divide="ignore", invalid="ignore"):
        ratios = num[idx].sum(1) / den[idx].sum(1)
    ratios = ratios[np.isfinite(ratios)]
    return (float(np.quantile(ratios, alpha / 2)), float(np.quantile(ratios, 1 - alpha / 2)))


def run(df, cfg, h):
    from .core import result
    a = cfg["alpha"]
    if {"successes", "trials"} <= set(df.columns):
        k, n = float(df.successes.sum()), float(df.trials.sum())
        ci, est, method = wilson(k, n, a), (k / n if n else None), "wilson"
        validity = "insufficient" if n == 0 else ("low_power" if k < 5 or n - k < 5 else "valid")
        warn = [] if validity == "valid" else [f"only {int(k)} successes in {int(n)} trials"]
        nobs = int(n)
    elif {"count", "exposure"} <= set(df.columns) or "count" in df.columns:
        c = float(df["count"].sum())
        e = float(df["exposure"].sum()) if "exposure" in df.columns else float(len(df))
        ci, est, method = poisson_rate(c, e, a), c / e, "poisson_exact"
        validity = "low_power" if c < 10 else "valid"
        warn = [] if validity == "valid" else [f"only {int(c)} events observed"]
        nobs = int(c)
    elif {"num", "den"} <= set(df.columns):
        est = float(df.num.sum() / df.den.sum())
        ci = bootstrap_ratio(df.num, df.den, a, cfg["bootstrap_iterations"], cfg["seed"])
        method, nobs = "bootstrap_percentile", len(df)
        validity = "low_power" if len(df) < 20 else "valid"
        warn = [] if validity == "valid" else [f"only {len(df)} rows to resample"]
    else:
        raise ValueError("S01 needs columns successes,trials or count[,exposure] or num,den")
    return result("S01", n=nobs, estimate=est, ci=list(ci), method=method,
                  assumptions_checked=["independent trials/events"], warnings=warn,
                  validity=validity, inp_hash=h, seed=cfg["seed"])
