"""Diagnose end-to-end and contract tests (planted constraints, warn-first, gate 0, freeze, memory, gate)."""
import json
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest
from common.gate import GateError, assert_applicable
from common.schema import errors
from conftest import chain, planted_funnel
from diagnose import brief as B
from memory import context as C
from memory import ledger as L

RUN = Path(__file__).resolve().parents[1] / "scripts" / "run.py"
ACC = "acct-1"
SAAS_T = [None, 0.05, 0.08, 0.40, 0.40, 0.30]
ECOM_T = [None, 0.02, 0.92, 0.10, 0.50, 0.60]


def setup(tmp_path, model, targets, plant, weeks=16, **kw):
    stages = [s["id"] for s in chain(model)["stages"]]
    df, cfg = planted_funnel(stages, targets, plant=plant, weeks=weeks, **kw)
    f = tmp_path / "funnel.csv"
    df.to_csv(f, index=False)
    C.profile_set(tmp_path, ACC, "targets.throughput", cfg["target_throughput"])
    for s, r in cfg["target_rates"].items():
        C.profile_set(tmp_path, ACC, f"targets.rates.{s}", r)
    C.profile_set(tmp_path, ACC, "lag_days", 30)
    return f, stages


STATS_ID = re.compile(r"S(0[1-9]|1[0-6])-[0-9a-f]{10}")


@pytest.mark.parametrize("model,targets,plant", [("saas", SAAS_T, 3), ("ecommerce", ECOM_T, 4), ("saas", SAAS_T, 0)])
def test_planted_constraint_end_to_end(tmp_path, model, targets, plant):
    f, stages = setup(tmp_path, model, targets, plant)
    brief, results, findings = B.build(str(tmp_path), ACC, str(f), model)
    c = brief["constraint"]
    assert c["link"].split("->")[-1] == stages[plant] and brief["status"] == "constraint_found"
    assert len(brief["exploit"]) <= 3 and brief["subordinate"] and all(e["gated"] for e in brief["elevate"])
    for a in brief["exploit"]:
        assert a["stats_ids"] and all(STATS_ID.fullmatch(s) for s in a["stats_ids"])
    for line in c["evidence"]:  # every number in evidence cites a stats id (operational lines are reported, not numeric)
        assert STATS_ID.search(line) or line.startswith("operational:")
    for r in results:
        assert not errors("stats-result.v1", json.loads(json.dumps(r, default=float)))
    assert brief["warn_first"] is None
    assert all(f_["evidence_type"] in ("observed", "reported", "estimated") for f_ in findings)


def test_warn_first_is_first_line_when_low_power(tmp_path):
    f, _ = setup(tmp_path, "saas", SAAS_T, 2, weeks=3)
    brief, results, _ = B.build(str(tmp_path), ACC, str(f), "saas")
    md = B.render(brief)
    assert brief["warn_first"] and md.splitlines()[0] == brief["warn_first"]
    assert md.startswith("STATISTICAL VALIDITY WARNING")
    assert brief["constraint"] is None or brief["constraint"]["confidence"] == "low"


def test_missing_target_returns_unknown_with_question(tmp_path):
    f = tmp_path / "f.csv"
    pd.DataFrame({"period": ["2026-01-05"], "impressions": [1]}).to_csv(f, index=False)
    brief, _, _ = B.build(str(tmp_path), ACC, str(f), "saas")
    assert brief["status"] == "unknown" and "Q02" in brief["warn_first"]


def test_scaffold_playbook_is_unknown(tmp_path):
    f, _ = setup(tmp_path, "saas", SAAS_T, 2)
    brief, _, _ = B.build(str(tmp_path), ACC, str(f), "marketplace")
    assert brief["status"] == "unknown"


def test_gate0_blocks_on_dead_conversion_tracking(tmp_path):
    f, _ = setup(tmp_path, "saas", SAAS_T, 2)
    ex = tmp_path / "export.csv"
    pd.DataFrame({"date": [str(date.today() - timedelta(days=i)) for i in range(1, 8)], "campaign": "a",
                  "impressions": 1000, "clicks": 50, "conversions": 0, "cost": 25.0}).to_csv(ex, index=False)
    brief, _, _ = B.build(str(tmp_path), ACC, str(f), "saas", export=str(ex))
    assert brief["status"] == "blocked_gate0"
    assert any(g["control_id"] == "G0-01" and g["status"] == "fail" for g in brief["gate0"])
    assert brief["parking_lot"][0].startswith("GATE 0 BLOCKER")


def test_open_window_freezes_exploit(tmp_path):
    f, stages = setup(tmp_path, "saas", SAAS_T, 2)
    link = f"{stages[1]}->{stages[2]}"
    L.append(tmp_path, ACC, "decision", {"hypothesis": "new LP", "constraint_link": link, "status": "measuring",
             "window": {"start": str(date.today()), "end": str(date.today() + timedelta(days=10))}})
    brief, _, _ = B.build(str(tmp_path), ACC, str(f), "saas")
    assert len(brief["exploit"]) == 1 and brief["exploit"][0]["action"].startswith("FROZEN")


def test_owner_hypothesis_is_tested_not_evidence(tmp_path):
    f, stages = setup(tmp_path, "saas", SAAS_T, 2)
    C.set_field(tmp_path, ACC, "owner_hypothesis_constraint", "sales team capacity (sql)", "user", "high")
    brief, _, findings = B.build(str(tmp_path), ACC, str(f), "saas")
    assert brief["owner_hypothesis"]["matches"] is False
    assert not any("sales team" in e for e in brief["constraint"]["evidence"])


def test_cli_commit_writes_memory_through_ledger(tmp_path):
    f, _ = setup(tmp_path, "ecommerce", ECOM_T, 3)
    r = subprocess.run([sys.executable, str(RUN), "diagnose", "--workspace", str(tmp_path), "--account", ACC,
                        "--funnel", str(f), "--playbook", "ecommerce", "--commit"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    d = tmp_path / ".gads-master" / ACC
    assert L.events(tmp_path, ACC, "constraint")[-1]["link"] == out["brief"]["constraint"]["link"]
    assert (d / "baselines.json").exists() and (d / "runs" / f"{out['run_id']}.json").exists()
    assert out["markdown"].startswith("# Constraint Brief")


def _draft(**kw):
    d = {"schema": "change-draft.v1", "id": "CD-1", "account_id": ACC, "created_at": "2026-11-06T00:00:00Z",
         "constraint_link": "clicks->signups_or_leads", "hypothesis": "h",
         "operations": [{"resource": "campaign", "op": "create", "payload": {"status": "PAUSED"}}],
         "warn_first": None, "stats_ids": ["S16-0123456789"], "window_days": 28,
         "rollback": [{"op": "remove"}], "idempotency_key": "k" * 16, "approval": None, "status": "draft"}
    d.update(kw)
    return d


def test_writes_impossible_without_approved_draft():
    with pytest.raises(GateError):
        assert_applicable(_draft(), dry_run_passed=True)
    ok = _draft(status="approved", approval={"approved_by": "owner", "approved_at": "2026-11-06T10:00:00Z"})
    with pytest.raises(GateError):
        assert_applicable(ok, dry_run_passed=False)
    assert_applicable(ok, dry_run_passed=True)
    live = _draft(status="approved", approval={"approved_by": "o", "approved_at": "t"},
                  operations=[{"resource": "campaign", "op": "create", "payload": {"status": "ENABLED"}}])
    with pytest.raises(GateError):
        assert_applicable(live, dry_run_passed=True)


def test_core_has_no_google_ads_write_path():
    src = "\n".join(p.read_text() for p in (Path(__file__).resolve().parents[1] / "scripts").rglob("*.py"))
    assert "google.ads" not in src and "mutate" not in src.lower().replace("mutation gate", "")


def test_controls_registry_has_real_logic():
    from diagnose import controls as K
    reg = K.registry()
    for cid, c in reg.items():
        for k in ("inputs", "rule", "evidence_required", "pass", "fail", "unknown"):
            assert c[k] and "TODO" not in str(c[k]), (cid, k)
        if c["implemented_in"] == "v0.1":
            assert callable(getattr(K, c["evaluator"])), cid


def test_schemas_are_valid_json_schema():
    from jsonschema import Draft202012Validator
    for p in (Path(__file__).resolve().parents[1] / "schemas").glob("*.json"):
        Draft202012Validator.check_schema(json.loads(p.read_text()))


@pytest.mark.parametrize("model", ["saas", "ecommerce"])
def test_chain_yaml_is_well_formed(model):
    ch = chain(model)
    for s in ch["stages"]:
        assert 1 <= s["effort"] <= 5 and s["toc_link"]
        for k in ("exploit", "subordinate", "elevate", "instruments", "operational_signals"):
            assert s[k] and all(isinstance(x, str) for x in s[k]), (s["id"], k)
