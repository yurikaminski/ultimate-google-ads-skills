"""Python dependency bootstrap (stdlib only).

Deps live in a private venv OUTSIDE the plugin folder (the plugin dir is replaced on update):
  $GADSM_VENV > $CLAUDE_PLUGIN_DATA/venv > ~/.gads-master/venv
`run.py setup` creates it (uv if available, else python3 -m venv + pip). Every other command
re-executes itself inside that venv when the current interpreter lacks the deps.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

REQ = Path(__file__).resolve().parents[1] / "requirements.txt"
MODULES = ["numpy", "pandas", "scipy", "statsmodels", "yaml", "jsonschema"]
MARK = "GADSM_BOOTSTRAPPED"


def venv_dir() -> Path:
    if os.environ.get("GADSM_VENV"):
        return Path(os.environ["GADSM_VENV"]).expanduser()
    if os.environ.get("CLAUDE_PLUGIN_DATA"):
        return Path(os.environ["CLAUDE_PLUGIN_DATA"]) / "venv"
    return Path.home() / ".gads-master" / "venv"


def venv_python() -> Path:
    d = venv_dir()
    return d / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def missing() -> list[str]:
    return [m for m in MODULES if importlib.util.find_spec(m) is None]


def ensure(argv: list[str]) -> None:
    """Re-exec inside the private venv if deps are missing here. Returns only if deps are importable."""
    if not missing():
        return
    py = venv_python()
    if py.exists() and not os.environ.get(MARK):
        os.environ[MARK] = "1"
        os.execv(str(py), [str(py), str(Path(sys.argv[0]).resolve()), *argv])
    import json
    print(json.dumps({"error": "deps_missing", "missing": missing(),
                      "fix": f'python3 "{Path(__file__).resolve().parent / "run.py"}" setup',
                      "note": "one-time install of numpy, pandas, scipy, statsmodels, pyyaml, jsonschema from PyPI "
                              f"into {venv_dir()} (outside the plugin folder)"}), file=sys.stderr)
    raise SystemExit(4)


def setup() -> dict:
    d, py = venv_dir(), venv_python()
    d.parent.mkdir(parents=True, exist_ok=True)
    uv = shutil.which("uv")
    if uv:
        if not py.exists():
            subprocess.run([uv, "venv", "-q", "--python", "3.12", str(d)], check=True)
        subprocess.run([uv, "pip", "install", "-q", "--python", str(py), "-r", str(REQ)], check=True)
        tool = "uv"
    else:
        if sys.version_info < (3, 10):
            raise SystemExit("Python >= 3.10 required to create the venv (or install uv: https://docs.astral.sh/uv/)")
        if not py.exists():
            subprocess.run([sys.executable, "-m", "venv", str(d)], check=True)
        subprocess.run([str(py), "-m", "pip", "install", "-q", "-r", str(REQ)], check=True)
        tool = "venv+pip"
    out = subprocess.run([str(py), "-c", f"import {', '.join(MODULES)}; print('ok')"], capture_output=True, text=True)
    return {"venv": str(d), "python": str(py), "tool": tool, "deps_ok": out.stdout.strip() == "ok"}
