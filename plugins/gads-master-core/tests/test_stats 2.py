import numpy as np
import pandas as pd
import pytest
from adsstats import s01_ci, s04_lag, s09_shrinkage, s15_quality
from adsstats.__main__ import run_analysis
from adsstats.core import load_cfg, warn_first

ALPHA = 0.10


def test_wilson_coverage():
    rng = np.random.default_rng(1)
    p, n, sims = 0.05, 200, 3000
    hits = sum(lo <= p <= hi for lo, hi in (s01_ci.wilson(k, n, ALPHA) for k in rng.binomial(n, p, sims)))
    assert 0.86 <= hits / sims <= 0.95


def test_poisson_coverage_is_conservative():
    rng = np.random.default_rng(2)
    mu, sims = 4.0, 3000
    hits = sum(lo <= mu <= hi for lo, hi in (s01_ci.poisson_rate(c, 1, ALPHA) for c in rng.poisson(mu, sims)))
    assert hits / sims >= 0.89


def test_bootstrap_ratio_brackets_truth():
    rng = np.random.default_rng(3)
    den = rng.integers(50, 150, 60)
    num = rng.binomial(den, 0.1)
    lo, hi = s01_ci.bootstrap_ratio(num, den, ALPHA, 1000, 0)
    assert lo < 0.1 < hi


def test_s04_recovers_quantile():
    rng = np.random.default_rng(4)
    df = pd.DataFrame({"lag_days": rng.exponential(10, 2000)})
    cfg = load_cfg(overrides={"nowcast": [{"cohort_age_days": 7, "observed": 50}]})
    r = s04_lag.run(df, cfg, "x" * 12)
    true_p90 = -10 * np.log(0.1)
    assert abs(r["estimate"]["maturity_cutoff_days"] - true_p90) / true_p90 < 0.1
    nc = r["details"]["nowcast"][0]
    assert nc["expected_final"] > 50 and nc["ci"][0] <= nc["expected_final"] <= nc["ci"][1]
    assert r["validity"] == "valid"


def test_s04_low_data_warns():
    r = s04_lag.run(pd.DataFrame({"lag_days": [1, 3, 9]}), load_cfg(), "y" * 12)
    assert r["validity"] == "insufficient" or r["validity"] == "low_power"
    assert warn_first([r]).startswith("STATISTICAL VALIDITY WARNING")


def _s09_sim(true_cvr, be, clicks, n_ent, seed):
    rng = np.random.default_rng(seed)
    others = pd.DataFrame({"entity": [f"o{i}" for i in range(20)], "clicks": 300,
                           "conversions": rng.binomial(300, be * 1.5, 20)})
    test = pd.DataFrame({"entity": [f"t{i}" for i in range(n_ent)], "clicks": clicks,
                         "conversions": rng.binomial(clicks, true_cvr, n_ent)})
    cfg = load_cfg(overrides={"s09": {"break_even_cvr": be}})
    r = s09_shrinkage.run(pd.concat([others, test], ignore_index=True), cfg, "z" * 12)
    return [e["verdict"] for e in r["estimate"]["entities"] if e["entity"].startswith("t")]


def test_s09_type1_good_entities_rarely_flagged():
    v = _s09_sim(true_cvr=0.06, be=0.03, clicks=150, n_ent=200, seed=5)
    assert v.count("likely_below") / len(v) < 0.05


def test_s09_power_bad_entities_flagged():
    v = _s09_sim(true_cvr=0.005, be=0.03, clicks=400, n_ent=200, seed=6)
    assert v.count("likely_below") / len(v) > 0.7


def test_s09_zero_conversion_small_sample_is_not_condemned():
    v = _s09_sim(true_cvr=0.0, be=0.03, clicks=20, n_ent=50, seed=7)
    assert v.count("likely_below") / len(v) < 0.5  # 20 clicks and no conversion proves little


def test_s15_detects_planted_issues():
    df = pd.DataFrame({"date": ["2026-10-01", "2026-10-01", "2026-10-03", "2099-01-01"],
                       "campaign": ["a", "a", "b", "c"], "impressions": [100, 100, 5, 10],
                       "clicks": [10, 10, 9, 20], "conversions": [0, 0, 0, 0], "cost": [5, 5, -1, 3]})
    r = s15_quality.run(df, load_cfg(), "q" * 12)
    failed = {c["check"] for c in r["estimate"]["checks"] if c["status"] == "fail"}
    assert {"duplicate_keys", "clicks_le_impressions", "non_negative_cost", "date_gaps",
            "no_future_dates", "conversion_signal_present"} <= failed
    assert "conversion_signal_present" in r["estimate"]["gate0"]


def test_s15_drift(tmp_path):
    a = pd.DataFrame({"date": ["2026-10-01", "2026-10-02"], "clicks": [100, 100], "cost": [50.0, 50.0]})
    b = a.assign(cost=[50.0, 60.0])
    p = tmp_path / "b.csv"
    b.to_csv(p, index=False)
    cfg = load_cfg(overrides={"s15": {"compare_with": str(p)}})
    r = s15_quality.run(a, cfg, "d" * 12)
    st = {c["check"]: c["status"] for c in r["estimate"]["checks"]}
    assert st["drift_cost"] == "fail" and st["drift_clicks"] == "pass"


def test_result_contract_and_ids_are_deterministic():
    df = pd.DataFrame({"successes": [3], "trials": [40]})
    r1, r2 = run_analysis("S01", df, load_cfg()), run_analysis("S01", df, load_cfg())
    assert r1["id"] == r2["id"] and r1["id"].startswith("S01-")
    for k in ("id", "n", "estimate", "ci", "method", "assumptions_checked", "warnings", "validity", "status"):
        assert k in r1
    assert r1["validity"] == "low_power" and warn_first([r1]).startswith("STATISTICAL VALIDITY WARNING")
