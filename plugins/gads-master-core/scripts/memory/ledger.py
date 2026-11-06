"""Append-only JSONL ledgers with file locks.

Logs: decision (decision-log.jsonl), constraint (constraint-history.jsonl), parking (parking-lot.jsonl).
Status changes are new events with the same id; current state is the fold of events by id.
"""
from __future__ import annotations

import fcntl
import json
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from common.schema import validate
from common.state import account_dir

FILES = {"decision": "decision-log.jsonl", "constraint": "constraint-history.jsonl", "parking": "parking-lot.jsonl"}
OPEN = {"applied", "measuring"}
OPPOSITE = {"increase": "decrease", "decrease": "increase", "add": "remove", "remove": "add"}


@contextmanager
def _locked(path: Path, mode: str):
    path.touch(exist_ok=True)
    with open(path, mode) as f:
        fcntl.flock(f, fcntl.LOCK_EX if "a" in mode else fcntl.LOCK_SH)
        try:
            yield f
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def path(ws: str, acct: str, log: str) -> Path:
    return account_dir(ws, acct) / FILES[log]


def append(ws: str, acct: str, log: str, rec: dict) -> dict:
    rec = dict(rec)
    rec.setdefault("ts", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    if log == "decision":
        rec.setdefault("schema", "decision-log.v1")
        rec.setdefault("id", f"D-{uuid.uuid4().hex[:8]}")
        validate("decision-log.v1", rec)
    elif log == "parking":
        if not isinstance(rec.get("item"), str) or len(rec["item"]) > 160 or "\n" in rec["item"]:
            raise ValueError("parking item must be one line, <= 160 chars")
    with _locked(path(ws, acct, log), "a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def events(ws: str, acct: str, log: str) -> list[dict]:
    with _locked(path(ws, acct, log), "r") as f:
        return [json.loads(line) for line in f if line.strip()]


def current(ws: str, acct: str, log: str = "decision") -> list[dict]:
    state: dict[str, dict] = {}
    for e in events(ws, acct, log):
        key = e.get("id") or e["ts"]
        state[key] = {**state.get(key, {}), **e}
    return sorted(state.values(), key=lambda r: r["ts"])


def update_status(ws: str, acct: str, decision_id: str, status: str, **extra) -> dict:
    cur = {d["id"]: d for d in current(ws, acct)}
    if decision_id not in cur:
        raise KeyError(decision_id)
    rec = {**cur[decision_id], **extra, "status": status}
    rec.pop("ts")  # append stamps the event time
    return append(ws, acct, "decision", rec)


def open_windows(ws: str, acct: str, today: date | None = None) -> list[dict]:
    today = today or date.today()
    out = []
    for d in current(ws, acct):
        w = d.get("window") or {}
        if d["status"] in OPEN and w.get("end") and date.fromisoformat(w["end"]) >= today:
            out.append(d)
    return out


def due_to_close(ws: str, acct: str, today: date | None = None) -> list[dict]:
    today = today or date.today()
    return [d for d in current(ws, acct) if d["status"] in OPEN and (d.get("window") or {}).get("end")
            and date.fromisoformat(d["window"]["end"]) < today]


def freeze_check(ws: str, acct: str, entity: str | None = None, link: str | None = None,
                 today: date | None = None) -> dict:
    """Is a change on this entity / constraint link allowed now? Frozen inside open windows."""
    blocking = [d for d in open_windows(ws, acct, today)
                if (entity and d.get("entity") == entity) or (link and d.get("constraint_link") == link)]
    return {"allowed": not blocking, "blocking": [{"id": d["id"], "window": d["window"]} for d in blocking]}


def flipflops(ws: str, acct: str, days: int = 30) -> list[dict]:
    """Same entity changed in opposite directions within `days`."""
    acted = [d for d in current(ws, acct) if d["status"] in {"applied", "measuring", "closed"} and d.get("entity")]
    out = []
    for i, a in enumerate(acted):
        for b in acted[i + 1:]:
            if a["entity"] == b["entity"] and OPPOSITE.get(a.get("direction")) == b.get("direction"):
                gap = (datetime.fromisoformat(b["ts"]) - datetime.fromisoformat(a["ts"])).days
                if gap <= days:
                    out.append({"entity": a["entity"], "first": a["id"], "second": b["id"], "days_apart": gap})
    return out
