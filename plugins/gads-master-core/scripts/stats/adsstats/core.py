"""Shared result model for adsstats. No network access anywhere in this package."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

VALIDITY = ("valid", "low_power", "insufficient")
DEFAULT_CFG = Path(__file__).resolve().parent.parent / "stats-config.yaml"


def load_cfg(path: str | None = None, overrides: dict | None = None) -> dict:
    cfg = yaml.safe_load(DEFAULT_CFG.read_text())
    if path:
        _deep_update(cfg, yaml.safe_load(Path(path).read_text()) or {})
    if overrides:
        _deep_update(cfg, overrides)
    return cfg


def _deep_update(base: dict, new: dict) -> None:
    for k, v in new.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_update(base[k], v)
        else:
            base[k] = v


def input_hash(obj) -> str:
    if isinstance(obj, (str, Path)) and Path(obj).exists():
        data = Path(obj).read_bytes()
    else:
        data = json.dumps(obj, sort_keys=True, default=str).encode()
    return hashlib.sha256(data).hexdigest()


def result(analysis: str, *, n, estimate, ci, method, assumptions_checked, warnings,
           validity, inp_hash, seed=None, details=None, status="ok") -> dict:
    assert validity in VALIDITY, validity
    return {
        "schema": "stats-result.v1",
        "id": f"{analysis}-{inp_hash[:10]}",
        "analysis": analysis,
        "n": n,
        "estimate": estimate,
        "ci": ci,
        "method": method,
        "assumptions_checked": assumptions_checked,
        "warnings": warnings,
        "validity": validity,
        "status": status,
        "input_hash": inp_hash,
        "seed": seed,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "details": details or {},
    }


def warn_first(results: list[dict]) -> str | None:
    """The line that must open any response citing these results, or None if all valid."""
    bad = [r for r in results if r["validity"] != "valid"]
    if not bad:
        return None
    worst = "insufficient" if any(r["validity"] == "insufficient" for r in bad) else "low_power"
    why = "; ".join(f"{r['id']}: {r['warnings'][0] if r['warnings'] else r['validity']}" for r in bad)
    return (f"STATISTICAL VALIDITY WARNING ({worst}): {why}. "
            "Findings below are indicative only; confidence is capped at low.")
