"""Evaluators for v0.1 controls in references/controls-registry.json. Each returns a finding.v1."""
from __future__ import annotations

import json
from pathlib import Path

REGISTRY = Path(__file__).resolve().parents[2] / "references" / "controls-registry.json"


def registry() -> dict:
    return {c["id"]: c for c in json.loads(REGISTRY.read_text())["controls"]}


def _finding(cid, status, observation, refs, stats_ids, ev="observed", diagnosis=None, rec=None,
             confidence="high", indicative=False):
    return {"schema": "finding.v1", "id": f"F-{cid}", "control_id": cid, "status": status,
            "evidence_type": ev, "evidence_refs": refs, "stats_ids": stats_ids,
            "observation": observation, "diagnosis": diagnosis, "recommendation": rec,
            "confidence": confidence, "indicative": indicative}


def g0_conversion_signal(s15: dict | None, ref: str | None):
    if not s15:
        return _finding("G0-01", "unknown", "no account export supplied", [], [], confidence="low")
    c = next((c for c in s15["estimate"]["checks"] if c["check"] == "conversion_signal_present"), None)
    if not c:
        return _finding("G0-01", "unknown", "export has no clicks/conversions columns", [ref], [s15["id"]], confidence="low")
    return _finding("G0-01", c["status"], c["message"], [ref], [s15["id"]],
                    diagnosis="tracking likely broken" if c["status"] == "fail" else None,
                    rec="verify conversion actions and tags before any optimization" if c["status"] == "fail" else None)


def g0_data_quality(s15: dict | None, ref: str | None):
    if not s15:
        return _finding("G0-02", "unknown", "no account export supplied", [], [], confidence="low")
    bl = [c["check"] for c in s15["estimate"]["checks"] if c["status"] == "fail" and c["severity"] == "blocker"
          and c["check"] != "conversion_signal_present"]
    return _finding("G0-02", "fail" if bl else "pass",
                    f"failed blocker checks: {bl}" if bl else "no blocker checks failed", [ref], [s15["id"]],
                    rec="fix the export or tracking before trusting any number" if bl else None)


def g0_funnel_plausible(s16: dict, ref: str):
    rows = s16["estimate"]["stages"]
    if not s16["n"]:
        return _finding("G0-03", "unknown", "no mature periods", [ref], [s16["id"]], confidence="low")
    bad = [f"{rows[k-1]['stage']} < {rows[k]['stage']}" for k in range(1, len(rows))
           if (rows[k]["mean_per_period"] or 0) > (rows[k - 1]["mean_per_period"] or 0)]
    return _finding("G0-03", "fail" if bad else "pass",
                    f"stage totals increase downstream: {bad}" if bad else "stage totals non-increasing",
                    [ref], [s16["id"]],
                    diagnosis="double counting or mixed stage definitions" if bad else None,
                    rec="align stage definitions (one cohort, one count per entity)" if bad else None)


def g0_maturity(s16: dict, ref: str):
    v = s16["validity"]
    return _finding("G0-04", "pass" if v == "valid" else "unknown",
                    f"{s16['n']} mature periods, validity {v}", [ref], [s16["id"]],
                    confidence="high" if v == "valid" else "low", indicative=v != "valid")


def toc_constraint(s16: dict, ref: str, has_test: bool):
    c = s16["estimate"]["constraint"]
    if c is None:
        return _finding("TOC-01", "unknown", "no starving or inconclusive stage at current targets", [ref],
                        [s16["id"]], confidence="low", indicative=s16["validity"] != "valid")
    ok = c["confidence"] in ("medium", "high") or has_test
    return _finding("TOC-01", "pass" if ok else "fail",
                    f"constraint {c['link']} ({c['kind']}), confidence {c['confidence']}", [ref], [s16["id"]],
                    confidence=c["confidence"], indicative=s16["validity"] != "valid")


def toc_owner_hypothesis(hyp: str | None, s16: dict, ref: str):
    c = s16["estimate"]["constraint"]
    if not hyp or not c:
        return _finding("TOC-02", "unknown", "no owner hypothesis stated" if not hyp else "no constraint to compare",
                        [ref], [s16["id"]], confidence="low")
    stage = c["link"].split("->")[-1]
    match = stage.lower() in hyp.lower() or c["link"].lower() in hyp.lower()
    return _finding("TOC-02", "pass" if match else "fail",
                    f"owner hypothesis {'matches' if match else 'differs from'} S16 constraint {c['link']}",
                    [ref], [s16["id"]], ev="reported", confidence="medium",
                    diagnosis=None if match else "the data points elsewhere; the hypothesis is kept as a hypothesis")


def toc_flipflops(flips: list[dict]):
    return _finding("TOC-03", "fail" if flips else "pass",
                    f"{len(flips)} flip-flops in 30 days" if flips else "no flip-flops in 30 days",
                    [f"decision-log:{f['first']},{f['second']}" for f in flips] or ["decision-log.jsonl"], [])


def toc_freeze(blocking: list[dict], link: str | None):
    if not link:
        return _finding("TOC-04", "unknown", "no constraint", ["decision-log.jsonl"], [], confidence="low")
    return _finding("TOC-04", "fail" if blocking else "pass",
                    f"open windows on {link}: {[b['id'] for b in blocking]}" if blocking else f"no open window on {link}",
                    ["decision-log.jsonl"], [])
