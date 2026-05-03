# Phase 3806–3925 Prompt: Maintenance Mode Hardening and Release-Cycle Checklist Freeze

You are working in the repository on branch `phase-post-merge-research-next`.

## Current Baseline

The active project mainline is **Microsoft Qlib / Qlib Base / qlib-cajas**, a Qlib-based offline research infrastructure validation effort.

Recent completed phase:

- Phase 3686–3805 implemented milestone watch governance closure and stable maintenance cadence.
- Local commits:
  - `b9ce7c68` `fix: clarify milestone ready-for-review semantics`
  - `62d3a6c8` `feat: add validation maintenance cadence report`
  - `ec491e6a` `test: add final reviewer maintenance handoff`
  - `63f45a5e` `test: integrate maintenance cadence into release readiness`
  - `7a90c783` `docs: document maintenance cadence and final handoff`
- Milestone packet:
  - `overall_status=watch`
  - `review_state=ready_for_review`
  - `blocking=false`
  - `blocking_reasons=[]`
  - `superseded_watch_items` populated
  - `maintenance_cadence=next_release_cycle`
- Maintenance cadence:
  - `tmp/validation-maintenance-cadence.json`
  - status: `routine`
  - recommended_cadence: `next_release_cycle`
  - routine_commands: `6`
  - watch_items: `[]`
- Final reviewer packet:
  - `tmp/validation-final-reviewer-packet.json`
  - status: `ready_for_review`
  - includes cadence summary and reviewer handoff section
  - remaining_followups: `[]`
- Release readiness:
  - `tmp/validation-release-readiness.json`
  - status: `ready`
- Alias migration:
  - alias post-removal closure status: `closed`
  - canonical-only manifest confirmed:
    - `history` present
    - `history_update` absent
  - legacy read normalization kept
- Validation:
  - focused suites: `26 passed`
  - related suite: `237 passed`, `319 deselected`
  - fast validation: about `54.733s`
  - pytest_fast: about `50.813s`
  - runtime budget: `pass`
  - timing consistency: `pass`
  - runtime edge: `pass`
  - runtime release-cycle: `pass`
  - runtime variance closure: `closed`
  - data-source audit: `read_csv_count=29`
  - hygiene: pass
- Current recommendation:
  - ready for review
  - routine maintenance mode
- Remaining optional follow-ups:
  - external consumer ownership/evidence completion for alias sunset governance trail
  - optional slow-test optimization from pytest profile warnings

Current interpretation:

- The project is no longer in active feature-expansion mode.
- The system is review-ready and should now be hardened for repeatable release-cycle maintenance.
- Next work should freeze the routine checklist, artifact contract, and optional follow-up queue.

## User Direction

The user wants larger phases, but now the project has reached ready-for-review. Avoid new broad feature expansion. Focus on maintenance-mode hardening and reviewer/operator clarity.

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

Implement **Maintenance Mode Hardening and Release-Cycle Checklist Freeze**.

The goal is to turn the ready-for-review state into a stable maintenance workflow that a reviewer/operator can repeat each release cycle.

This phase should answer:

1. What exact commands should be run every routine release cycle?
2. Which artifacts are canonical and should be frozen as the review bundle surface?
3. Which warnings are blocking vs non-blocking in maintenance mode?
4. What optional follow-ups remain outside release readiness?
5. What rollback/compatibility guarantees must remain?
6. Can a single maintenance checklist packet summarize all of the above?

## Required Work

### 1. Add maintenance checklist packet

Create:

- `cajas/reports/validation_maintenance_checklist.py`
- `cajas/scripts/build_validation_maintenance_checklist.py`

Outputs:

```text
tmp/validation-maintenance-checklist.json
tmp/validation-maintenance-checklist.md
```

Suggested JSON:

```json
{
  "schema_version": "v1",
  "status": "ready|watch|blocked",
  "mode": "routine_maintenance",
  "review_state": "ready_for_review",
  "routine_commands": [
    {
      "name": "fast_validation",
      "command": "./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/fast_validation_latest.json",
      "required": true,
      "expected_status": "pass"
    }
  ],
  "canonical_artifacts": [
    "tmp/validation-final-reviewer-packet.md",
    "tmp/validation-release-readiness.md",
    "tmp/validation-milestone-packet.md",
    "tmp/validation-maintenance-cadence.md"
  ],
  "blocking_policy": {
    "runtime_budget": "blocking",
    "manifest_compatibility": "blocking",
    "data_source_audit_read_csv_count_drift": "watch_or_blocking_by_policy",
    "optional_followups": "non_blocking"
  },
  "optional_followups": [
    "external consumer ownership/evidence completion for governance trail",
    "optional slow-test optimization from pytest profile"
  ],
  "rollback_readiness": "preserved",
  "recommended_cadence": "next_release_cycle"
}
```

### 2. Add artifact freeze policy

Create a compact report section or separate module if cleaner:

- canonical artifacts
- generated artifacts
- transient artifacts
- archived compatibility artifacts
- what should not be manually edited

Could be part of maintenance checklist.

Suggested policy:

- canonical review surface:
  - final reviewer packet
  - release readiness
  - milestone packet
  - review bundle manifest/index
  - manifest compatibility report
  - runtime budget/edge/release-cycle/variance closure
  - data-source audit
- transient:
  - temporary simulated evidence candidate artifacts
  - profiling before/after artifacts
- preserved compatibility:
  - legacy read normalization, not legacy emission

### 3. Add optional follow-up queue report

Create:

- `cajas/reports/validation_optional_followups.py`
- `cajas/scripts/build_validation_optional_followups.py`

Outputs:

```text
tmp/validation-optional-followups.json
tmp/validation-optional-followups.md
```

Suggested JSON:

```json
{
  "schema_version": "v1",
  "status": "open|empty|blocked",
  "blocking": false,
  "items": [
    {
      "id": "external-consumer-evidence-governance",
      "status": "open",
      "blocking_release": false,
      "recommended_timing": "when external owner evidence is available"
    },
    {
      "id": "slow-test-optimization",
      "status": "optional",
      "blocking_release": false,
      "recommended_timing": "if runtime variance recurs"
    }
  ]
}
```

### 4. Integrate checklist/followups into final reviewer packet, release readiness, and milestone

Add optional inputs:

```bash
--maintenance-checklist tmp/validation-maintenance-checklist.json
--optional-followups tmp/validation-optional-followups.json
```

For:

- `build_validation_final_reviewer_packet.py`
- `build_validation_release_readiness_report.py`
- `build_validation_milestone_packet.py`

Reports should surface:

- maintenance checklist status
- optional followup count
- blocking=false for optional queue
- canonical artifact list

### 5. Tests

Add/update tests:

- `cajas/tests/test_validation_maintenance_checklist.py`
- `cajas/tests/test_validation_optional_followups.py`
- `cajas/tests/test_validation_final_reviewer_packet.py`
- `cajas/tests/test_validation_release_readiness.py`
- `cajas/tests/test_validation_milestone_packet.py`

Cover:

- checklist ready when cadence/release/final packet are ready
- checklist blocked when required runtime/compatibility gate fails
- artifact freeze policy includes canonical/transient/preserved compatibility classes
- optional followups are non-blocking
- final reviewer packet includes checklist/followups summary
- release readiness remains ready with non-blocking followups
- milestone remains ready_for_review/blocking=false
- Markdown includes routine commands and offline validation non-goals

### 6. Regenerate artifacts

Build optional followups:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_optional_followups.py \
  --release-readiness-report tmp/validation-release-readiness.json \
  --final-reviewer-packet tmp/validation-final-reviewer-packet.json \
  --maintenance-cadence tmp/validation-maintenance-cadence.json \
  --out-json tmp/validation-optional-followups.json \
  --out-md tmp/validation-optional-followups.md
```

Build maintenance checklist:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_maintenance_checklist.py \
  --maintenance-cadence tmp/validation-maintenance-cadence.json \
  --release-readiness-report tmp/validation-release-readiness.json \
  --final-reviewer-packet tmp/validation-final-reviewer-packet.json \
  --milestone-packet tmp/validation-milestone-packet.json \
  --runtime-budget-report tmp/validation_runtime_budget_report.json \
  --runtime-edge-report tmp/validation-runtime-edge-report.json \
  --runtime-release-cycle-report tmp/validation-runtime-release-cycle-report.json \
  --manifest-compatibility-report tmp/validation-review-bundle/manifest_compatibility_report.json \
  --data-source-audit-report tmp/data_source_audit.json \
  --optional-followups tmp/validation-optional-followups.json \
  --out-json tmp/validation-maintenance-checklist.json \
  --out-md tmp/validation-maintenance-checklist.md
```

Rebuild final reviewer packet:

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
  --maintenance-cadence tmp/validation-maintenance-cadence.json \
  --maintenance-checklist tmp/validation-maintenance-checklist.json \
  --optional-followups tmp/validation-optional-followups.json \
  --out-json tmp/validation-final-reviewer-packet.json \
  --out-md tmp/validation-final-reviewer-packet.md
```

Rebuild release readiness:

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
  --maintenance-cadence tmp/validation-maintenance-cadence.json \
  --maintenance-checklist tmp/validation-maintenance-checklist.json \
  --optional-followups tmp/validation-optional-followups.json \
  --runtime-watch-triage-report tmp/validation-runtime-watch-triage-report.json \
  --pytest-runtime-profile tmp/validation-pytest-runtime-profile.json \
  --out-json tmp/validation-release-readiness.json \
  --out-md tmp/validation-release-readiness.md
```

Rebuild milestone packet:

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
  --maintenance-cadence tmp/validation-maintenance-cadence.json \
  --maintenance-checklist tmp/validation-maintenance-checklist.json \
  --optional-followups tmp/validation-optional-followups.json \
  --runtime-watch-triage-report tmp/validation-runtime-watch-triage-report.json \
  --pytest-runtime-profile tmp/validation-pytest-runtime-profile.json \
  --out-json tmp/validation-milestone-packet.json \
  --out-md tmp/validation-milestone-packet.md
```

### 7. Validation

Focused tests:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_maintenance_checklist.py -q
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_optional_followups.py -q
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_final_reviewer_packet.py -q
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_release_readiness.py -q
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_milestone_packet.py -q
```

Related tests:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests -k "dataset_quality or qlib_experiment_manifest or validation_runtime_budget or reviewer_report_diff or validation_delivery_packet or validation_review_bundle or validation_gate_summary or validation_profile_matrix or validation_history_alias_migration or validation_runtime_edge or validation_milestone_packet or validation_alias_sunset_review or validation_runtime_release_cycle or validation_runtime_variance or validation_runtime_variance_closure or validation_release_readiness or validation_release_ready_closure or validation_final_reviewer_packet or validation_maintenance_cadence or validation_maintenance_checklist or validation_optional_followups or validation_alias_removal_plan or validation_consumer_evidence_closure or validation_consumer_owner_handoff or validation_consumer_owner_response or validation_consumer_evidence_candidate or validation_evidence_candidate_approval or validation_alias_sunset_schedule or validation_canonical_evidence_update_plan or validation_canonical_evidence_apply or validation_applied_evidence_readiness or validation_alias_fallback_removal_readiness or validation_alias_post_removal_closure or validation_runtime_watch_triage or validation_runners or validation_pytest_runtime_profile" -q
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

### 8. Documentation updates

Update:

- `cajas/docs/dataset_quality_loop.md`
- `cajas/README.md`
- `cajas/docs/current_qlib_base_stage_archive.md`

Add Phase 3806–3925 section explaining:

- maintenance checklist
- artifact freeze policy
- optional followup queue
- routine release-cycle commands
- final reviewer packet maintenance handoff
- ready-for-review / maintenance-mode status
- explicit non-goals

### 9. Commit plan

Suggested commits:

```bash
git add cajas/reports/validation_maintenance_checklist.py \
        cajas/scripts/build_validation_maintenance_checklist.py \
        cajas/tests/test_validation_maintenance_checklist.py
git commit -m "feat: add maintenance checklist packet"

git add cajas/reports/validation_optional_followups.py \
        cajas/scripts/build_validation_optional_followups.py \
        cajas/tests/test_validation_optional_followups.py
git commit -m "feat: add optional followup queue report"

git add cajas/reports/validation_final_reviewer_packet.py \
        cajas/scripts/build_validation_final_reviewer_packet.py \
        cajas/reports/validation_release_readiness.py \
        cajas/scripts/build_validation_release_readiness_report.py \
        cajas/reports/validation_milestone_packet.py \
        cajas/scripts/build_validation_milestone_packet.py \
        cajas/tests/test_validation_final_reviewer_packet.py \
        cajas/tests/test_validation_release_readiness.py \
        cajas/tests/test_validation_milestone_packet.py
git commit -m "test: integrate maintenance checklist into final reports"

git add cajas/docs/dataset_quality_loop.md cajas/README.md cajas/docs/current_qlib_base_stage_archive.md
git commit -m "docs: document maintenance mode checklist"
```

## Final Response Required

At the end, provide a compact summary with:

- branch
- commits
- changed files
- maintenance checklist behavior
- artifact freeze policy
- optional followup queue behavior
- final reviewer packet handoff behavior
- release readiness/milestone final status
- alias migration closure status
- canonical-only/legacy normalization confirmation
- validation results with runtimes
- maintenance checklist output paths
- optional followup output paths
- final reviewer packet output paths
- release readiness output paths
- milestone packet output paths
- runtime budget status and timing consistency status
- data-source audit count
- fast validation runtime compared to:
  - Phase 3686 baseline: ~54.733s
  - Phase 3566 baseline: ~57.525s
- recommendation on maintenance mode
- remaining optional follow-ups
- maintenance cadence
- scope confirmation
- risks/limitations
- manual push command

Do not include old Rust trading, kline-labeler, manual annotation, human-in-the-loop, or broker execution as active work.
