"""Fetch one public page for onboarding. robots.txt respected, Google SERPs refused, size capped."""
from __future__ import annotations

import hashlib
import re
import urllib.request
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlparse

UA = "gads-master-onboard/0.1 (public page research; respects robots.txt)"
MAX_BYTES = 2_000_000
BLOCKED_HOST = re.compile(r"(^|\.)google\.[a-z.]+$")  # no Google SERP scraping


def allowed(url: str) -> tuple[bool, str]:
    u = urlparse(url)
    if u.scheme not in ("http", "https"):
        return False, "only http(s) URLs"
    if BLOCKED_HOST.search(u.netloc.lower()) and u.path.startswith(("/search", "/url")):
        return False, "Google search result pages are never fetched (hard stop)"
    rp = urllib.robotparser.RobotFileParser(f"{u.scheme}://{u.netloc}/robots.txt")
    try:
        rp.read()
    except Exception:  # noqa: BLE001 - unreachable robots.txt: treat as allowed, as crawlers do
        return True, "robots.txt unreachable"
    return (rp.can_fetch(UA, url), "robots.txt")


def fetch(url: str, out_dir: str) -> dict:
    ok, why = allowed(url)
    if not ok:
        return {"url": url, "fetched": False, "reason": why}
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            ctype = r.headers.get("Content-Type", "")
            if "html" not in ctype:
                return {"url": url, "fetched": False, "reason": f"not html ({ctype})"}
            body = r.read(MAX_BYTES + 1)
    except Exception as e:  # noqa: BLE001
        return {"url": url, "fetched": False, "reason": f"{type(e).__name__}: {e}"[:200]}
    if len(body) > MAX_BYTES:
        body = body[:MAX_BYTES]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / (hashlib.sha256(url.encode()).hexdigest()[:16] + ".html")
    path.write_bytes(body)
    return {"url": url, "fetched": True, "path": str(path), "bytes": len(body)}
