import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts" / "stats"), str(ROOT / "scripts")]
PLAYBOOKS = ROOT / "references" / "business-model-playbooks"


def chain(name):
    return yaml.safe_load((PLAYBOOKS / f"{name}.chain.yaml").read_text())


def planted_funnel(stages, targets, plant=None, plant_factor=0.5, second=None, second_factor=0.75,
                   top_ratio=1.4, weeks=16, base_top=None, seed=0):
    """Synthetic weekly funnel. targets[k] = r* into stage k (k>=1).

    plant: stage index whose inflow rate (or top volume when 0) is cut by plant_factor.
    Returns (df, cfg) with T* chosen so that the unplanted funnel is comfortably ok.
    """
    rng = np.random.default_rng(seed)
    K = len(stages)
    prod = float(np.prod([targets[k] for k in range(1, K)]))
    T = 60.0  # target final-stage throughput per week
    v0_req = T / prod
    v0 = v0_req * top_ratio * (plant_factor if plant == 0 else 1.0)
    rates = [None] + [targets[k] for k in range(1, K)]
    if plant:
        rates[plant] *= plant_factor
    if second:
        rates[second] *= second_factor
    rows = []
    for w in range(weeks):
        v = rng.poisson(v0)
        row = {"period": str(pd.Timestamp("2026-01-05") + pd.Timedelta(weeks=w))[:10], stages[0]: v}
        for k in range(1, K):
            v = rng.binomial(v, min(rates[k], 1.0))
            row[stages[k]] = v
        row["cohort_age_days"] = 200
        rows.append(row)
    cfg = {"stages": stages, "target_throughput": T,
           "target_rates": {stages[k]: targets[k] for k in range(1, K)}, "lag_days": 30}
    return pd.DataFrame(rows), cfg
