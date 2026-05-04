# Phase 5006–5125 — Routine Maintenance Baseline Continuation

## Context

The project is Qlib Base / qlib-cajas.

Current repository posture:

- Keep the current GitHub fork relationship from `microsoft/qlib`.
- Do not remove the fork relationship.
- Do not migrate to a new independent repository.
- Do not sync from upstream unless explicitly requested in a future phase.
- Continue treating this project as Qlib-based offline research / validation infrastructure, not Qlib core and not a trading execution system.

Current mainline status after the completed post-merge validation:

- `phase-post-merge-research-next` was manually merged to `main`.
- `phase-post-merge-mainline-validation` was also manually merged to `main`.
- Post-merge mainline status was `mainline_validated`.
- Release readiness was `ready`.
- Final reviewer packet was `ready_for_review`.
- Milestone review state was `ready_for_review`, `blocking=false`.
- Optional followups count was `1`, `blocking=false`.
- Canonical manifest compatibility was OK:
  - `history_present=true`
  - `history_update_absent=true`
  - `legacy_read_normalization_kept=true`

Important scope boundary:

- Offline Qlib validation automation only.
- Do not modify Qlib core.
- Do not introduce trading execution, broker routing, live/paper trading, annotation loops, live data workflows, or training/workflow execution.
- Do not perform automated merge operations.
- Any merge to `main` must be done manually by the human user on GitHub.

## Goal

Create a small routine maintenance continuation report that freezes the current repository posture and confirms that the project can continue in maintenance mode without upstream sync or fork removal.

This phase should be conservative. It should not introduce new product behavior.

## Required Work

### 1. Add routine maintenance continuation report

Create:

`cajas/reports/validation_routine_maintenance_continuation.py`

The report should read existing generated artifacts where available and produce a compact JSON/Markdown summary with at least:

- `status`
  - expected happy path: `routine_continues`
- `review_state`
  - expected: `ready_for_review`
- `blocking`
  - expected: `false`
- `repo_posture`
  - `fork_relationship`: `kept`
  - `upstream_sync_planned`: `false`
  - `repo_migration_planned`: `false`
  - `manual_merge_policy`: `github_only`
- `mainline_validation_status`
- `release_readiness_status`
- `final_reviewer_packet_status`
- `milestone_review_state`
- `milestone_blocking`
- `optional_followup_count`
- `optional_followup_blocking`
- `remaining_optional_followups`
- `canonical_manifest_status`
  - `history_present`
  - `history_update_absent`
  - `legacy_read_normalization_kept`
- `scope_boundary`
  - no Qlib core changes
  - no trading execution
  - no broker routing
  - no live/paper trading
  - no training/workflow execution
  - no upstream sync in this phase
  - no repo migration in this phase
- `next_cadence`
  - expected: `routine_next_release_cycle`
- `recommended_next_actions`
  - monitor routine validation runtime
  - keep optional slow-test optimization non-blocking
  - only evaluate upstream sync in a dedicated future audit branch if explicitly requested

Status rules:

- `routine_continues` if:
  - release readiness is `ready`
  - final reviewer packet is `ready_for_review`
  - milestone blocking is false
  - optional followups are non-blocking
  - canonical manifest compatibility remains intact
- `watch` if:
  - readiness is ready but some non-critical context artifact is missing
- `blocked` if:
  - release readiness is not ready
  - milestone blocking is true
  - canonical manifest contract is broken

The module should be defensive:
- Missing optional artifacts should not crash.
- Missing required readiness artifacts should produce `watch` or `blocked` based on severity.
- Do not require upstream remote availability.

### 2. Add CLI builder

Create:

`cajas/scripts/build_validation_routine_maintenance_continuation.py`

It should write:

- `tmp/validation-routine-maintenance-continuation.json`
- `tmp/validation-routine-maintenance-continuation.md`

CLI should accept explicit input paths for:

- post-merge mainline validation report
- release readiness
- final reviewer packet
- milestone packet
- optional followups
- alias post-removal closure / manifest compatibility source if used by existing reports
- output JSON
- output Markdown

### 3. Add tests

Create:

`cajas/tests/test_validation_routine_maintenance_continuation.py`

Cover at least:

1. Happy path:
   - post-merge mainline status `mainline_validated`
   - release readiness `ready`
   - final reviewer packet `ready_for_review`
   - milestone blocking false
   - optional followups non-blocking
   - canonical manifest compatibility intact
   - status `routine_continues`

2. Repo posture:
   - report records fork kept
   - upstream sync planned false
   - repo migration planned false
   - manual merge policy GitHub only

3. Blocking path:
   - milestone blocking true or release readiness not ready
   - status `blocked`

4. Missing optional context:
   - optional followups missing
   - no crash
   - status `routine_continues` or `watch`, not `blocked`, when readiness is otherwise ready

5. Markdown output:
   - states routine maintenance continues
   - states fork relationship is kept
   - states no upstream sync in this phase
   - states no automated merge

### 4. Integrate into docs only

Do not add this as a required gate to release readiness unless the existing architecture clearly supports it without circular dependency.

Update docs:

- `cajas/docs/current_qlib_base_stage_archive.md`
- `cajas/docs/dataset_quality_loop.md`
- `cajas/README.md`

Document:

- fork relationship is intentionally kept for now
- no upstream sync is planned in the current maintenance cycle
- upstream sync should only happen in a dedicated future audit branch if explicitly requested
- release readiness remains ready
- mainline validation remains validated
- remaining optional followup is slow-test optimization, routine/non-blocking
- manual GitHub merge policy remains in effect

### 5. Regenerate artifacts

Run existing builders as needed, then run the new builder.

Expected new outputs:

- `tmp/validation-routine-maintenance-continuation.json`
- `tmp/validation-routine-maintenance-continuation.md`

Also ensure current canonical artifacts remain valid, especially:

- `tmp/validation-post-merge-mainline.json`
- `tmp/validation-release-readiness.json`
- `tmp/validation-final-reviewer-packet.json`
- `tmp/validation-milestone-packet.json`
- `tmp/validation-optional-followups.json`

### 6. Validation

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest   cajas/tests/test_validation_routine_maintenance_continuation.py   cajas/tests/test_validation_post_merge_mainline.py   cajas/tests/test_validation_final_reviewer_packet.py   cajas/tests/test_validation_release_readiness.py   cajas/tests/test_validation_milestone_packet.py
```

Run fast validation:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/fast_validation_latest.json
```

Run hygiene:

```bash
git diff --check
find cajas -path "*/init.py" -print
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Run py_compile for changed Python modules.

## Commit Guidance

Create a new branch from latest `main` unless already on a dedicated branch:

```bash
git checkout main
git pull origin main
git checkout -b phase-routine-maintenance-continuation
```

Suggested commits:

```bash
git add   cajas/reports/validation_routine_maintenance_continuation.py   cajas/scripts/build_validation_routine_maintenance_continuation.py   cajas/tests/test_validation_routine_maintenance_continuation.py

git commit -m "feat: add routine maintenance continuation report"

git add   cajas/docs/current_qlib_base_stage_archive.md   cajas/docs/dataset_quality_loop.md   cajas/README.md   tasks/phase_5006_5125_routine_maintenance_continuation_prompt.md

git commit -m "docs: document routine maintenance continuation"
```

Do not perform automated merge operations.

If ready, push the branch and tell the human user to merge manually on GitHub:

```bash
git push origin phase-routine-maintenance-continuation
```

## Final Response Required

When finished, report:

- active branch
- commits created
- files changed
- generated artifacts
- routine maintenance continuation status
- repo posture:
  - fork kept
  - upstream sync planned false
  - repo migration planned false
- release readiness status
- post-merge mainline status
- final reviewer packet status
- milestone review_state/blocking
- optional followups count/blocking
- canonical manifest compatibility status
- validation results
- fast validation runtime
- push status
- manual GitHub merge instruction if a new branch was created
- confirmation that no automated merge was performed
