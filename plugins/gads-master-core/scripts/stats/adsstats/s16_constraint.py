"""S16: queue/starvation boundary test (TOC constraint finder).

Input: one row per period (week) with one column per chain stage, in chain order.
Optional column cohort_age_days (age of the period END on the analysis date).

For each stage k:
  r*_k  target conversion rate from stage k-1 into k (owner > self-benchmark P75 > unknown)
  V*_k  required volume per period = T* / prod_{j>k} r*_j
  status from the exact Poisson CI of mean volume per mature period:
    starvation (upper < V*), ok (lower > V*), inconclusive (CI crosses V*), unknown.
Constraint = first starving stage going downstream. If its predecessor is ok, the link
(k-1 -> k) conversion is the constraint; if it is the top stage, the constraint is volume.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .core import result
from .s01_ci import poisson_rate, wilson


def _mature(df: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, int]:
    lag = float(cfg.get("lag_days") or 0)
    if "cohort_age_days" in df.columns:
        keep = df[df.cohort_age_days >= lag]
    elif "period" in df.columns and cfg.get("as_of"):
        end = pd.to_datetime(df.period) + pd.Timedelta(days=int(cfg.get("period_days", 7)))
        age = (pd.Timestamp(cfg["as_of"]) - end).dt.days
        keep = df[age >= lag]
    else:
        keep = df
    return keep, len(df) - len(keep)


def _targets(m: pd.DataFrame, stages: list[str], cfg: dict) -> dict:
    owner = cfg.get("target_rates") or {}
    out = {}
    for k in range(1, len(stages)):
        s, prev = stages[k], stages[k - 1]
        if owner.get(s) is not None:
            out[s] = (float(owner[s]), "owner")
            continue
        ok = m[m[prev] > 0]
        if len(ok) >= 2:
            out[s] = (float(np.quantile(ok[s] / ok[prev], 0.75)), "self_benchmark_p75")
        else:
            out[s] = (None, "unknown")
    return out


def analyze(df: pd.DataFrame, cfg: dict) -> dict:
    stages: list[str] = cfg["stages"]
    missing = [s for s in stages if s not in df.columns]
    if missing:
        raise ValueError(f"S16: funnel is missing stage columns {missing}")
    a, T = cfg["alpha"], float(cfg["target_throughput"])
    m, dropped = _mature(df, cfg)
    n = len(m)
    rstar = _targets(m, stages, cfg)

    rows = []
    for k, s in enumerate(stages):
        downstream = [rstar[stages[j]][0] for j in range(k + 1, len(stages))]
        vstar = None if any(r is None or r <= 0 for r in downstream) else T / float(np.prod(downstream) if downstream else 1.0)
        total = float(m[s].sum()) if n else 0.0
        mean = total / n if n else None
        ci = list(poisson_rate(total, n, a)) if n else None
        if n == 0 or vstar is None:
            status = "unknown"
        elif ci[1] < vstar:
            status = "starvation"
        elif ci[0] > vstar:
            status = "ok"
        else:
            status = "inconclusive"
        row = {"stage": s, "mean_per_period": mean, "ci": ci, "required_per_period": vstar, "status": status}
        if k > 0:
            prev_total = float(m[stages[k - 1]].sum()) if n else 0.0
            rate = total / prev_total if prev_total else None
            rci = list(wilson(min(total, prev_total), prev_total, a)) if prev_total else None
            r, src = rstar[s]
            row.update({"rate": rate, "rate_ci": rci, "target_rate": r, "target_rate_source": src,
                        "rate_below_target": None if (rci is None or r is None) else bool(rci[1] < r)})
        rows.append(row)

    # Estimated throughput gain if each non-ok element reached target (delta T per period).
    T_now = rows[-1]["mean_per_period"] or 0.0
    effort = cfg.get("effort") or {}
    cands = []
    for k, row in enumerate(rows):
        if row["status"] in ("ok", "unknown"):
            continue
        if k == 0:
            v = row["mean_per_period"] or 0
            gain = T_now * (row["required_per_period"] / v - 1) if v else None
            kind, link = "volume", row["stage"]
        else:
            r, rt = row.get("rate"), row.get("target_rate")
            gain = T_now * (rt / r - 1) if (r and rt and rt > r) else 0.0
            kind, link = "conversion", f"{rows[k-1]['stage']}->{row['stage']}"
        eff = float(effort.get(row["stage"], 3))
        cands.append({"index": k, "kind": kind, "link": link, "stage_status": row["status"],
                      "delta_T": gain, "effort": eff,
                      "score": (gain or 0) / eff})

    sig = cfg.get("operational_signals") or {}
    first = next((c for c in cands if c["stage_status"] == "starvation"), None)
    constraint, boundary = None, False
    if first is not None:
        constraint = first
        if first["index"] > 0 and rows[first["index"] - 1]["status"] == "inconclusive":
            boundary = True
    elif cands:  # only inconclusive stages: pick the best delta per effort, flag boundary
        constraint, boundary = max(cands, key=lambda c: c["score"]), True

    runner_up = None
    if constraint:
        others = [c for c in cands if c is not constraint]
        if others:
            runner_up = max(others, key=lambda c: c["score"])
        else:  # nothing else starving: the next constraint is the stage with the least headroom
            spare = [(r["mean_per_period"] / r["required_per_period"], k) for k, r in enumerate(rows)
                     if k != constraint["index"] and r["required_per_period"] and r["mean_per_period"] is not None]
            # Headroom propagates downstream, so prefer links whose own rate is below target (the origin).
            origin = [(h, k) for h, k in spare if k == 0 or rows[k].get("rate_below_target")]
            spare = origin or spare
            if spare:
                _, k = min(spare)
                runner_up = {"index": k, "kind": "volume" if k == 0 else "conversion",
                             "link": rows[k]["stage"] if k == 0 else f"{rows[k-1]['stage']}->{rows[k]['stage']}",
                             "stage_status": rows[k]["status"], "delta_T": None,
                             "reason": "nearest_to_starvation"}
        stage_row = rows[constraint["index"]]
        stat_ok = stage_row["status"] == "starvation" and (
            constraint["kind"] == "volume" or stage_row.get("rate_below_target") is True)
        op = sig.get(stage_row["stage"], {})
        op_ok = bool(op.get("supports_constraint"))
        if boundary or not (stat_ok or op_ok):
            conf = "low"
        elif stat_ok and op_ok:
            conf = "high"
        else:
            conf = "medium"
        constraint = {**constraint, "confidence": conf, "statistical_signal": stat_ok,
                      "operational_signal": op.get("signal") if op_ok else None,
                      "boundary_inconclusive": boundary}
        if constraint["kind"] == "volume":
            constraint["volume_cause_hints"] = {k: sig.get(k) for k in ("lost_is_budget", "lost_is_rank", "demand") if k in sig}

    min_p = int(cfg.get("min_periods", 4))
    warn = []
    if n == 0:
        validity = "insufficient"
        warn.append(f"no mature periods (all {dropped} periods younger than lag {cfg.get('lag_days')} days)")
    elif n < min_p:
        validity = "low_power"
        warn.append(f"only {n} mature periods (need >= {min_p})")
    else:
        validity = "valid"
    if dropped:
        warn.append(f"{dropped} immature periods excluded (age < lag {cfg.get('lag_days')} days)")
    if any(v[1] == "unknown" for v in rstar.values()):
        warn.append("some target rates unknown: set owner targets in profile")
    if constraint and constraint["confidence"] != "low" and validity != "valid":
        constraint["confidence"] = "low"
    return {"n": n, "rows": rows, "constraint": constraint, "runner_up": runner_up,
            "target_throughput": T, "current_throughput": T_now, "validity": validity,
            "warnings": warn, "dropped_immature": dropped}


def run(df, cfg, h):
    if cfg.get("period") == "day" and "date" in df.columns:
        d = df.assign(period=pd.to_datetime(df.date).dt.to_period("W-SUN").dt.start_time)
        full = d.groupby("period").size()
        d = d[d.period.isin(full[full == 7].index)]  # whole weeks only: removes day-of-week bias
        df = d.groupby("period", as_index=False)[cfg["stages"]].sum()
    out = analyze(df, cfg)
    est = {"constraint": out["constraint"], "runner_up": out["runner_up"], "stages": out["rows"],
           "target_throughput": out["target_throughput"], "current_throughput": out["current_throughput"]}
    return result("S16", n=out["n"], estimate=est, ci=None,
                  method="queue/starvation boundary: exact Poisson volume CI + Wilson rate CI",
                  assumptions_checked=["mature cohorts only (age >= lag)", "whole weeks (day-of-week neutral)",
                                       "stage counts are cohort-consistent"],
                  warnings=out["warnings"], validity=out["validity"], inp_hash=h, seed=cfg["seed"])
