"""S15: data quality. Plausibility, duplicates, gaps, drift between exports."""
from __future__ import annotations

import pandas as pd

from .core import result

METRICS = ("impressions", "clicks", "cost", "conversions", "conversion_value")


def _check(cid, ok, severity, msg, rows=None):
    return {"check": cid, "status": "pass" if ok else "fail", "severity": severity,
            "message": msg, "rows": rows or []}


def checks(df: pd.DataFrame, cfg: dict) -> list[dict]:
    c15 = cfg.get("s15", {})
    out = []
    req = c15.get("required", [])
    miss = [c for c in req if c not in df.columns]
    out.append(_check("required_columns", not miss, "blocker", f"missing columns: {miss}" if miss else "all present"))
    nulls = {c: int(df[c].isna().sum()) for c in df.columns if df[c].isna().any()}
    out.append(_check("nulls", not nulls, "warning", f"null cells: {nulls}" if nulls else "none"))
    for m in METRICS:
        if m in df.columns:
            neg = df.index[df[m] < 0].tolist()
            out.append(_check(f"non_negative_{m}", not neg, "blocker", f"{len(neg)} negative rows", neg[:20]))
    if {"clicks", "impressions"} <= set(df.columns):
        bad = df.index[df.clicks > df.impressions].tolist()
        out.append(_check("clicks_le_impressions", not bad, "blocker", f"{len(bad)} rows with clicks > impressions", bad[:20]))
    if {"conversions", "clicks"} <= set(df.columns):
        bad = df.index[df.conversions > df.clicks].tolist()
        out.append(_check("conversions_le_clicks", not bad, "warning",
                          f"{len(bad)} rows with conversions > clicks (possible view-through, multi-count or duplicate tags)", bad[:20]))
    key = [k for k in c15.get("key", ["date", "campaign"]) if k in df.columns]
    if key:
        dup = df.index[df.duplicated(key, keep=False)].tolist()
        out.append(_check("duplicate_keys", not dup, "blocker", f"{len(dup)} rows share key {key}", dup[:20]))
    if "date" in df.columns:
        d = pd.to_datetime(df["date"], errors="coerce")
        out.append(_check("parseable_dates", d.notna().all(), "blocker", f"{int(d.isna().sum())} unparseable dates"))
        d = d.dropna()
        if len(d):
            span = pd.date_range(d.min(), d.max(), freq="D")
            gaps = sorted(set(span.date) - set(d.dt.date))
            out.append(_check("date_gaps", not gaps, "warning", f"{len(gaps)} missing days", [str(g) for g in gaps[:20]]))
            fut = (d > pd.Timestamp(cfg.get("as_of") or pd.Timestamp.today().normalize())).sum()
            out.append(_check("no_future_dates", fut == 0, "blocker", f"{int(fut)} future-dated rows"))
    if "conversions" in df.columns and "clicks" in df.columns and len(df):
        dead = df.clicks.sum() > 0 and df.conversions.sum() == 0
        out.append(_check("conversion_signal_present", not dead, "blocker",
                          "clicks recorded but zero conversions in the whole window: tracking may be broken (Gate 0)" if dead else "conversions present"))
    return out


def drift(a: pd.DataFrame, b: pd.DataFrame, tol: float) -> list[dict]:
    if "date" not in a.columns or "date" not in b.columns:
        return []
    a, b = a.assign(date=pd.to_datetime(a.date)), b.assign(date=pd.to_datetime(b.date))
    common = sorted(set(a.date) & set(b.date))
    res = []
    for m in METRICS:
        if m in a.columns and m in b.columns and common:
            x, y = a[a.date.isin(common)][m].sum(), b[b.date.isin(common)][m].sum()
            rel = abs(x - y) / max(abs(x), abs(y), 1e-9)
            res.append(_check(f"drift_{m}", rel <= tol, "warning",
                              f"{m}: {x:.2f} vs {y:.2f} on {len(common)} overlapping days (rel diff {rel:.3%})"))
    return res


def run(df, cfg, h):
    res = checks(df, cfg)
    if cfg.get("s15", {}).get("compare_with"):
        res += drift(df, pd.read_csv(cfg["s15"]["compare_with"]), cfg["s15"]["drift_tolerance"])
    blockers = [c for c in res if c["status"] == "fail" and c["severity"] == "blocker"]
    warns = [c["message"] for c in res if c["status"] == "fail"]
    validity = "insufficient" if len(df) == 0 else "valid"
    if not len(df):
        warns.insert(0, "empty input")
    return result("S15", n=len(df), estimate={"checks": res, "blockers": len(blockers),
                  "gate0": [c["check"] for c in blockers]}, ci=None, method="rule checks",
                  assumptions_checked=["rows are one grain (no mixed aggregation levels)"],
                  warnings=warns, validity=validity, inp_hash=h, seed=cfg["seed"])
