"""run.py onboard <fetch|extract|draft|questions>"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from onboard import draft, extract, fetch, questions


def main(argv) -> int:
    p = argparse.ArgumentParser(prog="run.py onboard")
    sub = p.add_subparsers(dest="action", required=True)
    f = sub.add_parser("fetch"); f.add_argument("--url", action="append", required=True); f.add_argument("--out", required=True)
    e = sub.add_parser("extract"); e.add_argument("--file", required=True); e.add_argument("--url", required=True)
    d = sub.add_parser("draft")
    d.add_argument("--company", nargs="+", required=True, help="signal JSON files for the company's pages")
    d.add_argument("--competitor", nargs="*", default=[], help="domain=signals.json[,signals2.json]")
    d.add_argument("--out")
    q = sub.add_parser("questions")
    q.add_argument("--workspace", default="."); q.add_argument("--account", required=True)
    q.add_argument("--playbook", required=True); q.add_argument("--draft")
    q.add_argument("--answered", default=""); q.add_argument("--max", type=int, default=7)
    a = p.parse_args(argv)
    if a.action == "fetch":
        res = [fetch.fetch(u, a.out) for u in a.url]
    elif a.action == "extract":
        res = extract.extract(Path(a.file).read_text(errors="replace"), a.url)
    elif a.action == "draft":
        comp = {}
        for spec in a.competitor:
            dom, files = spec.split("=", 1)
            comp[dom] = [json.loads(Path(x).read_text()) for x in files.split(",")]
        res = draft.build([json.loads(Path(x).read_text()) for x in a.company], comp)
        if a.out:
            Path(a.out).write_text(json.dumps(res, indent=2))
    else:
        from memory import context as C
        if a.draft:
            fields = json.loads(Path(a.draft).read_text())["fields"]
        else:
            try:
                fields = C.load(a.workspace, a.account)[0]["fields"]
            except FileNotFoundError:
                fields = {}
        res = questions.select(fields, C.profile_get(a.workspace, a.account), a.playbook,
                               {x for x in a.answered.split(",") if x}, a.max)
    print(json.dumps(res, indent=2, default=str))
    return 0
