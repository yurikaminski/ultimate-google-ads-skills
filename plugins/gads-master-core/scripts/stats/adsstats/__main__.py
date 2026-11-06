"""CLI: python -m adsstats <ID> --in data.csv --cfg stats-config.yaml --out result.json"""
from __future__ import annotations

import argparse
import json
import sys

import pandas as pd

from . import s01_ci, s04_lag, s09_shrinkage, s15_quality, s16_constraint
from .core import input_hash, load_cfg, warn_first

ANALYSES = {"S01": s01_ci.run, "S04": s04_lag.run, "S09": s09_shrinkage.run,
            "S15": s15_quality.run, "S16": s16_constraint.run}
PLANNED = {f"S{i:02d}" for i in range(1, 17)} - set(ANALYSES)


def run_analysis(aid: str, df: pd.DataFrame, cfg: dict, h: str | None = None) -> dict:
    return ANALYSES[aid](df, cfg, h or input_hash(df.to_dict("list") | {"_cfg": cfg}))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="adsstats")
    p.add_argument("id", help="analysis id, e.g. S16")
    p.add_argument("--in", dest="inp", required=True)
    p.add_argument("--cfg")
    p.add_argument("--set", action="append", default=[], help="override, e.g. s09.target_cpa=80 (YAML value)")
    p.add_argument("--out")
    a = p.parse_args(argv)
    aid = a.id.upper()
    if aid in PLANNED:
        print(json.dumps({"error": f"{aid} is planned for v0.3 and not implemented"}), file=sys.stderr)
        return 3
    if aid not in ANALYSES:
        print(json.dumps({"error": f"unknown analysis {aid}"}), file=sys.stderr)
        return 2
    import yaml
    ov = {}
    for s in a.set:
        key, val = s.split("=", 1)
        cur = ov
        *parents, leaf = key.split(".")
        for k in parents:
            cur = cur.setdefault(k, {})
        cur[leaf] = yaml.safe_load(val)
    cfg = load_cfg(a.cfg, ov)
    df = pd.read_csv(a.inp)
    res = run_analysis(aid, df, cfg, input_hash({"data": input_hash(a.inp), "cfg": cfg}))
    res["warn_first"] = warn_first([res])
    text = json.dumps(res, indent=2, default=float)
    if a.out:
        open(a.out, "w").write(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
