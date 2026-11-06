"""Per-account state location. State lives outside the plugin so updates never overwrite it."""
from __future__ import annotations

import re
from pathlib import Path

ACCOUNT_RE = re.compile(r"^[A-Za-z0-9_-]{1,40}$")


def account_dir(workspace: str, account: str, create: bool = True) -> Path:
    if not ACCOUNT_RE.match(account):
        raise ValueError("account id must match [A-Za-z0-9_-]{1,40} (e.g. 123-456-7890)")
    d = Path(workspace).expanduser().resolve() / ".gads-master" / account
    if create:
        for sub in ("", "intel", "stats-cache", "runs"):
            (d / sub).mkdir(parents=True, exist_ok=True)
    return d
