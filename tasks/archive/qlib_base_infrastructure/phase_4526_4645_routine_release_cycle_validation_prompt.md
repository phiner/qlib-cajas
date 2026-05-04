# Phase 4526–4645 — Routine Release-Cycle Validation and Maintenance Stability

You are Codex working in the Qlib Base / `qlib-cajas` repository.

## Branch

Continue on:

```bash
git checkout phase-post-merge-research-next
```

## Current baseline

The project is in routine maintenance mode after the combined front-work closure phase.

Known completed state:

- External consumer evidence closure implemented and validated.
- Final maintenance archive closure implemented and validated.
- Post-freeze handoff seal implemented and validated.
- Final reviewer packet, release readiness, and milestone packet integrate the closure reports.
- Optional followup transition behavior is implemented and non-blocking.
- Artifacts are expected to be in `ready` / `ready_for_review` / non-blocking milestone watch context.
- Focused validation suite plus fast/hygiene checks passed.
- The prior local commit blocker was resolved by the user.

Scope remains unchanged:

- Offline Qlib validation automation only.
- No trading execution.
- No broker routing.
- No live or paper trading.
- No annotation loops.
- No Qlib core modifications.

## Goal

Perform a routine next-release-cycle validation pass and produce a compact maintenance stability packet proving that the project remains review-ready after the closure work.

This phase should avoid new architectural expansion. Prefer small, conservative verification/reporting changes only.

## Required work

### 1. Add a routine release-cycle stability report

Create:

- `cajas/reports/validation_routine_release_cycle_stability.py`
- `cajas/scripts/build_validation_routine_release_cycle_stability.py`
- `cajas/tests/test_validation_routine_release_cycle_stability.py`

The report should read existing regenerated artifacts and summarize:

- release readiness status
- final reviewer packet status
- milestone packet review state / blocking flag
- maintenance checklist status, if available
- maintenance governance closure status, if available
- final maintenance archive closure status, if available
- external consumer evidence closure status, if available
- post-freeze handoff seal status, if available
- runtime budget / timing consistency / runtime edge / release-cycle / variance closure status, if available
- data-source audit read_csv count, if available
- path hygiene status, if available
- optional followup status/count/blocking flag, if available

Expected top-level output fields:

```json
{
  "schema_version": 1,
  "status": "stable",
  "review_state": "ready_for_review",
  "blocking": false,
  "recommended_cadence": "next_release_cycle",
  "summary": {...},
  "checks": [...],
  "remaining_followups": [...],
  "next_actions": [...]
}
```

Status rules:

- `stable` if release readiness is ready, final reviewer packet is ready_for_review, milestone is non-blocking, closure reports are ready/closed/sealed as applicable, and runtime gates are pass/closed/healthy.
- `watch` if only non-blocking optional followups remain.
- `blocked` if any required readiness/closure/runtime gate is failing or explicitly blocking.

The markdown output should be short and reviewer-friendly.

### 2. Integrate the stability report

Add optional inputs and summaries for the new stability report to:

- `cajas/reports/validation_final_reviewer_packet.py`
- `cajas/scripts/build_validation_final_reviewer_packet.py`
- `cajas/reports/validation_release_readiness.py`
- `cajas/scripts/build_validation_release_readiness_report.py`
- `cajas/reports/validation_milestone_packet.py`
- `cajas/scripts/build_validation_milestone_packet.py`

Expected behavior:

- If stability status is `stable`, final reviewer packet remains `ready_for_review`.
- If stability status is `watch`, release readiness may remain ready only when `blocking=false`.
- If stability status is `blocked`, release readiness must not be `ready`.
- Milestone packet may retain non-blocking `watch` context, but must surface `blocking=false` and `review_state=ready_for_review` when appropriate.

Update tests for those integrations.

### 3. Regenerate artifacts

Regenerate the relevant artifact set, including at minimum:

- `tmp/validation-routine-release-cycle-stability.json`
- `tmp/validation-routine-release-cycle-stability.md`
- `tmp/validation-final-reviewer-packet.json`
- `tmp/validation-final-reviewer-packet.md`
- `tmp/validation-release-readiness.json`
- `tmp/validation-release-readiness.md`
- `tmp/validation-milestone-packet.json`
- `tmp/validation-milestone-packet.md`

Also regenerate any upstream artifacts required by the repo’s existing command contract.

### 4. Update docs

Update:

- `cajas/docs/current_qlib_base_stage_archive.md`
- `cajas/docs/dataset_quality_loop.md`
- `cajas/README.md` if it already references maintenance/release-cycle packets

Document:

- routine release-cycle stability status
- final review-ready state
- remaining followups, if any, as non-blocking
- command list for the next maintenance cycle

### 5. Validation

Run focused tests for new and changed modules.

Then run the repository’s current fast validation and hygiene commands, including the established maintenance command contract where available.

At minimum, run equivalents of:

```bash
python -m pytest cajas/tests/test_validation_routine_release_cycle_stability.py
python -m pytest cajas/tests/test_validation_final_reviewer_packet.py cajas/tests/test_validation_release_readiness.py cajas/tests/test_validation_milestone_packet.py
python cajas/scripts/run_fast_validation.py
python cajas/scripts/check_path_hygiene.py
git diff --check
find cajas -path "*/init.py" -print
```

If the repo has a frozen maintenance checklist command contract, run the exact commands from that checklist and report statuses.

## Commit plan

Create small commits, for example:

```bash
git add cajas/reports/validation_routine_release_cycle_stability.py \
        cajas/scripts/build_validation_routine_release_cycle_stability.py \
        cajas/tests/test_validation_routine_release_cycle_stability.py

git commit -m "feat: add routine release-cycle stability report"

git add cajas/reports/validation_final_reviewer_packet.py \
        cajas/scripts/build_validation_final_reviewer_packet.py \
        cajas/reports/validation_release_readiness.py \
        cajas/scripts/build_validation_release_readiness_report.py \
        cajas/reports/validation_milestone_packet.py \
        cajas/scripts/build_validation_milestone_packet.py \
        cajas/tests/test_validation_final_reviewer_packet.py \
        cajas/tests/test_validation_release_readiness.py \
        cajas/tests/test_validation_milestone_packet.py

git commit -m "test: integrate release-cycle stability into readiness reports"

git add cajas/docs/current_qlib_base_stage_archive.md \
        cajas/docs/dataset_quality_loop.md \
        cajas/README.md \
        tasks/phase_4526_4645_routine_release_cycle_validation_prompt.md

git commit -m "docs: document routine release-cycle stability"
```

Do not push unless explicitly requested.

## Final response required

Return a compact completion audit with:

- branch
- commits
- files changed
- generated artifacts
- stability status
- release readiness status
- final reviewer packet status
- milestone review state/blocking flag
- optional followups status/count/blocking flag
- validation results with timings
- runtime comparison against the previous baseline if available
- push status
- remaining risks or followups

