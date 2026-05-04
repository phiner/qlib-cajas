# Phase 4886–5005 — Post-Merge Mainline Validation and Maintenance Baseline Freeze

## Context

The branch `phase-post-merge-research-next` has been pushed to GitHub and manually merged into `main`.

The pre-merge final handoff status was:

- final maintenance handoff: `ready_for_manual_github_merge`
- release readiness: `ready`
- final reviewer packet: `ready_for_review`
- milestone packet: `overall_status=watch`, `review_state=ready_for_review`, `blocking=false`
- routine stability watch closure: `closed_non_blocking`
- optional followups: `count=1`, `blocking=false`
- remaining active optional followup: slow-test optimization only, routine / non-blocking
- fast validation baseline: `54.60s`
- merge method: manual GitHub merge only

Important scope boundary:

- Offline Qlib validation automation only.
- Do not modify Qlib core.
- Do not introduce trading execution, broker routing, live/paper trading, annotation loops, or workflow/training execution.
- Do not perform automated merge operations.

## Goal

Validate that the manually merged `main` branch preserves the final ready-for-review maintenance state, regenerate the canonical post-merge artifacts, and freeze a clean mainline maintenance baseline.

This phase should be small and conservative. It should focus on verification and documentation, not new behavior.

## Required Work

### 1. Checkout and verify main

Run:

```bash
git checkout main
git pull origin main
git status --short
git log --oneline -n 12
```

Confirm that the Phase 4766–4885 commits are present on `main`:

- `2bb6ba6f` `feat: add final maintenance handoff report`
- `b3bd33ab` `test: integrate final maintenance handoff`
- `336528c8` `docs: document manual merge handoff`

If GitHub merge created a merge commit or squash commit, record the actual mainline commit hash(es) instead of requiring exact hashes.

### 2. Regenerate final mainline artifacts

On `main`, regenerate:

- `tmp/validation-final-maintenance-handoff.json`
- `tmp/validation-final-maintenance-handoff.md`
- `tmp/validation-final-reviewer-packet.json`
- `tmp/validation-final-reviewer-packet.md`
- `tmp/validation-release-readiness.json`
- `tmp/validation-release-readiness.md`
- `tmp/validation-milestone-packet.json`
- `tmp/validation-milestone-packet.md`
- `tmp/validation-routine-stability-watch-closure.json`
- `tmp/validation-routine-stability-watch-closure.md`
- `tmp/validation-optional-followups.json`
- `tmp/validation-optional-followups.md`

Use existing builders and current artifact inputs.

Expected post-merge state:

- handoff status: `ready_for_manual_github_merge` or a mainline-specific equivalent such as `merged_ready_for_maintenance`
- release readiness: `ready`
- final reviewer packet: `ready_for_review`
- milestone:
  - `review_state=ready_for_review`
  - `blocking=false`
  - `overall_status=watch` is acceptable only as non-blocking governance context
- routine watch closure: `closed_non_blocking`
- optional followups:
  - `count=1`
  - `blocking=false`

### 3. Add post-merge mainline validation report

Create:

`cajas/reports/validation_post_merge_mainline.py`

The report should summarize:

- `status`
  - expected happy path: `mainline_validated`
- `branch`
  - expected: `main`
- `source_branch`
  - expected: `phase-post-merge-research-next`
- `merge_confirmed`
  - boolean
- `release_readiness_status`
- `final_reviewer_packet_status`
- `final_maintenance_handoff_status`
- `milestone_review_state`
- `milestone_blocking`
- `routine_watch_closure_status`
- `optional_followup_count`
- `optional_followup_blocking`
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
- `validation_summary`
  - focused tests
  - fast validation runtime
  - hygiene checks
- `post_merge_action`
  - expected: `continue_routine_maintenance`

Status rules:

- `mainline_validated` if:
  - release readiness is `ready`
  - final reviewer packet is `ready_for_review`
  - milestone blocking is false
  - optional followups are non-blocking
  - canonical-only manifest compatibility remains intact
- `watch` if:
  - readiness is ready but some non-critical context artifact is missing
- `blocked` if:
  - release readiness is not ready
  - milestone blocking is true
  - canonical-only manifest contract is broken

### 4. Add CLI builder

Create:

`cajas/scripts/build_validation_post_merge_mainline.py`

It should write:

- `tmp/validation-post-merge-mainline.json`
- `tmp/validation-post-merge-mainline.md`

CLI should accept explicit input paths for:

- release readiness
- final reviewer packet
- final maintenance handoff
- milestone packet
- routine stability watch closure
- optional followups
- alias post-removal closure / manifest compatibility artifact if used by existing reports
- fast validation timing JSON
- output JSON
- output Markdown

### 5. Add tests

Create:

`cajas/tests/test_validation_post_merge_mainline.py`

Cover at least:

1. Happy path:
   - release readiness ready
   - final reviewer packet ready_for_review
   - milestone blocking false
   - optional followups non-blocking
   - canonical manifest status intact
   - status `mainline_validated`

2. Blocking path:
   - milestone blocking true or release readiness not ready
   - status `blocked`

3. Watch path:
   - optional context missing but readiness still ready
   - status `watch` rather than crashing

4. Markdown output:
   - clearly states mainline validated / continue routine maintenance
   - does not instruct automated merge

### 6. Integrate post-merge report into docs only

Do not add another required gate to release readiness unless the existing report architecture clearly supports it without circular dependency.

Update docs:

- `cajas/docs/current_qlib_base_stage_archive.md`
- `cajas/docs/dataset_quality_loop.md`
- `cajas/README.md`

Document:

- `main` has absorbed the final maintenance handoff work
- post-merge mainline validation status
- release readiness remains ready
- remaining optional followup is routine/non-blocking slow-test optimization
- future work should use routine maintenance cadence
- no automated merge was performed

### 7. Validation

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest   cajas/tests/test_validation_post_merge_mainline.py   cajas/tests/test_validation_final_maintenance_handoff.py   cajas/tests/test_validation_final_reviewer_packet.py   cajas/tests/test_validation_release_readiness.py   cajas/tests/test_validation_milestone_packet.py
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

### 8. Commit guidance

Create commits on `main` only if the project policy allows small post-merge documentation/report commits directly on main. If direct commits to main are not allowed, create a new small branch such as:

`phase-post-merge-mainline-validation`

Recommended commits if committing directly or on a new branch:

```bash
git add   cajas/reports/validation_post_merge_mainline.py   cajas/scripts/build_validation_post_merge_mainline.py   cajas/tests/test_validation_post_merge_mainline.py

git commit -m "feat: add post-merge mainline validation report"

git add   cajas/docs/current_qlib_base_stage_archive.md   cajas/docs/dataset_quality_loop.md   cajas/README.md   tasks/phase_4886_5005_post_merge_mainline_validation_prompt.md

git commit -m "docs: freeze post-merge maintenance baseline"
```

Do not perform automated merge operations.

If a new branch is created, push it and ask the human user to merge manually on GitHub.

## Final Response Required

When finished, report:

- active branch
- whether Phase 4766–4885 commits are present on main
- commits created in this phase, if any
- files changed
- generated artifacts
- post-merge mainline status
- release readiness status
- final reviewer packet status
- final maintenance handoff status
- milestone review_state/blocking
- optional followups count/blocking
- canonical manifest compatibility status
- validation results
- fast validation runtime and comparison against pre-merge baseline `54.60s`
- push status
- whether manual GitHub merge is needed for any new branch
