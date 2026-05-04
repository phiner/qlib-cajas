# Phase 3926–4045 Prompt: Maintenance Governance Closure and Routine Release-Cycle Hardening

You are working in the Qlib Base / qlib-cajas repository on branch `phase-post-merge-research-next`.

## Current baseline

Phase 3806–3925 is complete. The project is in routine maintenance mode and ready for review.

Current confirmed state:

- `tmp/validation-maintenance-checklist.json`: `status=ready`, `mode=routine_maintenance`, `review_state=ready_for_review`, `recommended_cadence=next_release_cycle`.
- Routine command contract is frozen with 6 required commands and expected statuses.
- Canonical artifact count is 12.
- `tmp/validation-optional-followups.json`: `status=open`, `blocking=false`, `items=2`.
- `tmp/validation-final-reviewer-packet.json`: `status=ready_for_review`.
- `tmp/validation-release-readiness.json`: `status=ready`.
- `tmp/validation-milestone-packet.json`: `overall_status=watch`, `review_state=ready_for_review`, `blocking=false`.
- `tmp/alias-post-removal-closure.json`: `status=closed`.
- Review-bundle manifest is canonical-only: `history` present, `history_update` absent.
- Legacy read normalization remains preserved.
- Fast validation is healthy: about `52.503s`, `pytest_fast=48.625s`.
- Runtime budget, timing consistency, runtime edge, runtime release-cycle, runtime variance closure, data-source audit, and hygiene all pass.

Scope remains offline Qlib validation automation only. Do not add trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Goal

Close or better classify the remaining non-blocking maintenance governance surface while preserving ready-for-review status. The desired end state is that release readiness stays `ready`, final reviewer packet stays `ready_for_review`, and milestone `watch` is either clearly routine/non-blocking or transitions to a more explicit maintenance/ready classification if existing semantics allow it safely.

## Tasks

1. Inspect the current optional follow-up queue and maintenance checklist artifacts.
   - Identify the two optional follow-up items.
   - Confirm they are truly non-blocking.
   - Do not treat them as release blockers unless an actual validation artifact says they are blocking.

2. Add or refine a small maintenance governance closure report.
   - Suggested module: `cajas/reports/validation_maintenance_governance_closure.py`.
   - Suggested CLI: `cajas/scripts/build_validation_maintenance_governance_closure.py`.
   - Suggested outputs:
     - `tmp/validation-maintenance-governance-closure.json`
     - `tmp/validation-maintenance-governance-closure.md`
   - The report should read existing artifacts only where possible.
   - It should summarize:
     - maintenance checklist status;
     - optional follow-up queue status/count/blocking flag;
     - release readiness status;
     - milestone review state/blocking flag;
     - alias post-removal closure status;
     - runtime release-cycle / runtime variance closure status when available;
     - final conclusion: `routine`, `ready_for_review`, `watch_non_blocking`, or `blocked`.

3. Integrate the governance closure summary into existing review surfaces.
   - Final reviewer packet should include the governance closure status and conclusion.
   - Release readiness should include the governance closure status without downgrading `ready` when the closure is non-blocking.
   - Milestone packet should include the closure summary and make clear whether `overall_status=watch` is governance context only.

4. Add focused tests.
   - Test a fully ready/routine path.
   - Test optional followups open but non-blocking.
   - Test a blocking followup or missing critical artifact path if the existing framework supports it.
   - Test integration into final reviewer packet, release readiness, and milestone packet.

5. Regenerate artifacts.
   - Build the new governance closure report.
   - Rebuild final reviewer packet, release readiness, and milestone packet using the new report.
   - Keep generated artifacts in `tmp/` unless the project convention requires otherwise.

6. Run validation.
   - Run focused tests for new/changed modules.
   - Run related report tests.
   - Run fast validation.
   - Run runtime budget, timing consistency, runtime edge/release-cycle/variance closure checks if they are part of the maintenance contract.
   - Run data-source audit and hygiene checks.

7. Update docs.
   - Update `cajas/docs/current_qlib_base_stage_archive.md` with Phase 3926–4045 results.
   - Update `cajas/docs/dataset_quality_loop.md` or `cajas/README.md` only if the new governance closure surface changes reviewer handoff instructions.

## Constraints

- Keep all behavior offline and deterministic.
- Do not modify Qlib core.
- Do not reintroduce `history_update` producer emission.
- Do not remove legacy read normalization.
- Do not change active alias fallback removal semantics unless tests and existing reports explicitly justify it.
- Do not convert non-blocking optional followups into blockers.
- Prefer report-level summarization over new mutable workflow state.
- Keep changes small and reviewer-friendly.

## Expected final response

When finished, report:

- branch;
- commits;
- files changed;
- new artifacts generated;
- governance closure status/conclusion;
- release readiness status;
- milestone packet status/review_state/blocking flag;
- validation results;
- runtime comparison against Phase 3806–3925 baseline `52.503s`;
- remaining followups, if any;
- whether push was run.
