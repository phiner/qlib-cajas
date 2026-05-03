# Phase 4646–4765 — Routine Stability Watch Closure / Semantics Freeze

## Context

Branch: `phase-post-merge-research-next`

Current baseline after Phase 4526–4645:

- Routine release-cycle stability report is implemented.
- Current stability status is `watch` by design because one optional follow-up remains open.
- Release readiness remains `ready`.
- Final reviewer packet remains `ready_for_review`.
- Milestone review state remains `ready_for_review`, `blocking=false`.
- Optional followups remain `status=open`, `count=1`, `blocking=false`.
- Fast validation passed at about `63.45s`, with `pytest_fast=57.33s`.
- No Qlib core changes, no trading execution, no broker routing, no live/paper trading, and no training/workflow execution are in scope.

The goal of this phase is **not** to force all optional followups closed. The goal is to make the routine `watch` state reviewer-safe, explicit, stable, and non-blocking, so future maintainers understand that it is a maintenance signal rather than a release blocker.

## Objectives

1. Freeze the intended semantics of routine stability `watch`.
2. Add a small closure/interpretation report that explains why `watch` is non-blocking when release readiness is already `ready`.
3. Integrate that closure into final reviewer packet, release readiness, and milestone packet.
4. Ensure optional followup count `1` remains allowed as routine/non-blocking.
5. Preserve canonical-only producer behavior and legacy read normalization.
6. Keep this phase small and maintenance-only.

## Required implementation

### 1. Add routine stability watch closure report

Create:

- `cajas/reports/validation_routine_stability_watch_closure.py`
- `cajas/scripts/build_validation_routine_stability_watch_closure.py`
- `cajas/tests/test_validation_routine_stability_watch_closure.py`

The report should read existing generated artifacts where possible, especially:

- `tmp/validation-routine-release-cycle-stability.json`
- `tmp/validation-release-readiness.json`
- `tmp/validation-final-reviewer-packet.json`
- `tmp/validation-milestone-packet.json`
- `tmp/validation-optional-followups.json`

Expected output artifacts:

- `tmp/validation-routine-stability-watch-closure.json`
- `tmp/validation-routine-stability-watch-closure.md`

Suggested schema fields:

```json
{
  "status": "closed_non_blocking" | "watch" | "blocked",
  "review_state": "ready_for_review" | "watch" | "blocked",
  "blocking": false,
  "reason_code": "routine_optional_followup_only",
  "stability_status": "watch",
  "release_readiness_status": "ready",
  "final_reviewer_packet_status": "ready_for_review",
  "milestone_review_state": "ready_for_review",
  "optional_followup_count": 1,
  "optional_followups_blocking": false,
  "remaining_followup_type": "slow_test_optimization",
  "interpretation": "Routine stability watch is a non-blocking maintenance signal, not a release blocker.",
  "next_action": "monitor_next_release_cycle",
  "scope_boundary": {
    "qlib_core_changes": false,
    "trading_execution": false,
    "broker_routing": false,
    "training_workflow_execution": false
  }
}
```

Behavior rules:

- If release readiness is `ready`, final reviewer packet is `ready_for_review`, milestone is non-blocking, and optional followups are non-blocking, then closure status should be `closed_non_blocking` even if routine stability remains `watch`.
- If optional followups become blocking, status should not be closed.
- If release readiness is not ready, status should not be closed.
- Missing optional inputs should degrade conservatively with explicit reason fields rather than crashing.

### 2. Integrate into final reviewer packet

Update:

- `cajas/reports/validation_final_reviewer_packet.py`
- `cajas/scripts/build_validation_final_reviewer_packet.py`
- `cajas/tests/test_validation_final_reviewer_packet.py`

Add optional CLI/report input:

```bash
--routine-stability-watch-closure tmp/validation-routine-stability-watch-closure.json
```

Final reviewer packet should expose a compact summary:

- closure status
- blocking flag
- interpretation
- next action

It must remain `ready_for_review` when closure status is `closed_non_blocking`.

### 3. Integrate into release readiness

Update:

- `cajas/reports/validation_release_readiness.py`
- `cajas/scripts/build_validation_release_readiness_report.py`
- `cajas/tests/test_validation_release_readiness.py`

Add optional CLI/report input:

```bash
--routine-stability-watch-closure tmp/validation-routine-stability-watch-closure.json
```

Release readiness should remain `ready` when:

- routine stability status is `watch`, but
- routine stability watch closure is `closed_non_blocking`, and
- optional followups are non-blocking.

### 4. Integrate into milestone packet

Update:

- `cajas/reports/validation_milestone_packet.py`
- `cajas/scripts/build_validation_milestone_packet.py`
- `cajas/tests/test_validation_milestone_packet.py`

Add optional CLI/report input:

```bash
--routine-stability-watch-closure tmp/validation-routine-stability-watch-closure.json
```

Milestone may continue to show `overall_status=watch`, but it must clearly surface:

- `review_state=ready_for_review`
- `blocking=false`
- routine stability watch closure is non-blocking
- remaining followup is maintenance-only

### 5. Docs update

Update at least:

- `cajas/docs/current_qlib_base_stage_archive.md`
- `cajas/docs/dataset_quality_loop.md`
- `cajas/README.md`

Document:

- routine stability `watch` can be closed as non-blocking when release readiness and final reviewer packet are ready
- remaining slow-test optimization is routine maintenance only
- next release-cycle monitoring remains expected
- scope remains offline Qlib validation automation only

## Required validation

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_validation_routine_stability_watch_closure.py \
  cajas/tests/test_validation_final_reviewer_packet.py \
  cajas/tests/test_validation_release_readiness.py \
  cajas/tests/test_validation_milestone_packet.py
```

Run fast validation:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/fast_validation_latest.json
```

Run hygiene checks:

```bash
git diff --check
find cajas -path "*/init.py" -print
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Compile changed Python modules:

```bash
./.venv-qlib313/bin/python -m py_compile \
  cajas/reports/validation_routine_stability_watch_closure.py \
  cajas/scripts/build_validation_routine_stability_watch_closure.py \
  cajas/reports/validation_final_reviewer_packet.py \
  cajas/scripts/build_validation_final_reviewer_packet.py \
  cajas/reports/validation_release_readiness.py \
  cajas/scripts/build_validation_release_readiness_report.py \
  cajas/reports/validation_milestone_packet.py \
  cajas/scripts/build_validation_milestone_packet.py
```

## Commit guidance

Create small commits, for example:

```bash
git add \
  cajas/reports/validation_routine_stability_watch_closure.py \
  cajas/scripts/build_validation_routine_stability_watch_closure.py \
  cajas/tests/test_validation_routine_stability_watch_closure.py

git commit -m "feat: close routine stability watch semantics"

git add \
  cajas/reports/validation_final_reviewer_packet.py \
  cajas/scripts/build_validation_final_reviewer_packet.py \
  cajas/reports/validation_release_readiness.py \
  cajas/scripts/build_validation_release_readiness_report.py \
  cajas/reports/validation_milestone_packet.py \
  cajas/scripts/build_validation_milestone_packet.py \
  cajas/tests/test_validation_final_reviewer_packet.py \
  cajas/tests/test_validation_release_readiness.py \
  cajas/tests/test_validation_milestone_packet.py

git commit -m "test: integrate routine stability closure into readiness"

git add \
  cajas/docs/current_qlib_base_stage_archive.md \
  cajas/docs/dataset_quality_loop.md \
  cajas/README.md \
  tasks/phase_4646_4765_routine_stability_watch_closure_prompt.md

git commit -m "docs: document routine stability watch closure"
```

Do not push automatically unless requested. If code needs to be merged, ask the user to merge manually on GitHub.

## Completion report expected

Return a concise completion report with:

- branch
- commits
- files changed
- generated artifacts
- closure status
- release readiness status
- final reviewer packet status
- milestone status and blocking flag
- optional followup count and blocking flag
- validation results
- runtime comparison against Phase 4526–4645 fast validation baseline `63.45s`
- push status
- manual push command

