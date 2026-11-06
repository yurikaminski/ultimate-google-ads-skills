"""Mutation gate precondition. The api plugin (v0.3) must call assert_applicable() before any write.

Core itself never writes to Google Ads. This module makes "write without an approved draft" impossible
for any caller that goes through the gate.
"""
from __future__ import annotations

from common.schema import validate


class GateError(PermissionError):
    pass


def assert_applicable(draft: dict, dry_run_passed: bool) -> None:
    validate("change-draft.v1", draft)
    if draft["status"] not in ("approved", "dry_run_ok"):
        raise GateError(f"draft {draft['id']} is {draft['status']}: needs explicit user approval")
    ap = draft.get("approval") or {}
    if not (ap.get("approved_by") and ap.get("approved_at")):
        raise GateError("approval record missing (approved_by, approved_at)")
    if not dry_run_passed:
        raise GateError("dry-run (validate_only) must pass before apply")
    if not draft.get("rollback"):
        raise GateError("rollback plan required")
    for op in draft["operations"]:
        if op["op"] == "create" and op["resource"] == "campaign" and op["payload"].get("status") != "PAUSED":
            raise GateError("new campaigns must be created PAUSED")
