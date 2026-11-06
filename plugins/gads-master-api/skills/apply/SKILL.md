---
name: apply
description: "Planned for v0.3, not implemented: executes an approved change-draft through the mutation gate."
disable-model-invocation: true
---

# apply (scaffold, v0.3)

Status: NOT IMPLEMENTED. Writes are impossible in this version. Say so and hand the user the draft to apply manually.

Gate sequence (v0.3): load `change-draft.v1` > `common.gate.assert_applicable(draft, dry_run_passed)` from gads-master-core > dry-run with `validate_only` > apply with the idempotency key > verify by re-reading the resources > `run.py ledger append --log decision` (status applied, window) > keep rollback operations. New campaigns are created PAUSED. Never test a write capability by trying it.

TODO
- `scripts/gads/apply.py` calling the gate, partial-failure handling, verification reads.
- Tests: no write without approved draft, PAUSED enforcement, rollback replay, idempotency.

Acceptance criteria: contract test proves no code path reaches the API mutate call without `assert_applicable` passing.
