"""run.py diagnose: TOC Constraint Brief from a weekly funnel CSV (+ optional export, lag data, signals).

Every number in the brief is formatted from a stats-result and cites its id. Nothing is applied.
"""
from __future__ import annotations

import argparse
import json
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import yaml

from adsstats.__main__ import run_analysis
from adsstats.core import input_hash, load_cfg, warn_first
from common.schema import validate
from common.state import account_dir
from diagnose import controls as K
from memory import context as C
from memory import ledger as L

PLAYBOOKS = Path(__file__).resolve().parents[2] / "references" / "business-model-playbooks"


def _fmt(x, nd=1):
    return "n/a" if x is None else (f"{x:.{nd}f}" if abs(x) < 1000 else f"{x:,.0f}")


def _pct(x):
    return "n/a" if x is None else f"{x:.2%}"


def _stats(aid, df, cfg, ref):
    return run_analysis(aid, df, cfg, input_hash({"ref": ref, "data": df.to_dict("list"), "cfg": cfg}))


def build(ws: str, acct: str, funnel: str, playbook: str, signals: str | None = None,
          export: str | None = None, lag_file: str | None = None, as_of: str | None = None) -> dict:
    as_of_d = date.fromisoformat(as_of) if as_of else date.today()
    chain_p = PLAYBOOKS / f"{playbook}.chain.yaml"
    prof = C.profile_get(ws, acct)
    try:
        ctx = C.load(ws, acct)[0]
    except FileNotFoundError:
        ctx = None
    base = {"schema": "constraint-brief.v1", "account_id": acct,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "playbook": playbook,
            "gate0": [], "constraint": None, "runner_up": None, "exploit": [], "subordinate": [],
            "parking_lot": [], "elevate": [], "stats_ids": [], "falsifier": None, "disambiguating_test": None,
            "instruments": [], "owner_hypothesis": None, "next_review": (as_of_d + timedelta(days=7)).isoformat()}
    if not chain_p.exists():
        return {**base, "status": "unknown", "warn_first": f"Playbook '{playbook}' has no chain in v0.1 (scaffold only): no TOC verdict.",
                "parking_lot": [f"playbook {playbook}: chain not written yet (v0.3)"]}, [], []
    chain = yaml.safe_load(chain_p.read_text())
    T = (prof.get("targets") or {}).get("throughput")
    if not T:
        return {**base, "status": "unknown",
                "warn_first": "No target throughput (T*) in profile: S16 cannot run. Ask Q02 (target per week for the real result).",
                "parking_lot": ["T* missing: set with profile set --key targets.throughput"]}, [], []

    risk = prof.get("risk") or {}
    results, ref_f = [], f"file:{Path(funnel).name}"
    s15 = None
    if export:
        cfg15 = load_cfg(overrides={"as_of": as_of_d.isoformat(), "s15": {"required": ["date"]}})
        s15 = _stats("S15", pd.read_csv(export), cfg15, export)
        results.append(s15)
    lag = prof.get("lag_days")
    s04 = None
    if lag_file:
        s04 = _stats("S04", pd.read_csv(lag_file), load_cfg(), lag_file)
        results.append(s04)
        if s04["estimate"]:
            lag = s04["estimate"]["maturity_cutoff_days"]
    sig = json.loads(Path(signals).read_text()) if signals else {}
    stages = [s["id"] for s in chain["stages"]]
    effort = {s["id"]: s["effort"] for s in chain["stages"]} | (prof.get("effort") or {})
    cfg16 = load_cfg(overrides={"stages": stages, "target_throughput": float(T),
                                "target_rates": (prof.get("targets") or {}).get("rates") or {},
                                "lag_days": lag or 0, "as_of": as_of_d.isoformat(),
                                "operational_signals": sig, "effort": effort,
                                "alpha": risk.get("alpha", 0.10), "min_periods": risk.get("min_periods", 4)})
    fdf = pd.read_csv(funnel)
    s16 = _stats("S16", fdf, cfg16, funnel)
    results.append(s16)
    if lag is None:
        s16["warnings"].append("lag unknown: all periods treated as mature (set lag_days or pass --lag-file)")

    est, sid = s16["estimate"], s16["id"]
    c, ru = est["constraint"], est["runner_up"]
    rows = {r["stage"]: r for r in est["stages"]}
    stage_cfg = {s["id"]: s for s in chain["stages"]}

    # Gate 0 and TOC controls
    exp_ref = f"file:{Path(export).name}" if export else None
    gate0 = [K.g0_conversion_signal(s15, exp_ref), K.g0_data_quality(s15, exp_ref),
             K.g0_funnel_plausible(s16, ref_f), K.g0_maturity(s16, ref_f)]
    link = c["link"] if c else None
    blocking = L.freeze_check(ws, acct, link=link)["blocking"] if link else []
    hyp = ((ctx or {}).get("fields", {}).get("owner_hypothesis_constraint") or {}).get("value") if ctx else None
    toc = [K.toc_constraint(s16, ref_f, bool(c and c.get("boundary_inconclusive"))),
           K.toc_owner_hypothesis(hyp, s16, ref_f), K.toc_flipflops(L.flipflops(ws, acct)),
           K.toc_freeze(blocking, link)]
    findings = gate0 + toc
    blockers = [f for f in gate0 if f["status"] == "fail" and f["control_id"] in ("G0-01", "G0-02", "G0-03")]

    brief = {**base, "gate0": gate0, "stats_ids": [r["id"] for r in results], "warn_first": warn_first(results)}
    window = int((lag or 0) + 14)
    brief["next_review"] = (as_of_d + timedelta(days=window)).isoformat()

    if c is None:
        brief["status"] = "blocked_gate0" if blockers else ("no_constraint_at_target" if s16["validity"] == "valid" else "unknown")
        brief["elevate"] = [{"option": "Throughput meets T* on every link: raise T* or elevate the cheapest link", "gated": True}]
    else:
        st = stage_cfg[link.split("->")[-1]]
        row = rows[st["id"]]
        evidence = [f"{row['stage']}: {_fmt(row['mean_per_period'])}/week (CI {_fmt(row['ci'][0])} to {_fmt(row['ci'][1])}) "
                    f"vs required {_fmt(row['required_per_period'])}/week, status {row['status']} [{sid}]"]
        if c["kind"] == "conversion":
            evidence.append(f"rate into {row['stage']}: {_pct(row['rate'])} (CI {_pct(row['rate_ci'][0])} to {_pct(row['rate_ci'][1])}) "
                            f"vs target {_pct(row['target_rate'])} ({row['target_rate_source']}) [{sid}]")
        if c.get("operational_signal"):
            evidence.append(f"operational: {c['operational_signal']} (reported)")
        brief["constraint"] = {"link": link, "kind": c["kind"], "toc_link": st["toc_link"], "evidence": evidence,
                               "confidence": c["confidence"], "stats_ids": [sid]}
        if ru:
            brief["runner_up"] = {"link": ru["link"], "kind": ru["kind"], "reason": ru.get("reason", "next by delta T per effort"),
                                  "stats_ids": [sid]}
        brief["falsifier"] = (
            f"If the rate into {row['stage']} reaches {_pct(row['target_rate'])} for {window} days and "
            f"{stages[-1]} is still below T* {_fmt(T)}/week, the constraint is downstream." if c["kind"] == "conversion" else
            f"If lost impression share (budget and rank) on profitable terms is near zero while {stages[0]} stays below "
            f"{_fmt(row['required_per_period'])}/week, the limit is demand, not budget or rank.")
        if c.get("boundary_inconclusive"):
            brief["disambiguating_test"] = (f"Boundary is inconclusive: collect {window} more days or run the cheapest test on "
                                            f"{link} (instrument: {st['instruments'][0]}) before committing budget.")
        brief["instruments"] = st["instruments"]
        brief["subordinate"] = st["subordinate"]
        brief["elevate"] = [{"option": o, "gated": True} for o in st["elevate"]]
        if blocking:
            brief["exploit"] = [{"action": f"FROZEN: {b['id']} is measuring on this link until {b['window']['end']}. No new change.",
                                 "expected_delta": None, "stats_ids": [sid], "window_days": 0, "rollback": "none needed"}
                                for b in blocking[:1]]
        else:
            delta = c.get("delta_T")
            for i, a in enumerate(st["exploit"][:3]):
                brief["exploit"].append({
                    "action": a,
                    "expected_delta": ({"metric": f"{stages[-1]} per week if {link} reaches target (upper bound, all actions combined)",
                                        "value": round(delta, 2), "evidence_type": "estimated"} if (i == 0 and delta is not None) else None),
                    "stats_ids": [sid], "window_days": window,
                    "rollback": "Revert to the pre-change state recorded in the change draft; nothing is applied by diagnose."})
        brief["status"] = "blocked_gate0" if blockers else "constraint_found"
        if hyp:
            brief["owner_hypothesis"] = {"hypothesis": hyp, "matches": toc[1]["status"] == "pass"}

    parking = []
    for r in est["stages"]:
        if c and r["stage"] == link.split("->")[-1]:
            continue
        if r["status"] in ("starvation", "inconclusive"):
            parking.append(f"{r['stage']}: {r['status']} (downstream of or secondary to the constraint, not analyzed) [{sid}]")
    if s15:
        parking += [f"data warning: {c_['check']}" for c_ in s15["estimate"]["checks"]
                    if c_["status"] == "fail" and c_["severity"] == "warning"]
    for p_ in L.events(ws, acct, "parking")[-5:]:
        parking.append(f"resurfaced: {p_['item']}"[:160])
    brief["parking_lot"] = [p[:160] for p in dict.fromkeys(parking)]
    if blockers:
        brief["parking_lot"].insert(0, "GATE 0 BLOCKER: fix measurement before acting on the constraint")
    validate("constraint-brief.v1", brief)
    for f in findings:
        validate("finding.v1", f)
    return brief, results, findings


def render(brief: dict) -> str:
    lines = []
    if brief.get("warn_first"):
        lines.append(brief["warn_first"])
    lines.append(f"# Constraint Brief: {brief['account_id']} ({brief['playbook']}), status {brief['status']}")
    g0 = [f for f in brief["gate0"] if f["status"] == "fail"]
    if g0:
        lines.append("\n## Gate 0 blockers")
        lines += [f"- {f['control_id']}: {f['observation']} [{', '.join(f['stats_ids'])}]" for f in g0]
    c = brief["constraint"]
    if c:
        lines.append(f"\n## Constraint: {c['link']} ({c['kind']}, {c['toc_link']}), confidence {c['confidence']}")
        lines += [f"- {e}" for e in c["evidence"]]
        if brief["runner_up"]:
            lines.append(f"- Runner-up: {brief['runner_up']['link']} ({brief['runner_up']['reason']})")
        lines.append(f"- Would falsify it: {brief['falsifier']}")
        if brief.get("disambiguating_test"):
            lines.append(f"- Test first: {brief['disambiguating_test']}")
        if brief.get("owner_hypothesis"):
            h = brief["owner_hypothesis"]
            lines.append(f"- Owner hypothesis ({'matches' if h['matches'] else 'does not match'}): kept as hypothesis, not evidence")
        lines.append("\n## Exploit (max 3, zero new spend)")
        for i, a in enumerate(brief["exploit"], 1):
            d = a["expected_delta"]
            dtxt = f" Expected: +{d['value']} {d['metric']} ({d['evidence_type']}) [{', '.join(a['stats_ids'])}]." if d else ""
            lines.append(f"{i}. {a['action']}{dtxt} Window {a['window_days']}d. Rollback: {a['rollback']}")
        lines.append("\n## Subordinate (do NOT do now)")
        lines += [f"- {s}" for s in brief["subordinate"]]
        lines.append("\n## Elevate (gated: needs approval and budget)")
        lines += [f"- {e['option']}" for e in brief["elevate"]]
    if brief["parking_lot"]:
        lines.append("\n## Parking lot (listed, not analyzed)")
        lines += [f"- {p}" for p in brief["parking_lot"]]
    lines.append(f"\nNext review: {brief['next_review']}. Stats: {', '.join(brief['stats_ids']) or 'none'}")
    return "\n".join(lines)


def commit(ws: str, acct: str, brief: dict, results: list, findings: list, inputs: list[str]) -> str:
    """End-of-diagnose event: constraint-history, parking-lot, baselines (on constraint move), run bundle."""
    hist = L.events(ws, acct, "constraint")
    prev = hist[-1]["link"] if hist else None
    link = (brief["constraint"] or {}).get("link")
    L.append(ws, acct, "constraint", {"id": f"C-{uuid.uuid4().hex[:8]}", "link": link, "status": brief["status"],
                                      "confidence": (brief["constraint"] or {}).get("confidence"),
                                      "stats_ids": brief["stats_ids"], "moved_from": prev if prev != link else None})
    for p in brief["parking_lot"]:
        if not p.startswith("resurfaced:"):
            L.append(ws, acct, "parking", {"item": p})
    d = account_dir(ws, acct)
    s16 = next((r for r in results if r["analysis"] == "S16"), None)
    if s16 and (prev != link or not (d / "baselines.json").exists()):
        (d / "baselines.json").write_text(json.dumps({
            "set_at": brief["created_at"], "reason": "constraint moved" if prev and prev != link else "first baseline",
            "stats_id": s16["id"], "stages": {r["stage"]: {"mean_per_period": r["mean_per_period"], "rate": r.get("rate")}
                                              for r in s16["estimate"]["stages"]}}, indent=2, default=float))
    run_id = f"R-{datetime.now(timezone.utc):%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:4]}"
    bundle = {"schema": "run-bundle.v1", "run_id": run_id, "account_id": acct, "mode": "diagnose",
              "created_at": brief["created_at"],
              "inputs": [{"path": p, "sha256": input_hash(p)} for p in inputs if p],
              "stats_results": results, "findings": findings, "output": brief}
    validate("run-bundle.v1", json.loads(json.dumps(bundle, default=float)))
    (d / "runs" / f"{run_id}.json").write_text(json.dumps(bundle, indent=2, default=float))
    return run_id


def main(argv) -> int:
    p = argparse.ArgumentParser(prog="run.py diagnose")
    p.add_argument("--workspace", default="."); p.add_argument("--account", required=True)
    p.add_argument("--funnel", required=True); p.add_argument("--playbook", required=True)
    p.add_argument("--signals"); p.add_argument("--export"); p.add_argument("--lag-file")
    p.add_argument("--as-of"); p.add_argument("--out"); p.add_argument("--commit", action="store_true")
    a = p.parse_args(argv)
    brief, results, findings = build(a.workspace, a.account, a.funnel, a.playbook, a.signals, a.export, a.lag_file, a.as_of)
    out = {"brief": brief, "markdown": render(brief)}
    if a.commit and results:
        out["run_id"] = commit(a.workspace, a.account, brief, results, findings, [a.funnel, a.export, a.lag_file])
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=2, default=float))
    print(json.dumps(out, indent=2, default=float))
    return 0
