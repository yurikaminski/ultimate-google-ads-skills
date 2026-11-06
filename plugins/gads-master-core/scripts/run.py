#!/usr/bin/env python3
"""Single entry point: python3 "${CLAUDE_PLUGIN_ROOT}/scripts/run.py" <command> ...

Commands: doctor | stats | context | profile | ledger | onboard | diagnose
Output is JSON on stdout. Exit codes: 0 ok, 2 usage/validation error, 3 not implemented.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "stats")]


def _out(obj) -> None:
    print(json.dumps(obj, indent=2, default=str))


def _val(s: str):
    import yaml
    return yaml.safe_load(s)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "stats":
        from adsstats.__main__ import main as stats_main
        return stats_main(rest)

    p = argparse.ArgumentParser(prog=f"run.py {cmd}")
    p.add_argument("--workspace", default=".")
    p.add_argument("--account")
    try:
        if cmd == "doctor":
            import doctor
            a = p.parse_args(rest)
            _out(doctor.run(a.workspace, a.account))
        elif cmd == "context":
            from memory import context as c
            p.add_argument("action", choices=["init", "get", "set", "validate", "stale", "merge-draft"])
            p.add_argument("--field"); p.add_argument("--value"); p.add_argument("--source", default="user")
            p.add_argument("--confidence", default="high"); p.add_argument("--evidence", action="append", default=[])
            p.add_argument("--ttl-days", type=int); p.add_argument("--draft"); p.add_argument("--confirmed", action="store_true")
            a = p.parse_args(rest)
            if a.action == "init":
                _out(c.init(a.workspace, a.account))
            elif a.action in ("get", "validate"):
                obj, narrative = c.load(a.workspace, a.account)
                from common.schema import validate
                validate("business-context.v1", obj)
                _out(obj if a.action == "get" else {"valid": True})
            elif a.action == "set":
                _out(c.set_field(a.workspace, a.account, a.field, _val(a.value), a.source, a.confidence, a.evidence, a.ttl_days))
            elif a.action == "stale":
                _out(c.stale(a.workspace, a.account))
            else:
                _out(c.merge_draft(a.workspace, a.account, json.loads(Path(a.draft).read_text()), a.confirmed))
        elif cmd == "profile":
            from memory import context as c
            p.add_argument("action", choices=["get", "set"])
            p.add_argument("--key"); p.add_argument("--value")
            a = p.parse_args(rest)
            _out(c.profile_get(a.workspace, a.account) if a.action == "get"
                 else c.profile_set(a.workspace, a.account, a.key, _val(a.value)))
        elif cmd == "ledger":
            from memory import ledger as L
            p.add_argument("action", choices=["append", "list", "status", "open-windows", "freeze-check", "flipflops", "due"])
            p.add_argument("--log", default="decision", choices=list(L.FILES))
            p.add_argument("--record", help="JSON record (append)"); p.add_argument("--id"); p.add_argument("--status")
            p.add_argument("--entity"); p.add_argument("--link"); p.add_argument("--last", type=int)
            p.add_argument("--days", type=int, default=30)
            a = p.parse_args(rest)
            if a.action == "append":
                _out(L.append(a.workspace, a.account, a.log, json.loads(a.record)))
            elif a.action == "list":
                rows = L.current(a.workspace, a.account, a.log) if a.log == "decision" else L.events(a.workspace, a.account, a.log)
                _out(rows[-a.last:] if a.last else rows)
            elif a.action == "status":
                _out(L.update_status(a.workspace, a.account, a.id, a.status))
            elif a.action == "open-windows":
                _out(L.open_windows(a.workspace, a.account))
            elif a.action == "due":
                _out(L.due_to_close(a.workspace, a.account))
            elif a.action == "freeze-check":
                _out(L.freeze_check(a.workspace, a.account, a.entity, a.link))
            else:
                _out(L.flipflops(a.workspace, a.account, a.days))
        elif cmd == "onboard":
            from onboard import cli as ob
            return ob.main(rest)
        elif cmd == "diagnose":
            from diagnose import brief
            return brief.main(rest)
        else:
            print(json.dumps({"error": f"unknown command {cmd}"}), file=sys.stderr)
            return 2
    except (ValueError, KeyError, FileNotFoundError) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
