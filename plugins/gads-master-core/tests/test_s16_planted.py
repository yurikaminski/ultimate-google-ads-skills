"""Planted-constraint fixtures: one synthetic account per chain link, per business model."""
import pytest
from adsstats import s16_constraint
from adsstats.core import load_cfg
from conftest import chain, planted_funnel

TARGETS = {
    "saas": [None, 0.05, 0.08, 0.40, 0.40, 0.30],
    "ecommerce": [None, 0.02, 0.92, 0.10, 0.50, 0.60],
}
CASES = [(m, k) for m in TARGETS for k in range(len(TARGETS[m]))]


def _run(model, plant, second=None, **kw):
    ch = chain(model)
    stages = [s["id"] for s in ch["stages"]]
    df, c = planted_funnel(stages, TARGETS[model], plant=plant, second=second, **kw)
    cfg = load_cfg(overrides={**c, "effort": {s["id"]: s["effort"] for s in ch["stages"]}})
    return s16_constraint.analyze(df, cfg), stages


@pytest.mark.parametrize("model,plant", CASES)
def test_finds_planted_constraint_and_runner_up(model, plant):
    K = len(TARGETS[model])
    if plant < K - 1:  # second weakness downstream of the plant: it starves too, but later
        second, factor = min(plant + 2, K - 1), 0.6
    else:  # plant is the last link: a milder upstream weakness that is not (yet) starving
        second, factor = 1, 0.85
    out, stages = _run(model, plant, second=second, second_factor=factor, seed=plant + 10)
    c = out["constraint"]
    assert c is not None
    assert c["index"] == plant, (stages[plant], c)
    assert c["kind"] == ("volume" if plant == 0 else "conversion")
    assert out["runner_up"] is not None and out["runner_up"]["index"] == second
    assert c["confidence"] in ("medium", "high")


def test_operational_signal_raises_confidence_to_high():
    ch = chain("saas")
    stages = [s["id"] for s in ch["stages"]]
    df, c = planted_funnel(stages, TARGETS["saas"], plant=2, seed=3)
    cfg = load_cfg(overrides={**c, "operational_signals": {"signups_or_leads": {
        "supports_constraint": True, "signal": "spend on terms with CVR under target"}}})
    assert s16_constraint.analyze(df, cfg)["constraint"]["confidence"] == "high"


def test_healthy_funnel_has_no_confident_constraint():
    for seed in range(5):
        out, _ = _run("saas", plant=None, seed=seed, top_ratio=1.6)
        c = out["constraint"]
        assert c is None or c["confidence"] == "low"


def test_immature_periods_excluded_and_warned():
    ch = chain("saas")
    stages = [s["id"] for s in ch["stages"]]
    df, c = planted_funnel(stages, TARGETS["saas"], plant=3, weeks=6, seed=1)
    df.loc[3:, "cohort_age_days"] = 5
    out = s16_constraint.analyze(df, load_cfg(overrides=c))
    assert out["n"] == 3 and out["validity"] == "low_power"
    assert out["constraint"] is None or out["constraint"]["confidence"] == "low"
    assert any("immature" in w for w in out["warnings"])
