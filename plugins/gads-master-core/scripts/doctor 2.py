"""Environment and capability check. Writes capabilities.json. Never reads or stores secrets."""
from __future__ import annotations

import importlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from common.state import account_dir

CORE = Path(__file__).resolve().parents[1]
REQUIRED = ["numpy", "pandas", "scipy", "statsmodels", "yaml", "jsonschema"]
OPTIONAL = ["ruptures"]
CRED_ENV = ["GOOGLE_ADS_CONFIGURATION_FILE_PATH", "GOOGLE_ADS_CLIENT_ID", "GOOGLE_ADS_REFRESH_TOKEN",
            "GOOGLE_APPLICATION_CREDENTIALS"]
INTEL_ENV = ["GADSM_SERP_PROVIDER", "GADSM_SERP_API_KEY"]


def _mod(name):
    try:
        m = importlib.import_module(name)
        return {"ok": True, "version": getattr(m, "__version__", "?")}
    except Exception as e:  # noqa: BLE001 - report any import failure
        return {"ok": False, "error": type(e).__name__}


def _sibling(name: str) -> dict:
    """Find a sibling plugin: dev layout (plugins/<name>) or the installed plugin cache."""
    cands = [CORE.parent / name]
    cache = Path.home() / ".claude" / "plugins" / "cache"
    if cache.exists():
        cands += sorted(cache.glob(f"*/{name}*")) + sorted(cache.glob(f"*/{name}/*"))
    for c in cands:
        cap = c / "capability.json"
        if cap.exists():
            return {"installed": True, "path": str(c), **json.loads(cap.read_text())}
    return {"installed": False}


def run(ws: str, acct: str) -> dict:
    py_ok = sys.version_info >= (3, 10)
    deps = {m: _mod(m) for m in REQUIRED}
    opt = {m: _mod(m) for m in OPTIONAL}
    api, intel = _sibling("gads-master-api"), _sibling("gads-master-intel")
    creds = {k: bool(os.environ.get(k)) for k in CRED_ENV}
    creds["google_ads_yaml_present"] = (Path.home() / "google-ads.yaml").exists()
    stats_ok = py_ok and all(d["ok"] for d in deps.values())
    caps = {
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python": {"version": sys.version.split()[0], "ok": py_ok},
        "stats": "available" if stats_ok else "unavailable",
        "deps": deps, "optional_deps": opt,
        "interpreter": sys.executable,
        "api": ("available" if api.get("status") == "implemented" and any(creds.values())
                else "scaffold_only" if api.get("installed") else "unavailable"),
        "api_plugin": api, "credentials_present": creds,
        "intel": ("available" if intel.get("status") == "implemented" else
                  "scaffold_only" if intel.get("installed") else "unavailable"),
        "intel_plugin": intel, "intel_env_present": {k: bool(os.environ.get(k)) for k in INTEL_ENV},
        "input_mode": "csv_export",
        "notes": [],
    }
    if not stats_ok:
        caps["notes"].append("No statistical verdict possible until the one-time setup runs: "
                             f"python3 \"{CORE / 'scripts' / 'run.py'}\" setup")
    if caps["api"] != "available":
        caps["notes"].append("Input is CSV/export only. Google Ads MCP tools, if present in this session, "
                             "may be used read-only to pull the same reports.")
    if caps["intel"] != "available":
        caps["notes"].append("Intel instruments (auction insights, SERP sampler, SEO x Paid) unavailable: report them as such.")
    if ws and acct:
        (account_dir(ws, acct) / "capabilities.json").write_text(json.dumps(caps, indent=2))
    return caps
