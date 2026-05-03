# Phase 3566–3685 Prompt: Runtime Variance Watch Closure and Reviewer Finalization Packet

You are working in the repository on branch `phase-post-merge-research-next`.

## Current Baseline

The active project mainline is **Microsoft Qlib / Qlib Base / qlib-cajas**, a Qlib-based offline research infrastructure validation effort.

Recent completed phase:

- Phase 3446–3565 completed runtime release-cycle warning semantics and final release-ready closure packet.
- Commits:
  - `6e376f6b` `fix: close runtime release-cycle warning semantics`
  - `ceffb3a1` `feat: add final release-ready closure packet`
  - `f4ca70c6` `test: integrate final release-ready closure into reports`
  - `1617eacd` `docs: document final release-ready closure`
- Runtime release-cycle final status:
  - `watch`
  - reason_code: `runtime_variance_watch`
  - blocking_gates: `[]`
  - watch_gates: `["runtime_variance_status=watch"]`
  - recommendation: `monitor`
- Release-ready closure:
  - `tmp/validation-release-ready-closure.json`
  - `tmp/validation-release-ready-closure.md`
  - status: `watch`
  - remaining_blockers: `[]`
  - remaining_followups: `["runtime_release_cycle_status=watch"]`
  - recommendation: `monitor_runtime_next_cycle`
- Release readiness:
  - status: `watch`
  - reason: `runtime_release_cycle_status=watch; runtime_variance_status=watch`
  - no blocking failure
- Milestone packet:
  - status: `watch`
- Alias post-removal closure:
  - status: `closed`
- Alias migration:
  - functionally closed for producer-side fallback removal and compatibility preservation
  - canonical-only manifest contract confirmed:
    - `history` present
    - `history_update` absent
  - legacy read normalization preserved
  - manifest compatibility remains `pass`
- Latest validation:
  - runtime release-cycle tests: `4 passed`
  - release-ready closure tests: `3 passed`
  - release readiness tests: `8 passed`
  - milestone packet tests: `11 passed`
  - alias post-removal closure tests: `2 passed`
  - related suite: `227 passed`, `319 deselected`
  - fast validation: `58.351s`, `pytest_fast=53.097s`
  - runtime budget: `pass`
  - timing consistency: `pass`
  - runtime edge: `pass`
  - data-source audit: `read_csv_count=29`
  - hygiene: pass

Current interpretation:

- Final release readiness is not blocked.
- Current status is ready-for-review with runtime monitoring follow-up.
- The only remaining watch is runtime variance watch.
- The next phase should either:
  1. reduce/close runtime variance watch if current run stabilizes, or
  2. formalize it as non-blocking cycle-monitoring state and produce a final reviewer packet.

## User Direction

The user wants faster progress and larger combined phases, but this should remain disciplined. Do not add broad new infrastructure unless it closes the release-readiness loop.

## Strict Scope Boundaries

This project is **offline Qlib research infrastructure validation only**.

Do not add or revive:

- Trading execution
- Broker adapters
- Order routing
- Position sizing
- Live trading
- Paper trading execution
- Old Rust trading system logic
- Manual K-line annotation
- Human-in-the-loop annotation
- ML label learning loop
- Production deployment logic
- Alpha/profit/Sharpe/model-performance claims

Do not modify Qlib core unless absolutely necessary. Prefer all work in `cajas/`.

Quality scores remain data quality indicators only.

## Phase Goal

Implement **Runtime Variance Watch Closure and Reviewer Finalization Packet**.

The goal is to turn the final state from “watch but not blocked” into a reviewer-friendly closure posture.

This phase should answer:

1. Is runtime variance watch still present after a fresh validation cycle?
2. Is runtime variance watch a blocker or a monitoring-only follow-up?
3. Can release readiness be represented as ready-for-review even if runtime monitoring remains watch?
4. Can the reviewer see one final packet summarizing canonical-only manifest, alias closure, runtime status, data-source audit, and remaining follow-ups?
5. What is the recommended maintenance cadence after this milestone?

## Required Work

### 1. Audit runtime variance watch

Inspect:

```bash
cat tmp/validation-runtime-variance-report.json
cat tmp/validation-runtime-release-cycle-report.json
cat tmp/validation-runtime-watch-triage-report.json
cat tmp/validation-release-ready-closure.json
cat tmp/fast_validation_latest.json
```

Classify runtime variance watch as:

- `closed` if fresh run is within pass thresholds
- `monitoring_only` if pass budget/edge/timing but variance watch remains
- `blocking` only if runtime budget/edge/timing fails

Do not force pass if current variance logic says watch. Instead, encode whether it is blocking or non-blocking.

### 2. Add runtime variance closure report

Create:

- `cajas/reports/validation_runtime_variance_closure.py`
- `cajas/scripts/build_validation_runtime_variance_closure_report.py`

Outputs:

```text
tmp/validation-runtime-variance-closure.json
tmp/validation-runtime-variance-closure.md
```

Suggested JSON:

```json
{
  "schema_version": "v1",
  "status": "closed|monitoring_only|blocked",
  "runtime_variance_status": "pass|watch|warn|fail",
  "runtime_release_cycle_status": "pass|watch|warn|fail",
  "runtime_budget_status": "pass",
  "runtime_edge_status": "pass",
  "timing_consistency_status": "pass",
  "blocking": false,
  "remaining_followup": "monitor_next_cycle",
  "recommended_cadence": "next_release_cycle",
  "reason_code": "variance_watch_non_blocking|variance_pass|runtime_blocked"
}
```

Rules:

- If budget/edge/timing fail => `blocked`
- If budget/edge/timing pass but variance/release-cycle watch => `monitoring_only`
- If all pass => `closed`
- Markdown should clearly say whether this blocks release readiness.

### 3. Update release-ready closure semantics

Update:

- `cajas/reports/validation_release_ready_closure.py`
- `cajas/scripts/build_validation_release_ready_closure.py`

Add optional input:

```bash
--runtime-variance-closure tmp/validation-runtime-variance-closure.json
```

Behavior:

- If no blockers and runtime variance closure is `monitoring_only`, final closure should be `ready_for_review` or `watch_non_blocking`, depending existing enum preference.
- If existing enum only supports `ready|watch|blocked`, use:
  - `status=watch`
  - `review_state=ready_for_review`
  - `blocking=false`
- Add fields:

```json
{
  "review_state": "ready_for_review|blocked|needs_monitoring",
  "blocking": false,
  "non_blocking_followups": [...],
  "ready_for_review": true
}
```

### 4. Add final reviewer packet

Create:

- `cajas/reports/validation_final_reviewer_packet.py`
- `cajas/scripts/build_validation_final_reviewer_packet.py`

Outputs:

```text
tmp/validation-final-reviewer-packet.json
tmp/validation-final-reviewer-packet.md
```

Inputs:

- release-ready closure
- alias post-removal closure
- runtime variance closure
- release readiness
- milestone packet
- review bundle manifest
- manifest compatibility report
- runtime budget
- runtime edge
- data-source audit

Suggested JSON:

```json
{
  "schema_version": "v1",
  "status": "ready_for_review|watch|blocked",
  "summary": {
    "canonical_only_manifest": true,
    "alias_post_removal_closure": "closed",
    "legacy_read_normalization_kept": true,
    "manifest_compatibility": "pass",
    "runtime_budget": "pass",
    "runtime_edge": "pass",
    "runtime_variance_closure": "monitoring_only",
    "data_source_audit_read_csv_count": 29
  },
  "remaining_followups": [
    "monitor runtime variance next release cycle"
  ],
  "primary_artifacts": [...],
  "rollback_readiness": "...",
  "non_goals": [...]
}
```

Markdown should be concise and reviewer-facing.

### 5. Integrate final reviewer packet into milestone packet and release readiness

Add optional input:

```bash
--final-reviewer-packet tmp/validation-final-reviewer-packet.json
```

For:

- `build_validation_release_readiness_report.py`
- `build_validation_milestone_packet.py`

Reports should include:

- final reviewer packet status
- primary artifact path
- remaining non-blocking followups

### 6. Optional slow-test note

If runtime variance closure remains monitoring_only, add a small optional note from pytest runtime profile:

- top slow tests/files
- not blocking
- next optimization candidate

Do not optimize unless there is a trivial safe fix. This phase is closure/reporting focused.

### 7. Tests

Add/update tests:

- `cajas/tests/test_validation_runtime_variance_closure.py`
- `cajas/tests/test_validation_release_ready_closure.py`
- `cajas/tests/test_validation_final_reviewer_packet.py`
- `cajas/tests/test_validation_release_readiness.py`
- `cajas/tests/test_validation_milestone_packet.py`

Cover:

- variance closure closed when all runtime gates pass
- variance closure monitoring_only when budget/edge pass but variance watch
- variance closure blocked when budget/edge fail
- release-ready closure ready_for_review when only monitoring_only remains
- final reviewer packet ready_for_review with non-blocking runtime followup
- final reviewer packet blocked on compatibility/runtime failure
- release readiness/milestone include final reviewer packet summary
- Markdown includes offline validation scope and non-goals

### 8. Regenerate artifacts

Runtime fresh run:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/fast_validation_latest.json
```

Runtime budget:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/check_validation_runtime_budget.py \
  --budgets cajas/data_examples/validation_runtime_budgets.json \
  --timing-json tmp/fast_validation_latest.json \
  --out-json tmp/validation_runtime_budget_report.json \
  --out-md tmp/validation_runtime_budget_report.md
```

Runtime edge:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_runtime_edge_report.py \
  --timing-json tmp/fast_validation_latest.json \
  --runtime-budget-report tmp/validation_runtime_budget_report.json \
  --out-json tmp/validation-runtime-edge-report.json \
  --out-md tmp/validation-runtime-edge-report.md
```

Runtime variance:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_runtime_variance_report.py \
  --fast-timing-json tmp/fast_validation_latest.json \
  --runtime-budget-report tmp/validation_runtime_budget_report.json \
  --runtime-edge-report tmp/validation-runtime-edge-report.json \
  --baseline-label phase_3326 --baseline-fast-total 56.96 \
  --baseline-label phase_3446 --baseline-fast-total 58.351 \
  --out-json tmp/validation-runtime-variance-report.json \
  --out-md tmp/validation-runtime-variance-report.md
```

Runtime watch triage:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_runtime_watch_triage_report.py \
  --fast-timing-json tmp/fast_validation_latest.json \
  --runtime-edge-report tmp/validation-runtime-edge-report.json \
  --runtime-variance-report tmp/validation-runtime-variance-report.json \
  --pytest-runtime-profile tmp/validation-pytest-runtime-profile.json \
  --baseline-label phase_3326 --baseline-fast-total 56.96 \
  --baseline-label phase_3446 --baseline-fast-total 58.351 \
  --out-json tmp/validation-runtime-watch-triage-report.json \
  --out-md tmp/validation-runtime-watch-triage-report.md
```

Runtime release-cycle:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_runtime_release_cycle_report.py \
  --runtime-edge-report tmp/validation-runtime-edge-report.json \
  --runtime-budget-report tmp/validation_runtime_budget_report.json \
  --fast-timing-json tmp/fast_validation_latest.json \
  --runtime-variance-report tmp/validation-runtime-variance-report.json \
  --runtime-watch-triage-report tmp/validation-runtime-watch-triage-report.json \
  --pytest-runtime-profile tmp/validation-pytest-runtime-profile.json \
  --out-json tmp/validation-runtime-release-cycle-report.json \
  --out-md tmp/validation-runtime-release-cycle-report.md
```

Runtime variance closure:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_runtime_variance_closure_report.py \
  --runtime-variance-report tmp/validation-runtime-variance-report.json \
  --runtime-release-cycle-report tmp/validation-runtime-release-cycle-report.json \
  --runtime-budget-report tmp/validation_runtime_budget_report.json \
  --runtime-edge-report tmp/validation-runtime-edge-report.json \
  --out-json tmp/validation-runtime-variance-closure.json \
  --out-md tmp/validation-runtime-variance-closure.md
```

Release-ready closure:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_release_ready_closure.py \
  --alias-post-removal-closure tmp/alias-post-removal-closure.json \
  --release-readiness-report tmp/validation-release-readiness.json \
  --milestone-packet tmp/validation-milestone-packet.json \
  --runtime-release-cycle-report tmp/validation-runtime-release-cycle-report.json \
  --runtime-budget-report tmp/validation_runtime_budget_report.json \
  --runtime-edge-report tmp/validation-runtime-edge-report.json \
  --runtime-variance-closure tmp/validation-runtime-variance-closure.json \
  --manifest-compatibility-report tmp/validation-review-bundle/manifest_compatibility_report.json \
  --data-source-audit-report tmp/data_source_audit.json \
  --review-bundle-manifest tmp/validation-review-bundle/review_bundle_manifest.json \
  --out-json tmp/validation-release-ready-closure.json \
  --out-md tmp/validation-release-ready-closure.md
```

Final reviewer packet:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_final_reviewer_packet.py \
  --release-ready-closure tmp/validation-release-ready-closure.json \
  --alias-post-removal-closure tmp/alias-post-removal-closure.json \
  --runtime-variance-closure tmp/validation-runtime-variance-closure.json \
  --release-readiness-report tmp/validation-release-readiness.json \
  --milestone-packet tmp/validation-milestone-packet.json \
  --review-bundle-manifest tmp/validation-review-bundle/review_bundle_manifest.json \
  --manifest-compatibility-report tmp/validation-review-bundle/manifest_compatibility_report.json \
  --runtime-budget-report tmp/validation_runtime_budget_report.json \
  --runtime-edge-report tmp/validation-runtime-edge-report.json \
  --data-source-audit-report tmp/data_source_audit.json \
  --out-json tmp/validation-final-reviewer-packet.json \
  --out-md tmp/validation-final-reviewer-packet.md
```

Rebuild release readiness with final reviewer packet:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_release_readiness_report.py \
  --milestone-packet tmp/validation-milestone-packet.json \
  --alias-sunset-review tmp/history-alias-sunset-review.json \
  --runtime-release-cycle-report tmp/validation-runtime-release-cycle-report.json \
  --runtime-variance-report tmp/validation-runtime-variance-report.json \
  --runtime-edge-report tmp/validation-runtime-edge-report.json \
  --runtime-budget-report tmp/validation_runtime_budget_report.json \
  --alias-removal-plan tmp/history-alias-removal-plan.json \
  --consumer-evidence-closure-report tmp/history-alias-consumer-evidence-closure.json \
  --consumer-owner-handoff tmp/history-alias-consumer-owner-handoff.json \
  --consumer-owner-response-validation tmp/history-alias-consumer-owner-response-validation.json \
  --consumer-evidence-candidate-report tmp/simulated-confirmed-clear/history-alias-consumer-evidence-candidate.json \
  --evidence-candidate-approval-report tmp/evidence-candidate-approval-report.json \
  --alias-sunset-schedule tmp/history-alias-sunset-schedule.json \
  --canonical-evidence-update-plan tmp/canonical-evidence-update-plan.json \
  --canonical-evidence-apply-report tmp/canonical-evidence-apply-dry-run.json \
  --applied-evidence-readiness tmp/applied-canonical-evidence/applied-evidence-readiness.json \
  --alias-fallback-removal-readiness tmp/alias-fallback-removal-readiness.json \
  --alias-post-removal-closure tmp/alias-post-removal-closure.json \
  --release-ready-closure tmp/validation-release-ready-closure.json \
  --final-reviewer-packet tmp/validation-final-reviewer-packet.json \
  --runtime-watch-triage-report tmp/validation-runtime-watch-triage-report.json \
  --pytest-runtime-profile tmp/validation-pytest-runtime-profile.json \
  --out-json tmp/validation-release-readiness.json \
  --out-md tmp/validation-release-readiness.md
```

Rebuild milestone packet with final reviewer packet:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_milestone_packet.py \
  --review-bundle-root tmp/validation-review-bundle \
  --alias-fallback-bundle-root tmp/validation-review-bundle-alias-fallback \
  --runtime-edge-report tmp/validation-runtime-edge-report.json \
  --migration-readiness-report tmp/history-alias-migration-readiness.json \
  --runtime-budget-report tmp/validation_runtime_budget_report.json \
  --data-source-audit-report tmp/data_source_audit.json \
  --fast-timing-json tmp/fast_validation_latest.json \
  --alias-sunset-review tmp/history-alias-sunset-review.json \
  --runtime-release-cycle-report tmp/validation-runtime-release-cycle-report.json \
  --runtime-variance-report tmp/validation-runtime-variance-report.json \
  --release-readiness-report tmp/validation-release-readiness.json \
  --alias-removal-plan tmp/history-alias-removal-plan.json \
  --consumer-evidence-closure-report tmp/history-alias-consumer-evidence-closure.json \
  --consumer-owner-handoff tmp/history-alias-consumer-owner-handoff.json \
  --consumer-owner-response-validation tmp/history-alias-consumer-owner-response-validation.json \
  --consumer-evidence-candidate-report tmp/simulated-confirmed-clear/history-alias-consumer-evidence-candidate.json \
  --evidence-candidate-approval-report tmp/evidence-candidate-approval-report.json \
  --alias-sunset-schedule tmp/history-alias-sunset-schedule.json \
  --canonical-evidence-update-plan tmp/canonical-evidence-update-plan.json \
  --canonical-evidence-apply-report tmp/canonical-evidence-apply-dry-run.json \
  --applied-evidence-readiness tmp/applied-canonical-evidence/applied-evidence-readiness.json \
  --alias-fallback-removal-readiness tmp/alias-fallback-removal-readiness.json \
  --alias-post-removal-closure tmp/alias-post-removal-closure.json \
  --release-ready-closure tmp/validation-release-ready-closure.json \
  --final-reviewer-packet tmp/validation-final-reviewer-packet.json \
  --runtime-watch-triage-report tmp/validation-runtime-watch-triage-report.json \
  --pytest-runtime-profile tmp/validation-pytest-runtime-profile.json \
  --out-json tmp/validation-milestone-packet.json \
  --out-md tmp/validation-milestone-packet.md
```

### 9. Validation

Focused tests:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_runtime_variance_closure.py -q
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_release_ready_closure.py -q
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_final_reviewer_packet.py -q
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_release_readiness.py -q
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_milestone_packet.py -q
```

Related tests:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests -k "dataset_quality or qlib_experiment_manifest or validation_runtime_budget or reviewer_report_diff or validation_delivery_packet or validation_review_bundle or validation_gate_summary or validation_profile_matrix or validation_history_alias_migration or validation_runtime_edge or validation_milestone_packet or validation_alias_sunset_review or validation_runtime_release_cycle or validation_runtime_variance or validation_runtime_variance_closure or validation_release_readiness or validation_release_ready_closure or validation_final_reviewer_packet or validation_alias_removal_plan or validation_consumer_evidence_closure or validation_consumer_owner_handoff or validation_consumer_owner_response or validation_consumer_evidence_candidate or validation_evidence_candidate_approval or validation_alias_sunset_schedule or validation_canonical_evidence_update_plan or validation_canonical_evidence_apply or validation_applied_evidence_readiness or validation_alias_fallback_removal_readiness or validation_alias_post_removal_closure or validation_runtime_watch_triage or validation_runners or validation_pytest_runtime_profile" -q
```

Fast validation and hygiene:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/fast_validation_latest.json

PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/check_validation_runtime_budget.py \
  --budgets cajas/data_examples/validation_runtime_budgets.json \
  --timing-json tmp/fast_validation_latest.json \
  --out-json tmp/validation_runtime_budget_report.json \
  --out-md tmp/validation_runtime_budget_report.md

./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py \
  --project-root cajas \
  --data-root /tmp/nonexistent-data-root-for-static-audit \
  --out-json tmp/data_source_audit.json \
  --out-md tmp/data_source_audit.md

git diff --check
find cajas -path "*/init.py"
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

### 10. Documentation updates

Update:

- `cajas/docs/dataset_quality_loop.md`
- `cajas/README.md`
- `cajas/docs/current_qlib_base_stage_archive.md`

Add Phase 3566–3685 section explaining:

- runtime variance closure classification
- ready-for-review vs blocked semantics
- final reviewer packet
- alias migration closure status
- runtime monitoring follow-up
- validation results
- maintenance cadence
- explicit non-goals

### 11. Commit plan

Suggested commits:

```bash
git add cajas/reports/validation_runtime_variance_closure.py \
        cajas/scripts/build_validation_runtime_variance_closure_report.py \
        cajas/tests/test_validation_runtime_variance_closure.py
git commit -m "feat: add runtime variance closure report"

git add cajas/reports/validation_release_ready_closure.py \
        cajas/scripts/build_validation_release_ready_closure.py \
        cajas/tests/test_validation_release_ready_closure.py
git commit -m "fix: mark non-blocking runtime variance followup"

git add cajas/reports/validation_final_reviewer_packet.py \
        cajas/scripts/build_validation_final_reviewer_packet.py \
        cajas/tests/test_validation_final_reviewer_packet.py
git commit -m "feat: add final reviewer packet"

git add cajas/reports/validation_release_readiness.py \
        cajas/scripts/build_validation_release_readiness_report.py \
        cajas/reports/validation_milestone_packet.py \
        cajas/scripts/build_validation_milestone_packet.py \
        cajas/tests/test_validation_release_readiness.py \
        cajas/tests/test_validation_milestone_packet.py
git commit -m "test: integrate final reviewer packet into readiness reports"

git add cajas/docs/dataset_quality_loop.md cajas/README.md cajas/docs/current_qlib_base_stage_archive.md
git commit -m "docs: document runtime variance closure and final review packet"
```

## Final Response Required

At the end, provide a compact summary with:

- branch
- commits
- changed files
- runtime variance closure behavior
- release-ready closure final behavior
- final reviewer packet behavior
- release readiness/milestone final status
- alias migration closure status
- canonical-only/legacy normalization confirmation
- validation results with runtimes
- variance closure output paths
- final reviewer packet output paths
- release readiness output paths
- milestone packet output paths
- runtime budget status and timing consistency status
- data-source audit count
- fast validation runtime compared to:
  - Phase 3446 baseline: ~58.351s
  - Phase 3326 baseline: ~56.96s
- recommendation on ready-for-review
- remaining follow-ups
- maintenance cadence
- scope confirmation
- risks/limitations
- manual push command

Do not include old Rust trading, kline-labeler, manual annotation, human-in-the-loop, or broker execution as active work.
