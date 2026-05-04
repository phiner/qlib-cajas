# Phase 6806–6925 — EURUSD 15m GUI Review Completion, Batch Merge, and Feedback Summary

## Context

You are working in the Qlib Base / qlib-cajas repository.

Current branch context:

- Previous phase branch: `phase-eurusd-15m-gui-review-stabilization`
- Previous phase completed GUI stabilization from latest `main`.
- Commit already created:
  - `d13101cd` `feat: stabilize EURUSD local review GUI workflow`
- GUI report status:
  - `ready`
- Streamlit availability:
  - `true`
- Plotly availability:
  - `true`
- Launcher command:
  - `./scripts/run_eurusd_review_gui.sh`
- Direct run command:
  - `./.venv-qlib313/bin/python -m streamlit run cajas/apps/eurusd_pattern_review_app.py`

Important local status from previous phase:

- `git status --short` showed one untracked prompt:
  - `tasks/phase_6686_6805_eurusd_15m_gui_review_stabilization_prompt.md`

Before starting this phase, decide whether that prompt should be committed or intentionally left untracked/removed. Do not let it accidentally remain as unexplained state.

Project objective:

- EURUSD 15m Bid pattern research.
- GUI is now the human review interface.
- CSV/JSONL remain durable storage/interchange formats.
- Next goal is to close the loop after the human completes the first review batch.

Scope boundaries:

- EURUSD 15m Bid only.
- No 1H/4H aggregation.
- No live trading.
- No paper trading.
- No broker routing.
- No order generation.
- No production model training.
- No Qlib core modifications.
- No labels should be invented by automation.
- Manual GitHub merge only.

Current expected artifacts:

```text
tmp/eurusd/EURUSD_15m_Bid_clean_view.csv
tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv
tmp/validation-eurusd-pattern-label-schema.json
tmp/validation-eurusd-pattern-review-gui.json
tmp/validation-eurusd-research-readiness.json
```

Human-reviewed GUI output path:

```text
tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv
```

Full merged review output path:

```text
tmp/eurusd/EURUSD_15m_pattern_review_completed.csv
```

## Goal

Implement and stabilize the completed-review loop after GUI labeling.

This phase should:

1. Validate the GUI-completed batch file if it exists.
2. Keep a non-blocking awaiting state if the completed file does not exist yet.
3. Merge valid completed batch rows into the full completed review file.
4. Regenerate feedback and summary reports.
5. Surface completed-review progress in EURUSD research readiness.
6. Preserve GUI-first workflow while keeping CSV as durable storage.
7. Avoid generating or inferring labels automatically.

## Branch Setup

If previous GUI branch has not yet been pushed/merged, either continue on it or create a follow-up branch from it.

Preferred if previous branch is already merged:

```bash
git checkout main
git pull origin main
git checkout -b phase-eurusd-15m-gui-review-completion-loop
```

If previous branch is not merged yet and this is intended as a continuation:

```bash
git checkout phase-eurusd-15m-gui-review-stabilization
git status --short --branch
```

If `git status` is not clean except the known prompt file, stop and report.

If keeping the previous phase prompt, commit it separately before continuing:

```bash
git add tasks/phase_6686_6805_eurusd_15m_gui_review_stabilization_prompt.md
git commit -m "docs: add EURUSD GUI review stabilization prompt"
```

If not keeping it, remove it:

```bash
rm -f tasks/phase_6686_6805_eurusd_15m_gui_review_stabilization_prompt.md
```

## Required Work

### 1. Validate completed GUI batch

Ensure or update:

```text
cajas/reports/validation_eurusd_pattern_review_batch_completion.py
cajas/scripts/build_eurusd_pattern_review_batch_completion_report.py
cajas/tests/test_validation_eurusd_pattern_review_batch_completion.py
```

Behavior:

If completed batch file is missing:

- status: `awaiting_completed_batch`
- blocking: `false`
- reviewed_count: `0`
- pending_count: batch row count
- next_action: `run_local_review_app`

If completed batch file exists:

- validate required identity fields:
  - `sample_id`
  - `timestamp`
  - `candidate_type`
  - `schema_version`
- validate review fields:
  - `human_pattern_label`
  - `market_context`
  - `direction_context`
  - `structure_quality`
  - `follow_through_quality`
  - `review_confidence`
  - `review_notes`
  - `review_status`
- validate enum values against schema version:
  - `eurusd_15m_pattern_review_v1`
- validate numeric rating ranges:
  - 1–5
- validate no duplicate `sample_id`
- validate completed rows correspond to batch sample IDs
- validate forbidden trading/action columns absent:
  - `buy`
  - `sell`
  - `long`
  - `short`
  - `order`
  - `position`
  - `target_position`
  - `signal`
  - `entry`
  - `exit`

Status rules:

- `ready` if completed file is valid and has reviewed rows.
- `watch` if file exists but all rows are pending or only partially reviewed.
- `blocked` if invalid schema/enum/rating/duplicate/forbidden columns exist.

### 2. Add or stabilize batch merge workflow

Ensure or create:

```text
cajas/reports/validation_eurusd_pattern_review_batch_merge.py
cajas/scripts/build_eurusd_pattern_review_batch_merge_report.py
cajas/tests/test_validation_eurusd_pattern_review_batch_merge.py
```

Inputs:

```text
batch_completion_report=tmp/validation-eurusd-pattern-review-batch-001-completion.json
completed_batch_csv=tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv
full_completed_review_csv=tmp/eurusd/EURUSD_15m_pattern_review_completed.csv
label_schema=tmp/validation-eurusd-pattern-label-schema.json
```

Behavior if completed batch missing or completion report awaiting:

- status: `awaiting_completed_batch`
- blocking: `false`
- merge_performed: `false`
- reviewed_count_added: `0`
- next_action: `run_local_review_app`

Behavior if completed batch is valid:

- merge by `sample_id`
- if full completed review file does not exist, create it
- if full completed review file exists:
  - update matching `sample_id` rows
  - append new sample IDs
  - do not duplicate rows
- if overwriting an existing full completed review file, write backup:
  - `tmp/eurusd/EURUSD_15m_pattern_review_completed.backup.csv`
- status: `ready`
- merge_performed: `true`
- include:
  - reviewed_count_added
  - reviewed_count_total
  - updated_existing_count
  - duplicate_sample_id_count
  - created_new_completed_file
  - backup_path
  - next_action: `regenerate_feedback_summary`

Behavior if completed batch invalid:

- status: `blocked`
- blocking: `true`
- merge_performed: `false`
- next_action: `fix_completed_batch`

Generated artifacts:

```text
tmp/validation-eurusd-pattern-review-batch-001-merge.json
tmp/validation-eurusd-pattern-review-batch-001-merge.md
```

### 3. Regenerate feedback and summary from merged review

Ensure or update:

```text
cajas/reports/validation_eurusd_pattern_review_feedback.py
cajas/scripts/build_eurusd_pattern_review_feedback_report.py
cajas/tests/test_validation_eurusd_pattern_review_feedback.py

cajas/reports/validation_eurusd_pattern_review_summary.py
cajas/scripts/build_eurusd_pattern_review_summary_report.py
cajas/tests/test_validation_eurusd_pattern_review_summary.py
```

Expected behavior:

If full completed review is missing:

- feedback status: `awaiting_review_input`
- summary status: `awaiting_review_input`

If full completed review exists:

- feedback validates full review file
- summary reports:
  - reviewed rows by candidate type
  - valid/weak/false-positive/unclear rates
  - average structure quality
  - average follow-through quality
  - average confidence
  - high-confidence valid examples
  - high-confidence false positives
  - candidate types needing more review
  - next recommendation

Recommendation examples:

- `continue_gui_review`
- `expand_review_batch`
- `refine_candidate_rules`
- `begin_outcome_analysis_when_review_threshold_met`

No strategy or trading labels should be generated.

### 4. Readiness integration

Update if needed:

```text
cajas/reports/validation_eurusd_research_readiness.py
cajas/scripts/build_eurusd_research_readiness_report.py
cajas/tests/test_validation_eurusd_research_readiness.py
```

Readiness should consume optional reports:

- GUI report
- batch completion report
- batch merge report
- review feedback report
- review summary report

Expected readiness behavior:

If GUI ready but batch completion awaiting:

- status remains `ready_for_pattern_research_with_clean_view`
- include:
  - `pattern_review_gui_status=ready`
  - `batch_completion_status=awaiting_completed_batch`
- next_action: `run_local_review_app`

If batch merge ready and feedback/summary ready:

- include:
  - `batch_merge_status=ready`
  - reviewed_count_total
  - summary recommendation
- next_action:
  - summary recommendation, such as `continue_gui_review` or `refine_candidate_rules`

If completed batch/merge blocked:

- readiness should become `blocked` or clearly surface blocking reason according to existing readiness semantics.

### 5. CLI commands to generate artifacts

Run completion report:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_eurusd_pattern_review_batch_completion_report.py   --batch-csv tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv   --completed-batch-csv tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv   --label-schema tmp/validation-eurusd-pattern-label-schema.json   --output-json tmp/validation-eurusd-pattern-review-batch-001-completion.json   --output-md tmp/validation-eurusd-pattern-review-batch-001-completion.md
```

Run merge report:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_eurusd_pattern_review_batch_merge_report.py   --batch-completion-report tmp/validation-eurusd-pattern-review-batch-001-completion.json   --completed-batch-csv tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv   --full-completed-review-csv tmp/eurusd/EURUSD_15m_pattern_review_completed.csv   --label-schema tmp/validation-eurusd-pattern-label-schema.json   --output-json tmp/validation-eurusd-pattern-review-batch-001-merge.json   --output-md tmp/validation-eurusd-pattern-review-batch-001-merge.md
```

Regenerate feedback:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_eurusd_pattern_review_feedback_report.py   --template-csv tmp/eurusd/EURUSD_15m_pattern_review_template.csv   --completed-review-csv tmp/eurusd/EURUSD_15m_pattern_review_completed.csv   --label-schema tmp/validation-eurusd-pattern-label-schema.json   --output-json tmp/validation-eurusd-pattern-review-feedback.json   --output-md tmp/validation-eurusd-pattern-review-feedback.md
```

Regenerate summary:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_eurusd_pattern_review_summary_report.py   --feedback-report tmp/validation-eurusd-pattern-review-feedback.json   --completed-review-csv tmp/eurusd/EURUSD_15m_pattern_review_completed.csv   --candidate-pack-report tmp/validation-eurusd-pattern-candidate-pack.json   --output-json tmp/validation-eurusd-pattern-review-summary.json   --output-md tmp/validation-eurusd-pattern-review-summary.md
```

Regenerate readiness with all available reports:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_eurusd_research_readiness_report.py   --base-maintenance-continuation-report tmp/validation-routine-maintenance-continuation.json   --dataset-contract-report tmp/validation-eurusd-dataset-contract.json   --dataset-audit-report tmp/validation-eurusd-dataset-audit.json   --clean-dataset-view-report tmp/validation-eurusd-clean-dataset-view.json   --pattern-candidate-pack-report tmp/validation-eurusd-pattern-candidate-pack.json   --pattern-review-template-report tmp/validation-eurusd-pattern-review-template.json   --pattern-review-gui-report tmp/validation-eurusd-pattern-review-gui.json   --pattern-review-batch-completion-report tmp/validation-eurusd-pattern-review-batch-001-completion.json   --pattern-review-batch-merge-report tmp/validation-eurusd-pattern-review-batch-001-merge.json   --pattern-review-feedback-report tmp/validation-eurusd-pattern-review-feedback.json   --pattern-review-summary-report tmp/validation-eurusd-pattern-review-summary.json   --output-json tmp/validation-eurusd-research-readiness.json   --output-md tmp/validation-eurusd-research-readiness.md
```

If some CLI flags do not exist yet, implement them.

### 6. Tests

Add/update tests:

```text
cajas/tests/test_validation_eurusd_pattern_review_batch_completion.py
cajas/tests/test_validation_eurusd_pattern_review_batch_merge.py
cajas/tests/test_validation_eurusd_pattern_review_feedback.py
cajas/tests/test_validation_eurusd_pattern_review_summary.py
cajas/tests/test_validation_eurusd_research_readiness.py
```

Required scenarios:

1. Completed batch missing:
   - completion status `awaiting_completed_batch`
   - merge status `awaiting_completed_batch`
   - readiness next_action `run_local_review_app`

2. Completed batch valid:
   - completion status `ready` or `watch`
   - merge creates full completed review CSV
   - no duplicate `sample_id`

3. Existing full review file:
   - merge updates by `sample_id`
   - writes backup
   - no duplicate rows

4. Invalid enum:
   - completion or merge blocked

5. Forbidden trading/action columns:
   - completion or merge blocked
   - output never preserves forbidden columns

6. Feedback after merged review:
   - reviewed_count matches merged file

7. Summary after merged review:
   - candidate type summary generated

8. Readiness with GUI ready and completion awaiting:
   - next_action `run_local_review_app`

9. Readiness with merge ready:
   - next_action comes from summary recommendation

### 7. Documentation

Update:

```text
cajas/README.md
cajas/docs/eurusd_pattern_research_kickoff.md
tasks/eurusd_15m_research_end_to_end_roadmap.md
```

Document the completed GUI review loop:

1. Run GUI:
   - `./scripts/run_eurusd_review_gui.sh`
2. Review samples and save completed CSV:
   - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv`
3. Run completion report.
4. Run merge report.
5. Regenerate feedback/summary/readiness.
6. Continue GUI review or refine candidate rules based on summary.

State clearly:

- GUI is the review interface.
- CSV/JSONL are durable storage.
- No labels are invented.
- No trading signals/orders/model training are produced.

### 8. Validation

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest   cajas/tests/test_validation_eurusd_pattern_review_batch_completion.py   cajas/tests/test_validation_eurusd_pattern_review_batch_merge.py   cajas/tests/test_validation_eurusd_pattern_review_feedback.py   cajas/tests/test_validation_eurusd_pattern_review_summary.py   cajas/tests/test_validation_eurusd_research_readiness.py
```

Run py_compile for changed Python modules.

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

## Commit Guidance

Suggested commits:

```bash
git add   cajas/reports/validation_eurusd_pattern_review_batch_completion.py   cajas/scripts/build_eurusd_pattern_review_batch_completion_report.py   cajas/tests/test_validation_eurusd_pattern_review_batch_completion.py   cajas/reports/validation_eurusd_pattern_review_batch_merge.py   cajas/scripts/build_eurusd_pattern_review_batch_merge_report.py   cajas/tests/test_validation_eurusd_pattern_review_batch_merge.py

git commit -m "feat: add EURUSD GUI review completion merge loop"

git add   cajas/reports/validation_eurusd_pattern_review_feedback.py   cajas/reports/validation_eurusd_pattern_review_summary.py   cajas/reports/validation_eurusd_research_readiness.py   cajas/scripts/build_eurusd_research_readiness_report.py   cajas/tests/test_validation_eurusd_pattern_review_feedback.py   cajas/tests/test_validation_eurusd_pattern_review_summary.py   cajas/tests/test_validation_eurusd_research_readiness.py

git commit -m "feat: surface EURUSD completed review summaries"

git add   cajas/README.md   cajas/docs/eurusd_pattern_research_kickoff.md   tasks/eurusd_15m_research_end_to_end_roadmap.md   tasks/phase_6806_6925_eurusd_15m_gui_review_completion_loop_prompt.md

git commit -m "docs: document EURUSD GUI review completion loop"
```

Do not perform automated merge operations.

Manual push after completion:

```bash
git push origin <active-branch>
```

Then open PR and merge manually on GitHub.

## Final Response Required

Report:

- active branch
- relationship to previous GUI branch or latest `main`
- commits created
- files changed
- generated artifacts
- batch completion status
- batch merge status
- feedback status
- summary status
- reviewed count
- pending count
- EURUSD research readiness status
- next recommended action
- validation results
- fast validation runtime
- push status
- manual GitHub merge instruction
- confirmation that GUI remains the review interface and CSV/JSONL remain durable storage
- confirmation that no labels were invented
- confirmation that no trading signals/orders/model training were produced
- confirmation that no automated merge was performed
