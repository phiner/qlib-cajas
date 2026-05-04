# Combined Prompt — Phase 4166–4525 Front-Work Closure, Governance Completion, and Final Maintenance Handoff

You are working in the repository branch:

- `phase-post-merge-research-next`

## Overall objective

Complete the remaining front-work closure in one continuous implementation pass.

This combined prompt merges three phases:

1. **Phase 4166–4285 — External Consumer Evidence Governance Closure**
2. **Phase 4286–4405 — Final Maintenance Freeze and Archive Closure**
3. **Phase 4406–4525 — Post-Freeze Verification and Maintenance Handoff Seal**

The project should end in a reviewer-friendly, routine-maintenance state where:

- release readiness is `ready`
- final reviewer packet is `ready_for_review`
- milestone packet is ready-for-review and non-blocking
- external consumer/evidence governance is closed or explicitly external-tracking-only
- final maintenance archive closure is ready
- post-freeze verification is sealed
- optional followups are closed or routine/non-blocking
- canonical-only producer behavior is confirmed: `history` present, `history_update` absent
- legacy read normalization remains preserved
- no Qlib core changes are made
- no trading execution, broker routing, live/paper trading, annotation loops, or external runtime services are added

## Current baseline

Known state before this combined phase:

- Branch: `phase-post-merge-research-next`
- Release readiness: `ready`
- Final reviewer packet: `ready_for_review`
- Maintenance checklist: `ready`
- Maintenance governance closure: `ready`, conclusion `routine`
- Alias post-removal closure: `closed`
- Canonical producer path: manifest emits `history` only; `history_update` absent
- Legacy read normalization: preserved
- Milestone packet: `overall_status=watch`, `review_state=ready_for_review`, `blocking=false`
- Optional followups: open but non-blocking, count `2`
- Runtime checks: pass
- Data-source audit: `read_csv_count=29`
- Latest baseline fast validation: Phase 3926–4045 `52.688s`, `pytest_fast=49.045s`

Remaining optional followups from previous phases:

1. External consumer ownership/evidence governance completion
2. Optional slow-test optimization only if runtime variance/watch recurs

## Global scope boundaries

Allowed:

- Add report modules, CLIs, tests, docs, and final-report integrations.
- Read existing generated artifacts and evidence/example files.
- Add small governance closure fixtures/templates if useful.
- Mark old governance trails as closed, superseded, or external-tracking-only when they are non-blocking.
- Preserve reviewer-friendly historical context.
- Keep release readiness `ready` when all operational gates remain healthy.

Not allowed:

- Do not reintroduce `history_update` generation.
- Do not remove `normalize_history_metadata` or legacy read compatibility.
- Do not edit Qlib core.
- Do not add trading execution, broker routing, live/paper trading, annotation loops, model training, or external service dependencies.
- Do not require external services or network access.
- Do not manually edit generated artifacts except through scripts.

---

# Phase 4166–4285 — External Consumer Evidence Governance Closure

## Goal

Implement a final external consumer evidence governance closure packet that converts the old alias/evidence followup into a completed governance trail, or clearly marks it as externally-unresolved but operationally closed/non-blocking.

This phase must not remove legacy read normalization and must not re-enable `history_update` alias emission.

## Required implementation

### 1. Add external consumer evidence governance closure report

Create:

- `cajas/reports/validation_external_consumer_evidence_closure.py`
- `cajas/scripts/build_validation_external_consumer_evidence_closure.py`
- `cajas/tests/test_validation_external_consumer_evidence_closure.py`

The report should produce:

- `tmp/validation-external-consumer-evidence-closure.json`
- `tmp/validation-external-consumer-evidence-closure.md`

Recommended JSON fields:

```json
{
  "status": "closed_confirmed | closed_unresolved_external | watch | fail",
  "blocking": false,
  "review_state": "ready_for_review",
  "evidence_governance_state": "closed",
  "canonical_only_confirmed": true,
  "legacy_read_normalization_kept": true,
  "active_alias_emission_supported": false,
  "external_consumer_summary": {
    "consumer_count": 0,
    "unresolved_count": 0,
    "requires_alias_count": 0,
    "owner_missing_count": 0
  },
  "closure_reason": "...",
  "remaining_action": "none | external_tracking_only",
  "release_blocking": false,
  "next_review_cadence": "next_release_cycle"
}
```

The report should read available prior artifacts when present, such as:

- `tmp/alias-post-removal-closure.json`
- `tmp/validation-maintenance-governance-closure.json`
- `tmp/validation-release-readiness.json`
- `tmp/validation-optional-followups.json`
- any existing external consumer evidence/owner handoff artifacts

Behavior:

- If canonical-only producer path is confirmed and alias post-removal closure is closed, evidence governance may be considered operationally closed even when old external evidence records are incomplete, as long as the remaining work is explicitly external/non-blocking.
- If any artifact says a consumer still requires active alias emission, status must not be ready/closed; use `watch` or `fail` depending on severity.
- The report must never claim alias emission is available.

### 2. Integrate into final reports

Update relevant modules/scripts/tests so the new report is surfaced in:

- `validation_final_reviewer_packet.py`
- `validation_release_readiness.py`
- `validation_milestone_packet.py`

Add optional CLI args:

- `--external-consumer-evidence-closure-report`

Expected integration behavior:

- Release readiness should remain `ready` when this closure report is `closed_confirmed` or `closed_unresolved_external`, `blocking=false`, and existing gates pass.
- Milestone packet may keep governance `watch` context only if needed, but it must remain `review_state=ready_for_review`, `blocking=false`.
- Final reviewer packet should summarize that external evidence governance is closed or external-tracking-only.

### 3. Update optional followup queue behavior

If the optional followup queue currently lists external consumer ownership/evidence governance completion, update its report behavior so that when the new closure artifact is provided and closed, that item is marked closed or moved into a completed/non-active section.

Do not delete historical context; make the transition reviewer-friendly.

Expected optional followup output after integration:

- `blocking=false`
- active open item count should ideally decrease from `2` to `1`
- remaining active item should be slow-test optimization only if runtime variance/watch recurs

### 4. Documentation

Update:

- `cajas/docs/current_qlib_base_stage_archive.md`
- `cajas/docs/dataset_quality_loop.md`
- `cajas/README.md` if appropriate

Document:

- external consumer evidence governance closure status
- why this does not re-enable alias emission
- why release readiness remains ready
- what remains as routine next release-cycle monitoring

---

# Phase 4286–4405 — Final Maintenance Freeze and Archive Closure

## Goal

Create a final maintenance freeze/archive closure packet that freezes the review surface, documents the long-term maintenance contract, and ensures no old pre-removal workflow gate can be misread as a current blocker.

The desired final state is:

- release readiness `ready`
- final reviewer packet `ready_for_review`
- milestone packet either `ready` or `watch` only as non-blocking governance context
- maintenance mode clearly frozen
- no active alias migration work remaining
- optional followups either closed or explicitly routine/non-blocking

## Required implementation

### 1. Add final maintenance archive closure report

Create:

- `cajas/reports/validation_final_maintenance_archive_closure.py`
- `cajas/scripts/build_validation_final_maintenance_archive_closure.py`
- `cajas/tests/test_validation_final_maintenance_archive_closure.py`

Generate:

- `tmp/validation-final-maintenance-archive-closure.json`
- `tmp/validation-final-maintenance-archive-closure.md`

Recommended JSON structure:

```json
{
  "status": "ready | watch | fail",
  "review_state": "ready_for_review",
  "blocking": false,
  "maintenance_mode": "frozen_routine",
  "archive_closure": "closed",
  "release_ready": true,
  "canonical_only_confirmed": true,
  "legacy_read_normalization_kept": true,
  "alias_migration_active_work_remaining": false,
  "runtime_monitoring_cadence": "next_release_cycle",
  "canonical_review_surface": {
    "artifact_count": 12,
    "artifacts": []
  },
  "superseded_historical_gates": [],
  "active_followups": [],
  "routine_maintenance_commands": [],
  "scope_boundary": {
    "offline_validation_only": true,
    "qlib_core_modified": false,
    "trading_execution_added": false
  }
}
```

The report should consume current artifacts when available, such as:

- `tmp/validation-maintenance-checklist.json`
- `tmp/validation-maintenance-governance-closure.json`
- `tmp/validation-external-consumer-evidence-closure.json`
- `tmp/validation-optional-followups.json`
- `tmp/validation-release-readiness.json`
- `tmp/validation-final-reviewer-packet.json`
- `tmp/validation-milestone-packet.json`
- `tmp/alias-post-removal-closure.json`
- runtime budget / edge / release-cycle / variance closure artifacts

Behavior:

- `status=ready` only if release readiness is ready, alias post-removal closure is closed, canonical-only is confirmed, and no blocking followups remain.
- If only routine/non-blocking followups remain, status can still be `ready` with active followups listed as routine.
- If any current gate says `blocking=true` or alias active emission is required, status must be `watch` or `fail`.

### 2. Integrate into final reviewer packet, release readiness, and milestone packet

Add optional CLI args:

- `--final-maintenance-archive-closure-report`

Update:

- `validation_final_reviewer_packet.py`
- `build_validation_final_reviewer_packet.py`
- `validation_release_readiness.py`
- `build_validation_release_readiness_report.py`
- `validation_milestone_packet.py`
- `build_validation_milestone_packet.py`
- relevant tests

Expected behavior:

- Final reviewer packet prominently reports final maintenance archive closure.
- Release readiness remains `ready` when archive closure is `ready` and existing gates pass.
- Milestone packet should avoid creating confusion: if it remains `watch`, include `blocking=false`, `review_state=ready_for_review`, and a clear `watch_reason=historical_governance_context_only` or equivalent.

### 3. Freeze/archive docs

Update:

- `cajas/docs/current_qlib_base_stage_archive.md`
- `cajas/docs/dataset_quality_loop.md`
- `cajas/README.md`

Add a final section explaining:

- current maintenance mode
- canonical review surface
- generated artifact freeze policy
- routine commands for next release cycle
- scope boundary
- alias migration closure
- legacy compatibility posture
- remaining optional work, if any

### 4. Optional archive index helper

If useful and simple, add an archive index section in the final archive closure report summarizing the key generated artifacts and their purpose.

Do not overbuild; keep the phase focused on closure clarity.

---

# Phase 4406–4525 — Post-Freeze Verification and Maintenance Handoff Seal

## Goal

Add one final verification/handoff seal that proves the previous closure reports agree with each other and that the project can be handed off as a stable routine-maintenance baseline.

This phase should not add another new workstream. It should be a seal/checksum-style governance packet that validates the already-generated closure artifacts and produces a compact reviewer handoff summary.

Desired final state:

- all current closure artifacts agree on `ready` / `ready_for_review` / non-blocking posture
- optional followups are either closed, external-tracking-only, or routine/non-blocking
- no alias migration active work remains
- no generated artifact freeze-policy violations are present
- final reviewer packet includes this seal
- release readiness remains `ready`
- milestone packet is ready-for-review and non-blocking

## Required implementation

### 1. Add post-freeze verification/handoff seal report

Create:

- `cajas/reports/validation_post_freeze_handoff_seal.py`
- `cajas/scripts/build_validation_post_freeze_handoff_seal.py`
- `cajas/tests/test_validation_post_freeze_handoff_seal.py`

Generate:

- `tmp/validation-post-freeze-handoff-seal.json`
- `tmp/validation-post-freeze-handoff-seal.md`

Recommended JSON structure:

```json
{
  "status": "sealed | watch | fail",
  "review_state": "ready_for_review",
  "blocking": false,
  "seal_version": 1,
  "handoff_state": "routine_maintenance",
  "release_ready": true,
  "final_reviewer_ready": true,
  "milestone_non_blocking": true,
  "closure_consistency": {
    "external_consumer_evidence_closure": "closed_confirmed | closed_unresolved_external | external_tracking_only",
    "final_maintenance_archive_closure": "ready",
    "maintenance_governance_closure": "ready",
    "alias_post_removal_closure": "closed",
    "runtime_release_cycle": "pass"
  },
  "canonical_contract": {
    "history_present": true,
    "history_update_absent": true,
    "legacy_read_normalization_kept": true,
    "active_alias_emission_supported": false
  },
  "freeze_policy_check": {
    "canonical_artifact_count": 12,
    "manual_edit_violations": 0,
    "generated_artifacts_current": true
  },
  "active_followups": [],
  "routine_followups": [],
  "reviewer_handoff": {
    "recommended_action": "review_or_merge",
    "next_cadence": "next_release_cycle",
    "push_command": "git push origin phase-post-merge-research-next"
  }
}
```

The report should consume current artifacts when available, especially:

- `tmp/validation-external-consumer-evidence-closure.json`
- `tmp/validation-final-maintenance-archive-closure.json`
- `tmp/validation-maintenance-governance-closure.json`
- `tmp/validation-maintenance-checklist.json`
- `tmp/validation-optional-followups.json`
- `tmp/validation-release-readiness.json`
- `tmp/validation-final-reviewer-packet.json`
- `tmp/validation-milestone-packet.json`
- `tmp/alias-post-removal-closure.json`
- runtime release-cycle / runtime budget / runtime variance closure artifacts if present

Behavior:

- Use `status=sealed` only when all operational and closure gates are ready/non-blocking.
- Use `watch` if all release blockers are clear but some routine followup remains visible.
- Use `fail` if any current artifact indicates active alias emission is required, canonical-only is broken, release readiness is not ready, or a blocking followup remains.
- The seal must not mutate prior artifacts; it only reads and summarizes.

### 2. Integrate the seal into final reporting surfaces

Add optional CLI args:

- `--post-freeze-handoff-seal-report`

Update:

- `validation_final_reviewer_packet.py`
- `build_validation_final_reviewer_packet.py`
- `validation_release_readiness.py`
- `build_validation_release_readiness_report.py`
- `validation_milestone_packet.py`
- `build_validation_milestone_packet.py`
- relevant tests

Expected behavior:

- Final reviewer packet should prominently show the handoff seal status.
- Release readiness should remain `ready` when the seal is `sealed` or `watch` with `blocking=false` and all existing gates pass.
- Milestone packet should keep `review_state=ready_for_review`, `blocking=false`; if `overall_status=watch`, the reason must be routine/historical context only.

### 3. Add final docs note

Update:

- `cajas/docs/current_qlib_base_stage_archive.md`
- `cajas/docs/dataset_quality_loop.md`
- `cajas/README.md` if appropriate

Document:

- post-freeze handoff seal status
- final maintenance cadence
- push/review handoff
- how to regenerate the closure and seal artifacts
- what must not be changed in maintenance mode

### 4. Optional: compact command contract summary

If straightforward, include the routine command contract from the maintenance checklist in the handoff seal markdown.

Keep this as a summary only; do not duplicate large generated outputs.

---

# Combined validation plan

Run focused tests in order:

```bash
pytest cajas/tests/test_validation_external_consumer_evidence_closure.py -q
pytest cajas/tests/test_validation_optional_followups.py -q
pytest cajas/tests/test_validation_final_maintenance_archive_closure.py -q
pytest cajas/tests/test_validation_post_freeze_handoff_seal.py -q
pytest cajas/tests/test_validation_final_reviewer_packet.py -q
pytest cajas/tests/test_validation_release_readiness.py -q
pytest cajas/tests/test_validation_milestone_packet.py -q
pytest cajas/tests/test_validation_maintenance_checklist.py -q
pytest cajas/tests/test_validation_maintenance_governance_closure.py -q
```

Regenerate the new artifacts and final reporting artifacts in dependency order. Suggested order:

```bash
python cajas/scripts/build_validation_external_consumer_evidence_closure.py \
  --out-json tmp/validation-external-consumer-evidence-closure.json \
  --out-md tmp/validation-external-consumer-evidence-closure.md

python cajas/scripts/build_validation_optional_followups.py \
  --external-consumer-evidence-closure-report tmp/validation-external-consumer-evidence-closure.json \
  --out-json tmp/validation-optional-followups.json \
  --out-md tmp/validation-optional-followups.md

python cajas/scripts/build_validation_final_maintenance_archive_closure.py \
  --external-consumer-evidence-closure-report tmp/validation-external-consumer-evidence-closure.json \
  --optional-followups-report tmp/validation-optional-followups.json \
  --out-json tmp/validation-final-maintenance-archive-closure.json \
  --out-md tmp/validation-final-maintenance-archive-closure.md

python cajas/scripts/build_validation_post_freeze_handoff_seal.py \
  --external-consumer-evidence-closure-report tmp/validation-external-consumer-evidence-closure.json \
  --final-maintenance-archive-closure-report tmp/validation-final-maintenance-archive-closure.json \
  --optional-followups-report tmp/validation-optional-followups.json \
  --out-json tmp/validation-post-freeze-handoff-seal.json \
  --out-md tmp/validation-post-freeze-handoff-seal.md
```

Then regenerate final reviewer packet, release readiness, and milestone packet with all new report inputs:

```bash
python cajas/scripts/build_validation_final_reviewer_packet.py \
  --external-consumer-evidence-closure-report tmp/validation-external-consumer-evidence-closure.json \
  --final-maintenance-archive-closure-report tmp/validation-final-maintenance-archive-closure.json \
  --post-freeze-handoff-seal-report tmp/validation-post-freeze-handoff-seal.json

python cajas/scripts/build_validation_release_readiness_report.py \
  --external-consumer-evidence-closure-report tmp/validation-external-consumer-evidence-closure.json \
  --final-maintenance-archive-closure-report tmp/validation-final-maintenance-archive-closure.json \
  --post-freeze-handoff-seal-report tmp/validation-post-freeze-handoff-seal.json

python cajas/scripts/build_validation_milestone_packet.py \
  --external-consumer-evidence-closure-report tmp/validation-external-consumer-evidence-closure.json \
  --final-maintenance-archive-closure-report tmp/validation-final-maintenance-archive-closure.json \
  --post-freeze-handoff-seal-report tmp/validation-post-freeze-handoff-seal.json
```

Adjust exact CLI arguments to match existing script patterns if the repository uses different names. Keep the artifact dependency order.

Run full fast validation and hygiene:

```bash
python cajas/scripts/run_fast_validation.py
python cajas/scripts/audit_data_sources.py
python cajas/scripts/audit_validation_runtime.py
python cajas/scripts/check_path_hygiene.py

git diff --check
find cajas -path "*/init.py" -print
```

If there is an established related-suite command, run it as well and report the pass/deselect counts.

## Expected final combined state

- `tmp/validation-external-consumer-evidence-closure.json` exists and is closed/non-blocking.
- `tmp/validation-final-maintenance-archive-closure.json` exists and is `status=ready`.
- `tmp/validation-post-freeze-handoff-seal.json` exists and is `status=sealed` or `watch` with `blocking=false`.
- Release readiness remains `ready`.
- Final reviewer packet remains `ready_for_review`.
- Milestone packet is ready-for-review and non-blocking.
- Optional followup active count is reduced where possible; any remaining followup is routine/non-blocking.
- Alias post-removal closure remains `closed`.
- Canonical-only producer path remains `history` only, `history_update` absent.
- Legacy read normalization remains preserved.
- Maintenance mode is frozen/routine.
- No Qlib core changes.
- No trading execution scope added.
- Runtime/audit/hygiene remain pass.

## Commit guidance

Use small commits. Suggested grouping:

1. `feat: add external consumer evidence closure report`
2. `feat: add final maintenance archive closure report`
3. `feat: add post-freeze handoff seal report`
4. `test: integrate closure reports into final reporting`
5. `docs: document final maintenance handoff closure`

## Final response format

When done, report:

- branch
- commits
- files changed
- new artifacts
- external consumer evidence closure status
- final archive closure status
- post-freeze handoff seal status
- release readiness / final reviewer / milestone statuses
- optional followup count before/after and remaining followups
- alias/canonical compatibility status
- validation results
- runtime comparison against Phase 3926–4045 baseline `52.688s`
- remaining risks/limitations
- push status and manual push command

