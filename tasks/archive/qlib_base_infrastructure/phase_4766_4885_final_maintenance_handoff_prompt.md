# Phase 4766–4885 — Final Maintenance Handoff and GitHub Manual Merge Readiness

## Context

You are working in the Qlib Base / qlib-cajas repository on branch:

`phase-post-merge-research-next`

The project is now in routine maintenance mode. Recent completed phases established:

- Release readiness is `ready`.
- Final reviewer packet is `ready_for_review`.
- Milestone packet may remain `overall_status=watch`, but this is governance / maintenance context only:
  - `review_state=ready_for_review`
  - `blocking=false`
- Alias post-removal closure is complete:
  - generated manifests use canonical `history`
  - `history_update` is not actively emitted
  - legacy read normalization remains preserved
- External consumer evidence closure is confirmed.
- Final maintenance archive closure is ready.
- Post-freeze handoff seal is sealed.
- Routine stability watch semantics are closed as non-blocking:
  - `validation-routine-stability-watch-closure` status is `closed_non_blocking`
- The only remaining optional follow-up is slow-test optimization, routine / non-blocking.

Important scope boundary:

- Offline Qlib validation automation only.
- Do not modify Qlib core.
- Do not introduce trading execution, broker routing, live/paper trading, annotation loops, or workflow/training execution.
- Do not perform automatic merge operations.
- If merge readiness is reached, prepare handoff instructions and ask the human user to merge manually on GitHub.

## Goal

Create a final maintenance handoff / GitHub manual merge readiness packet that gives reviewers a clean end-state summary and explicitly instructs that any code merge should be done manually by the user on GitHub.

This phase should not add new product behavior. It should only add a small, reviewer-friendly final handoff surface and wire it into the existing final reports.

## Required Work

### 1. Add final handoff report module

Create:

`cajas/reports/validation_final_maintenance_handoff.py`

The report should read existing generated artifacts where available and produce a compact JSON/Markdown summary with at least:

- `status`
  - expected happy path: `ready_for_manual_github_merge`
- `review_state`
  - expected happy path: `ready_for_review`
- `blocking`
  - expected happy path: `false`
- `manual_merge_required`
  - expected happy path: `true`
- `merge_method`
  - expected value: `manual_github`
- `branch`
  - expected value: `phase-post-merge-research-next`
- `release_readiness_status`
- `final_reviewer_packet_status`
- `milestone_review_state`
- `milestone_blocking`
- `routine_watch_closure_status`
- `post_freeze_handoff_seal_status`
- `final_archive_closure_status`
- `external_consumer_evidence_closure_status`
- `alias_post_removal_closure_status`
- `optional_followup_summary`
  - count
  - blocking
  - remaining active item names if available
- `scope_boundary`
  - no Qlib core changes
  - no trading execution
  - no broker routing
  - no live/paper trading
  - no training/workflow execution
- `human_actions`
  - review PR / branch on GitHub
  - verify final artifacts
  - merge manually on GitHub if acceptable
  - push is allowed, but no automated merge should be attempted by Codex

The module should be defensive:
- If an optional artifact is missing, report `missing` for that dependency rather than crashing.
- Missing optional follow-up details should not block release if release readiness and final reviewer packet are ready.
- Missing required readiness artifacts should result in a non-ready status.

Suggested status rules:
- `ready_for_manual_github_merge` when:
  - release readiness is `ready`
  - final reviewer packet is `ready_for_review`
  - milestone blocking is `false`
  - routine watch closure is `closed_non_blocking` or missing but non-blocking if release readiness is ready
  - post-freeze handoff seal is `sealed` or not applicable only if older artifact is missing and release readiness is ready
  - alias post-removal closure is `closed`
- `watch` when:
  - readiness is ready but some handoff context is incomplete/non-critical
- `blocked` when:
  - release readiness is not ready
  - final reviewer packet is not ready for review
  - milestone blocking is true

### 2. Add CLI builder

Create:

`cajas/scripts/build_validation_final_maintenance_handoff.py`

It should write:

- `tmp/validation-final-maintenance-handoff.json`
- `tmp/validation-final-maintenance-handoff.md`

Use the style of existing validation report builders.

CLI should support explicit input paths for relevant artifacts where consistent with the existing codebase, including at minimum:

- release readiness
- final reviewer packet
- milestone packet
- routine stability watch closure
- post-freeze handoff seal
- final maintenance archive closure
- external consumer evidence closure
- alias post-removal closure
- optional followups
- output JSON
- output Markdown

### 3. Add tests

Create:

`cajas/tests/test_validation_final_maintenance_handoff.py`

Cover at least:

1. Happy path:
   - release readiness ready
   - final reviewer packet ready_for_review
   - milestone blocking false
   - routine watch closure closed_non_blocking
   - handoff status becomes `ready_for_manual_github_merge`
   - `manual_merge_required=true`
   - `merge_method=manual_github`

2. Blocking path:
   - release readiness not ready or milestone blocking true
   - handoff status becomes `blocked`

3. Missing optional context:
   - optional followups or routine watch closure missing
   - release readiness still ready
   - report does not crash
   - status is `ready_for_manual_github_merge` or `watch`, but not `blocked`

4. Markdown output:
   - contains a clear line instructing manual GitHub merge
   - contains no instruction to run automated merge

### 4. Integrate into final reports

Extend these existing report modules/scripts to accept and summarize the final maintenance handoff report:

- `cajas/reports/validation_final_reviewer_packet.py`
- `cajas/scripts/build_validation_final_reviewer_packet.py`
- `cajas/reports/validation_release_readiness.py`
- `cajas/scripts/build_validation_release_readiness_report.py`
- `cajas/reports/validation_milestone_packet.py`
- `cajas/scripts/build_validation_milestone_packet.py`

Expected behavior:

- If handoff report is ready, final reviewer packet should surface:
  - `final_maintenance_handoff_status=ready_for_manual_github_merge`
  - `manual_merge_required=true`
  - `merge_method=manual_github`
- Release readiness should remain `ready` if existing gates are ready and handoff is ready/watch non-blocking.
- Milestone packet should remain:
  - `review_state=ready_for_review`
  - `blocking=false`
  - `overall_status=watch` is acceptable as long as it is explicitly non-blocking governance context.

Update relevant tests:

- `cajas/tests/test_validation_final_reviewer_packet.py`
- `cajas/tests/test_validation_release_readiness.py`
- `cajas/tests/test_validation_milestone_packet.py`

### 5. Documentation updates

Update:

- `cajas/docs/current_qlib_base_stage_archive.md`
- `cajas/docs/dataset_quality_loop.md`
- `cajas/README.md`

Document:

- final maintenance handoff status
- release readiness remains ready
- manual GitHub merge instruction
- remaining optional follow-up is routine/non-blocking slow-test optimization
- no automated merge should be performed by Codex/local scripts

### 6. Regenerate artifacts

Run the new handoff CLI and regenerate integrated reports:

Expected outputs:

- `tmp/validation-final-maintenance-handoff.json`
- `tmp/validation-final-maintenance-handoff.md`
- `tmp/validation-final-reviewer-packet.json`
- `tmp/validation-final-reviewer-packet.md`
- `tmp/validation-release-readiness.json`
- `tmp/validation-release-readiness.md`
- `tmp/validation-milestone-packet.json`
- `tmp/validation-milestone-packet.md`

### 7. Validation

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest   cajas/tests/test_validation_final_maintenance_handoff.py   cajas/tests/test_validation_final_reviewer_packet.py   cajas/tests/test_validation_release_readiness.py   cajas/tests/test_validation_milestone_packet.py
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

Run py_compile for changed Python modules.

## Commit Guidance

Create local commits, for example:

```bash
git add   cajas/reports/validation_final_maintenance_handoff.py   cajas/scripts/build_validation_final_maintenance_handoff.py   cajas/tests/test_validation_final_maintenance_handoff.py

git commit -m "feat: add final maintenance handoff report"

git add   cajas/reports/validation_final_reviewer_packet.py   cajas/scripts/build_validation_final_reviewer_packet.py   cajas/reports/validation_release_readiness.py   cajas/scripts/build_validation_release_readiness_report.py   cajas/reports/validation_milestone_packet.py   cajas/scripts/build_validation_milestone_packet.py   cajas/tests/test_validation_final_reviewer_packet.py   cajas/tests/test_validation_release_readiness.py   cajas/tests/test_validation_milestone_packet.py

git commit -m "test: integrate final maintenance handoff"

git add   cajas/docs/current_qlib_base_stage_archive.md   cajas/docs/dataset_quality_loop.md   cajas/README.md   tasks/phase_4766_4885_final_maintenance_handoff_prompt.md

git commit -m "docs: document manual merge handoff"
```

Do not run an automated merge.

If the branch is ready to merge, report:

```bash
git push origin phase-post-merge-research-next
```

Then tell the human user to merge manually on GitHub.

## Final Response Required

When finished, report:

- branch
- commits
- files changed
- generated artifacts
- final handoff status
- release readiness status
- final reviewer packet status
- milestone review_state/blocking
- optional followups status/count/blocking
- validation results
- runtime total and comparison against Phase 4646–4765 baseline `56.15s`
- push status
- manual GitHub merge instruction
- confirmation that no automated merge was performed
