# Phase 3686–3805 Prompt: Milestone Watch Governance Closure and Stable Maintenance Cadence

You are working in the repository on branch `phase-post-merge-research-next`.

## Current Baseline

The active project mainline is **Microsoft Qlib / Qlib Base / qlib-cajas**, a Qlib-based offline research infrastructure validation effort.

Recent completed phase:

- Phase 3566–3685 implemented runtime variance closure and final reviewer packet.
- Local commits:
  - `e8fa930c` `feat: add runtime variance closure report`
  - `d68e945e` `fix: mark non-blocking runtime variance followup`
  - `95c59a7b` `feat: add final reviewer packet`
  - `f9ad59ce` `test: integrate final reviewer packet into readiness reports`
  - `4302a1b5` `docs: document runtime variance closure and final review packet`
- Runtime variance closure:
  - `tmp/validation-runtime-variance-closure.json`
  - status: `closed`
  - reason_code: `variance_pass`
  - remaining_followup: `none`
  - recommended_cadence: `routine`
- Runtime release-cycle:
  - status: `pass`
  - reason_code: `runtime_healthy`
- Release-ready closure:
  - status: `ready`
  - review_state: `ready_for_review`
  - blocking: `false`
  - ready_for_review: `true`
- Final reviewer packet:
  - `tmp/validation-final-reviewer-packet.json`
  - status: `ready_for_review`
- Release readiness:
  - status: `ready`
- Milestone packet:
  - overall_status: `watch`
  - reason: alias-sunset governance watch context still appears in milestone posture, even though release readiness is ready.
- Alias migration:
  - producer-side fallback removal is functionally closed
  - active `history_update` alias emission removed/hard-disabled
  - generated manifest is canonical-only:
    - `history` present
    - `history_update` absent
  - legacy read normalization preserved
  - manifest compatibility: `pass`
  - alias post-removal closure: `closed`
- Validation:
  - related suite: `232 passed`, `319 deselected`
  - fast validation total: `57.525s`
  - pytest_fast: `53.201s`
  - runtime budget: `pass`
  - timing consistency: `pass`
  - runtime edge: `pass`
  - runtime variance: `pass`
  - runtime watch triage: `pass`
  - runtime release-cycle: `pass`
  - data-source audit: `read_csv_count=29`
  - hygiene: pass
- Runtime comparison:
  - vs Phase 3446 baseline `58.351s`: current `57.525s`
  - vs Phase 3326 baseline `56.96s`: current `57.525s`

Current interpretation:

- Release readiness is ready.
- Final reviewer packet is ready for review.
- Runtime variance is closed.
- Alias migration is functionally closed.
- The only semantic inconsistency is milestone packet still reporting `watch` due governance context that no longer blocks release readiness.
- Next phase should not add broad features. It should clarify milestone governance semantics and define stable maintenance cadence.

## User Direction

The user wants faster progress and larger phases, but the project has reached a review-ready milestone. The next work should move the project from active implementation into stable maintenance/release-cycle monitoring.

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

Implement **Milestone Watch Governance Closure and Stable Maintenance Cadence**.

The goal is to resolve or clarify why the milestone packet remains `watch` when release readiness is `ready` and final reviewer packet is `ready_for_review`.

Preferred outcome:

- milestone packet reports `ready_for_review`, `ready`, or equivalent non-blocking status
- any remaining governance watch is represented as non-blocking context
- stable maintenance cadence packet/report is produced
- next-release monitoring commands are explicit
- no new broad validation feature surface is added

This phase should answer:

1. Why does milestone packet remain `watch`?
2. Is the milestone watch a blocker, governance note, or stale/superseded context?
3. Can milestone packet align with release readiness/final reviewer packet?
4. What maintenance cadence should be used after this milestone?
5. What commands should be run each release cycle?
6. What remains as optional future work?

## Required Work

### 1. Audit milestone watch reason

Inspect:

```bash
cat tmp/validation-milestone-packet.json
cat tmp/validation-milestone-packet.md
cat tmp/validation-release-readiness.json
cat tmp/validation-final-reviewer-packet.json
cat tmp/validation-release-ready-closure.json
cat tmp/alias-post-removal-closure.json
```

Classify milestone watch reason as one of:

- real blocking issue
- non-blocking governance context
- stale pre-removal alias workflow context
- optional follow-up
- runtime watch
- artifact inconsistency

Do not hide real blockers. If a true blocker exists, leave milestone watch and document it.

### 2. Update milestone status semantics

Inspect:

- `cajas/reports/validation_milestone_packet.py`
- `cajas/scripts/build_validation_milestone_packet.py`
- `cajas/tests/test_validation_milestone_packet.py`

Add explicit fields if useful:

```json
{
  "review_state": "ready_for_review|watch|blocked",
  "blocking": false,
  "blocking_reasons": [],
  "non_blocking_governance_notes": [...],
  "superseded_watch_items": [...],
  "maintenance_cadence": "routine_next_release_cycle"
}
```

If release readiness is `ready`, release-ready closure is `ready`, final reviewer packet is `ready_for_review`, alias post-removal closure is `closed`, runtime budget/edge/release-cycle are pass, and data-source audit is stable, then milestone should not present as a blocking watch.

Options:

- Set milestone `overall_status=ready`
- Or keep `overall_status=watch` but add `review_state=ready_for_review`, `blocking=false`

Prefer the least disruptive change to existing status enums.

### 3. Add stable maintenance cadence report

Create:

- `cajas/reports/validation_maintenance_cadence.py`
- `cajas/scripts/build_validation_maintenance_cadence_report.py`

Outputs:

```text
tmp/validation-maintenance-cadence.json
tmp/validation-maintenance-cadence.md
```

Suggested JSON:

```json
{
  "schema_version": "v1",
  "status": "active|routine|blocked",
  "recommended_cadence": "next_release_cycle",
  "routine_commands": [
    "run_fast_validation.py --tier fast",
    "check_validation_runtime_budget.py",
    "build_validation_runtime_edge_report.py",
    "build_validation_runtime_release_cycle_report.py",
    "audit_data_sources.py",
    "build_validation_final_reviewer_packet.py"
  ],
  "watch_items": [],
  "rollback_readiness": "preserved",
  "canonical_manifest_policy": "history_only",
  "legacy_read_normalization": "kept",
  "data_source_audit_expected_read_csv_count": 29
}
```

Status rules:

- `routine` if release readiness ready and final reviewer packet ready_for_review
- `active` if still watch but non-blocking
- `blocked` if any required gate fails

### 4. Integrate maintenance cadence into final reviewer packet, release readiness, and milestone

Add optional input:

```bash
--maintenance-cadence tmp/validation-maintenance-cadence.json
```

For:

- `build_validation_final_reviewer_packet.py`
- `build_validation_release_readiness_report.py`
- `build_validation_milestone_packet.py`

Reports should surface:

- cadence status
- recommended cadence
- routine command count/list
- whether there are watch items

### 5. Add reviewer handoff note

Add to final reviewer packet Markdown a concise handoff section:

```markdown
## Reviewer Handoff

Status: Ready for review
Canonical manifest policy: history-only
Alias migration: closed
Runtime: pass
Data-source audit: stable at 29 read_csv calls
Next routine action: run maintenance cadence at next release cycle
```

### 6. Tests

Add/update tests:

- `cajas/tests/test_validation_maintenance_cadence.py`
- `cajas/tests/test_validation_final_reviewer_packet.py`
- `cajas/tests/test_validation_release_readiness.py`
- `cajas/tests/test_validation_milestone_packet.py`

Cover:

- maintenance cadence routine when release ready and final packet ready_for_review
- maintenance cadence active/watch when non-blocking watch remains
- maintenance cadence blocked on required failure
- milestone ready_for_review semantics when release/final closure ready
- milestone still blocked if real blocker exists
- final reviewer packet includes cadence summary and reviewer handoff
- release readiness includes cadence summary
- Markdown includes offline validation non-goals

### 7. Regenerate artifacts

Build maintenance cadence:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_maintenance_cadence_report.py \
  --release-readiness-report tmp/validation-release-readiness.json \
  --release-ready-closure tmp/validation-release-ready-closure.json \
  --final-reviewer-packet tmp/validation-final-reviewer-packet.json \
  --alias-post-removal-closure tmp/alias-post-removal-closure.json \
  --runtime-budget-report tmp/validation_runtime_budget_report.json \
  --runtime-edge-report tmp/validation-runtime-edge-report.json \
  --runtime-release-cycle-report tmp/validation-runtime-release-cycle-report.json \
  --data-source-audit-report tmp/data_source_audit.json \
  --out-json tmp/validation-maintenance-cadence.json \
  --out-md tmp/validation-maintenance-cadence.md
```

Rebuild final reviewer packet with cadence:

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
  --out-json tmp/validation-final-reviewer-packet.json \
  --out-md tmp/validation-final-reviewer-packet.md
```

Rebuild release readiness with cadence:

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
  --runtime-watch-triage-report tmp/validation-runtime-watch-triage-report.json \
  --pytest-runtime-profile tmp/validation-pytest-runtime-profile.json \
  --out-json tmp/validation-release-readiness.json \
  --out-md tmp/validation-release-readiness.md
```

Rebuild milestone packet with cadence and final packet:

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
  --runtime-watch-triage-report tmp/validation-runtime-watch-triage-report.json \
  --pytest-runtime-profile tmp/validation-pytest-runtime-profile.json \
  --out-json tmp/validation-milestone-packet.json \
  --out-md tmp/validation-milestone-packet.md
```

### 8. Validation

Focused tests:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_maintenance_cadence.py -q
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_final_reviewer_packet.py -q
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_release_readiness.py -q
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_milestone_packet.py -q
```

Related tests:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests -k "dataset_quality or qlib_experiment_manifest or validation_runtime_budget or reviewer_report_diff or validation_delivery_packet or validation_review_bundle or validation_gate_summary or validation_profile_matrix or validation_history_alias_migration or validation_runtime_edge or validation_milestone_packet or validation_alias_sunset_review or validation_runtime_release_cycle or validation_runtime_variance or validation_runtime_variance_closure or validation_release_readiness or validation_release_ready_closure or validation_final_reviewer_packet or validation_maintenance_cadence or validation_alias_removal_plan or validation_consumer_evidence_closure or validation_consumer_owner_handoff or validation_consumer_owner_response or validation_consumer_evidence_candidate or validation_evidence_candidate_approval or validation_alias_sunset_schedule or validation_canonical_evidence_update_plan or validation_canonical_evidence_apply or validation_applied_evidence_readiness or validation_alias_fallback_removal_readiness or validation_alias_post_removal_closure or validation_runtime_watch_triage or validation_runners or validation_pytest_runtime_profile" -q
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

### 9. Documentation updates

Update:

- `cajas/docs/dataset_quality_loop.md`
- `cajas/README.md`
- `cajas/docs/current_qlib_base_stage_archive.md`

Add Phase 3686–3805 section explaining:

- milestone watch governance audit
- ready-for-review milestone semantics
- stable maintenance cadence
- final reviewer handoff
- routine commands
- remaining optional follow-ups
- explicit non-goals

### 10. Commit plan

Suggested commits:

```bash
git add cajas/reports/validation_milestone_packet.py \
        cajas/scripts/build_validation_milestone_packet.py \
        cajas/tests/test_validation_milestone_packet.py
git commit -m "fix: clarify milestone ready-for-review semantics"

git add cajas/reports/validation_maintenance_cadence.py \
        cajas/scripts/build_validation_maintenance_cadence_report.py \
        cajas/tests/test_validation_maintenance_cadence.py
git commit -m "feat: add validation maintenance cadence report"

git add cajas/reports/validation_final_reviewer_packet.py \
        cajas/scripts/build_validation_final_reviewer_packet.py \
        cajas/tests/test_validation_final_reviewer_packet.py
git commit -m "test: add final reviewer maintenance handoff"

git add cajas/reports/validation_release_readiness.py \
        cajas/scripts/build_validation_release_readiness_report.py \
        cajas/tests/test_validation_release_readiness.py
git commit -m "test: integrate maintenance cadence into release readiness"

git add cajas/docs/dataset_quality_loop.md cajas/README.md cajas/docs/current_qlib_base_stage_archive.md
git commit -m "docs: document maintenance cadence and final handoff"
```

## Final Response Required

At the end, provide a compact summary with:

- branch
- commits
- changed files
- milestone watch audit result
- milestone final status/review_state
- maintenance cadence behavior
- final reviewer packet handoff behavior
- release readiness final status
- alias migration closure status
- canonical-only/legacy normalization confirmation
- validation results with runtimes
- maintenance cadence output paths
- final reviewer packet output paths
- release readiness output paths
- milestone packet output paths
- runtime budget status and timing consistency status
- data-source audit count
- fast validation runtime compared to:
  - Phase 3566 baseline: ~57.525s
  - Phase 3446 baseline: ~58.351s
- recommendation on ready-for-review / maintenance mode
- remaining optional follow-ups
- maintenance cadence
- scope confirmation
- risks/limitations
- manual push command

Do not include old Rust trading, kline-labeler, manual annotation, human-in-the-loop, or broker execution as active work.
