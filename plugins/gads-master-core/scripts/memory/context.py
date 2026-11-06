"""business-context.md (structured fields with provenance + editable Narrative) and profile.yaml.

The LLM never hand-edits these files. Everything goes through this module, which validates
against business-context.v1 / profile.v1 and refuses raw or instruction-like external text.
"""
from __future__ import annotations

import json
import re
from datetime import date, timedelta
from pathlib import Path

import yaml

from common.schema import validate
from common.state import account_dir

FIELDS = ["business_model", "buyer_type", "vertical", "primary_offer", "price_point", "markets",
          "sales_motion", "sales_cycle_days", "conversion_path", "seasonality", "competitors",
          "brand_strength", "tracking_maturity", "goal", "owner_hypothesis_constraint",
          "regulatory_flags", "do_not_touch"]
DEFAULT_TTL = {"inferred": 90, "account_data": 30}  # days; user-sourced fields re-verify only on review
REVIEW_TTL_DAYS = 180
INJECTION = re.compile(r"(ignore (all|any|previous|prior)|disregard|system prompt|you are now|"
                       r"<\s*/?\s*script|assistant:|###\s*instruction)", re.I)
NARRATIVE_HEAD = "## Narrative"


def _plain(obj):
    """YAML parses ISO dates into date objects; schemas expect strings."""
    return json.loads(json.dumps(obj, default=str))


def _today() -> str:
    return date.today().isoformat()


def _unknown() -> dict:
    return {"value": None, "source": "unknown", "confidence": "low", "evidence": [], "captured_at": _today()}


def _ctx_path(ws, acct) -> Path:
    return account_dir(ws, acct) / "business-context.md"


def _guard(value) -> None:
    for s in _strings(value):
        if INJECTION.search(s):
            raise ValueError("refused: value looks like instructions from external content, not a business fact")


def _strings(v):
    if isinstance(v, str):
        yield v
    elif isinstance(v, dict):
        for x in v.values():
            yield from _strings(x)
    elif isinstance(v, list):
        for x in v:
            yield from _strings(x)


def init(ws: str, acct: str) -> dict:
    p = _ctx_path(ws, acct)
    if p.exists():
        return load(ws, acct)[0]
    obj = {"schema": "business-context.v1", "account_id": acct, "last_reviewed": _today(),
           "fields": {f: _unknown() for f in FIELDS}}
    save(ws, acct, obj, "Free text the owner may edit. Not used as evidence.\n")
    return obj


def load(ws: str, acct: str) -> tuple[dict, str]:
    p = _ctx_path(ws, acct)
    if not p.exists():
        raise FileNotFoundError(f"no business-context for account {acct}: run onboard")
    text = p.read_text()
    _, front, body = text.split("---\n", 2)
    narrative = body.split(NARRATIVE_HEAD, 1)[1].lstrip("\n") if NARRATIVE_HEAD in body else ""
    return _plain(yaml.safe_load(front)), narrative


def save(ws: str, acct: str, obj: dict, narrative: str | None = None) -> None:
    validate("business-context.v1", obj)
    if narrative is None:
        try:
            narrative = load(ws, acct)[1]
        except FileNotFoundError:
            narrative = ""
    front = yaml.safe_dump(obj, sort_keys=False, allow_unicode=True)
    _ctx_path(ws, acct).write_text(f"---\n{front}---\n\n# Business context: {acct}\n\n"
                                   f"Structured fields above are written only by context.py.\n\n"
                                   f"{NARRATIVE_HEAD}\n\n{narrative}")


def set_field(ws: str, acct: str, name: str, value, source: str, confidence: str,
              evidence: list[str] | None = None, ttl_days: int | None = None) -> dict:
    if name not in FIELDS:
        raise KeyError(f"unknown field {name}")
    _guard(value)
    obj = init(ws, acct)
    if source == "inferred" and ttl_days is None:
        ttl_days = DEFAULT_TTL["inferred"]
    if name == "competitors" and value:
        value = [{**c, "evidence_type": "reported"} for c in value]  # competitor claims are never observed
    obj["fields"][name] = {"value": value, "source": source, "confidence": confidence,
                           "evidence": evidence or [], "captured_at": _today(), "ttl_days": ttl_days}
    save(ws, acct, obj)
    return obj["fields"][name]


def merge_draft(ws: str, acct: str, draft: dict, confirmed: bool = False) -> dict:
    """Merge an onboarding draft. Never overwrites a user-sourced field with an inferred one."""
    obj = init(ws, acct)
    for name, f in draft.get("fields", {}).items():
        if name not in FIELDS:
            continue
        _guard(f.get("value"))
        cur = obj["fields"][name]
        if cur["source"] == "user" and f.get("source") != "user":
            continue
        obj["fields"][name] = {**_unknown(), **{k: f[k] for k in f if k in
                               ("value", "source", "confidence", "evidence", "captured_at", "ttl_days")}}
    if confirmed:
        obj["last_reviewed"] = _today()
    save(ws, acct, obj)
    return obj


def stale(ws: str, acct: str, today: date | None = None) -> dict:
    today = today or date.today()
    try:
        obj, _ = load(ws, acct)
    except FileNotFoundError:
        return {"missing": True, "stale_fields": [], "review_due": True, "unknown_fields": FIELDS}
    out = []
    for name, f in obj["fields"].items():
        ttl = f.get("ttl_days")
        if ttl and date.fromisoformat(str(f["captured_at"])) + timedelta(days=ttl) < today:
            out.append(name)
    review_due = date.fromisoformat(str(obj["last_reviewed"])) + timedelta(days=REVIEW_TTL_DAYS) < today
    unknown = [n for n, f in obj["fields"].items() if f["source"] == "unknown"]
    return {"missing": False, "stale_fields": out, "review_due": review_due, "unknown_fields": unknown}


# ---------- profile.yaml ----------

def _prof_path(ws, acct) -> Path:
    return account_dir(ws, acct) / "profile.yaml"


def profile_get(ws: str, acct: str) -> dict:
    p = _prof_path(ws, acct)
    if not p.exists():
        prof = {"schema": "profile.v1", "currency": None, "period": "week", "lag_days": None,
                "targets": {"throughput": None, "throughput_stage": None, "rates": {}},
                "unit_economics": {}, "guardrails": {}, "risk": {"alpha": 0.10, "min_periods": 4},
                "effort": {}}
        validate("profile.v1", prof)
        p.write_text(yaml.safe_dump(prof, sort_keys=False))
    return _plain(yaml.safe_load(p.read_text()))


def profile_set(ws: str, acct: str, key: str, value) -> dict:
    """Dotted key, e.g. targets.rates.sql=0.4 or unit_economics.gross_margin=0.7"""
    prof = profile_get(ws, acct)
    cur = prof
    *parents, leaf = key.split(".")
    for k in parents:
        cur = cur.setdefault(k, {})
    cur[leaf] = value
    validate("profile.v1", prof)
    _prof_path(ws, acct).write_text(yaml.safe_dump(prof, sort_keys=False))
    return prof
