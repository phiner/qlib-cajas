# Phase 5846–5965 — EURUSD 15m Completed Batch Intake, Merge, and Review Summary

## Context

You are working in the Qlib Base / qlib-cajas repository.

The active research objective is EURUSD 15m Bid pattern research.

Current baseline:

- Active branch: `phase-eurusd-pattern-research-kickoff`
- Research timeframe: fixed to `15m`
- Price side: `Bid`
- Do not aggregate to 1H/4H.
- Do not introduce live trading, paper trading, broker routing, order generation, production model training, or Qlib core modifications.
- Raw EURUSD CSV files are immutable.
- Clean view is approved for pattern research:
  - `tmp/eurusd/EURUSD_15m_Bid_clean_view.csv`

Current review workflow state from Phase 5726–5845:

- First review batch status: `ready`
- Review batch path:
  - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv`
- Review batch JSONL:
  - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001.jsonl`
- Review guide:
  - `tmp/validation-eurusd-pattern-review-guide.md`
- Batch row count: `100`
- Batch type distribution:
  - 10 candidate types
  - 10 rows per candidate type
- Review guide status: `ready`
- Label schema version:
  - `eurusd_15m_pattern_review_v1`
- Batch completion status:
  - `awaiting_completed_batch`
- Batch completion blocking:
  - `false`
- Reviewed count:
  - `0`
- Pending count:
  - `100`
- Expected completed batch path:
  - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv`
- Full review completed file path:
  - `tmp/eurusd/EURUSD_15m_pattern_review_completed.csv`

Important note:

- In Phase 5726–5845, EURUSD research readiness showed `blocked` because the base maintenance report was missing in that run environment.
- The review batch workflow itself passed and was valid.
- This phase should preserve that distinction and avoid treating missing optional/base context as a failure of human review intake unless it is truly required.

## Goal

Create a safe completed-batch intake and merge workflow for the first EURUSD 15m human review batch.

This phase should support both states:

1. If `tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv` is missing:
   - keep reporting `awaiting_completed_batch`
   - stay non-blocking
   - provide clear instructions for the human reviewer

2. If the completed batch exists:
   - validate it
   - merge it into the full completed review file
   - regenerate feedback and summary reports
   - surface progress in EURUSD research readiness

This phase should not invent labels. It should only validate and summarize human-provided labels.

## Required Work

### 1. Add completed batch merge report

Create:

`cajas/reports/validation_eurusd_pattern_review_batch_merge.py`

Inputs:

- batch completion report:
  - `tmp/validation-eurusd-pattern-review-batch-001-completion.json`
- completed batch CSV:
  - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv`
- existing full completed review CSV:
  - `tmp/eurusd/EURUSD_15m_pattern_review_completed.csv`
- output merged completed review CSV:
  - default same as full completed review CSV
- label schema JSON:
  - `tmp/validation-eurusd-pattern-label-schema.json`

Behavior if completed batch is missing:

- status: `awaiting_completed_batch`
- blocking: `false`
- merge_performed: `false`
- reviewed_count_added: `0`
- output path reported
- next_action: `fill_batch_001_review`

Behavior if completed batch exists and is valid:

- merge rows into full completed review CSV
- if full completed review CSV does not exist, create it from completed batch
- if full completed review CSV exists:
  - merge by `sample_id`
  - do not duplicate rows
  - update existing rows with same `sample_id` only if schema version matches and completed batch row is valid
- write a backup copy before overwriting existing full completed review, for example:
  - `tmp/eurusd/EURUSD_15m_pattern_review_completed.backup.csv`
- report:
  - status: `ready`
  - blocking: `false`
  - merge_performed: `true`
  - reviewed_count_added
  - reviewed_count_total
  - duplicate_sample_id_count
  - updated_existing_count
  - created_new_completed_file
  - backup_path if applicable
  - next_action: `regenerate_review_feedback_summary`

Behavior if completed batch exists but is invalid:

- status: `blocked`
- blocking: `true`
- merge_performed: `false`
- invalid reasons reported
- next_action: `fix_completed_batch`

Forbidden columns remain blocked:

- `buy`, `sell`, `long`, `short`, `order`, `position`, `target_position`, `signal`, `entry`, `exit`

Generated artifacts:

- `tmp/validation-eurusd-pattern-review-batch-001-merge.json`
- `tmp/validation-eurusd-pattern-review-batch-001-merge.md`
- possibly:
  - `tmp/eurusd/EURUSD_15m_pattern_review_completed.csv`
  - `tmp/eurusd/EURUSD_15m_pattern_review_completed.backup.csv`

### 2. Add CLI builder

Create:

`cajas/scripts/build_eurusd_pattern_review_batch_merge_report.py`

Default CLI args:

```text
--batch-completion-report tmp/validation-eurusd-pattern-review-batch-001-completion.json
--completed-batch-csv tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv
--full-completed-review-csv tmp/eurusd/EURUSD_15m_pattern_review_completed.csv
--label-schema tmp/validation-eurusd-pattern-label-schema.json
--output-json tmp/validation-eurusd-pattern-review-batch-001-merge.json
--output-md tmp/validation-eurusd-pattern-review-batch-001-merge.md
```

The CLI should not fail when completed batch is missing. It should generate an awaiting report.

### 3. Update feedback and summary workflow to consume merged review

Update if needed:

- `cajas/reports/validation_eurusd_pattern_review_feedback.py`
- `cajas/reports/validation_eurusd_pattern_review_summary.py`
- corresponding scripts/tests

Expected behavior:

- If merged full completed review file is missing:
  - feedback remains `awaiting_review_input`
- If it exists:
  - feedback validates it
  - summary reports reviewed pattern distribution
- If batch merge report is `awaiting_completed_batch`:
  - readiness next action should remain `fill_batch_001_review`
- If batch merge report is `ready`:
  - next action should become `review_feedback_summary` or summary recommendation

### 4. Update EURUSD research readiness

Update:

- `cajas/reports/validation_eurusd_research_readiness.py`
- `cajas/scripts/build_eurusd_research_readiness_report.py`
- `cajas/tests/test_validation_eurusd_research_readiness.py`

Add optional input for:

- review batch merge report

Expected readiness behavior:

- If batch/guide are ready and batch completion is awaiting:
  - readiness remains non-blocking
  - next_action: `fill_batch_001_review`
- If merge report is awaiting:
  - readiness remains non-blocking
  - next_action: `fill_batch_001_review`
- If merge report is ready:
  - include:
    - `review_batch_merge_status`
    - `reviewed_count_total`
    - `reviewed_count_added`
  - next_action should depend on feedback/summary:
    - `review_feedback_summary`
    - `continue_batch_review`
    - `analyze_valid_pattern_outcomes`
- If merge report is blocked:
  - readiness becomes blocked
  - reason: `review_batch_merge_blocked`

Also fix readiness handling so that missing base maintenance context in a local EURUSD-only run does not incorrectly mask the review workflow status. It may be reported as `base_context_missing` / `watch`, but should not be confused with review batch failure when all EURUSD inputs are valid.

### 5. Add tests

Create:

- `cajas/tests/test_validation_eurusd_pattern_review_batch_merge.py`

Update:

- `cajas/tests/test_validation_eurusd_pattern_review_feedback.py`
- `cajas/tests/test_validation_eurusd_pattern_review_summary.py`
- `cajas/tests/test_validation_eurusd_research_readiness.py`

Test scenarios:

1. Missing completed batch:
   - merge status `awaiting_completed_batch`
   - blocking false
   - merge_performed false

2. Valid completed batch and no existing full completed review:
   - merge status `ready`
   - creates full completed review
   - reviewed_count_added > 0

3. Valid completed batch and existing full completed review:
   - merge by `sample_id`
   - does not duplicate rows
   - updates existing rows where appropriate
   - writes backup path

4. Invalid completed batch:
   - merge status `blocked`
   - merge_performed false

5. Forbidden trading/action column:
   - merge status `blocked`

6. Feedback after merged completed review:
   - feedback status ready/watch
   - reviewed count matches merged file

7. Summary after merged completed review:
   - candidate type summary generated

8. Readiness with merge awaiting:
   - next_action `fill_batch_001_review`
   - non-blocking

9. Readiness with merge ready:
   - merge status surfaced
   - next action moves to review summary / continue review

10. Readiness with merge blocked:
   - readiness blocked

### 6. Documentation

Update:

- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `cajas/docs/dataset_quality_loop.md`
- `cajas/docs/current_qlib_base_stage_archive.md`
- `cajas/README.md`

Document:

- how to fill:
  - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv`
- save completed batch as:
  - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv`
- merge result path:
  - `tmp/eurusd/EURUSD_15m_pattern_review_completed.csv`
- feedback report path:
  - `tmp/validation-eurusd-pattern-review-feedback.json/.md`
- summary report path:
  - `tmp/validation-eurusd-pattern-review-summary.json/.md`
- missing completed batch is normal and non-blocking
- no labels should be invented by automation
- no trading signals/orders/model training are produced

### 7. Generate artifacts

Run current completion report first:

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

Regenerate EURUSD research readiness with the batch merge, feedback, and summary reports.

Expected outputs:

- `tmp/validation-eurusd-pattern-review-batch-001-merge.json/.md`
- regenerated:
  - `tmp/validation-eurusd-pattern-review-batch-001-completion.json/.md`
  - `tmp/validation-eurusd-pattern-review-feedback.json/.md`
  - `tmp/validation-eurusd-pattern-review-summary.json/.md`
  - `tmp/validation-eurusd-research-readiness.json/.md`

If completed batch is still missing, expected status remains:

- batch completion: `awaiting_completed_batch`
- merge: `awaiting_completed_batch`
- feedback: `awaiting_review_input`
- summary: `awaiting_review_input`
- readiness next action: `fill_batch_001_review`

### 8. Validation

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest   cajas/tests/test_validation_eurusd_pattern_review_batch_merge.py   cajas/tests/test_validation_eurusd_pattern_review_batch_completion.py   cajas/tests/test_validation_eurusd_pattern_review_feedback.py   cajas/tests/test_validation_eurusd_pattern_review_summary.py   cajas/tests/test_validation_eurusd_research_readiness.py
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

## Branch / Commit Guidance

Continue on the current EURUSD branch if it has not been merged yet:

```bash
git checkout phase-eurusd-pattern-research-kickoff
git status --short --branch
```

If the previous branch has already been merged, start from latest main:

```bash
git checkout main
git pull origin main
git checkout -b phase-eurusd-15m-completed-batch-intake
```

Suggested commits:

```bash
git add   cajas/reports/validation_eurusd_pattern_review_batch_merge.py   cajas/scripts/build_eurusd_pattern_review_batch_merge_report.py   cajas/tests/test_validation_eurusd_pattern_review_batch_merge.py

git commit -m "feat: add EURUSD review batch merge workflow"

git add   cajas/reports/validation_eurusd_pattern_review_feedback.py   cajas/reports/validation_eurusd_pattern_review_summary.py   cajas/reports/validation_eurusd_research_readiness.py   cajas/scripts/build_eurusd_research_readiness_report.py   cajas/tests/test_validation_eurusd_pattern_review_feedback.py   cajas/tests/test_validation_eurusd_pattern_review_summary.py   cajas/tests/test_validation_eurusd_research_readiness.py

git commit -m "feat: integrate EURUSD completed review summaries"

git add   cajas/docs/eurusd_pattern_research_kickoff.md   cajas/docs/current_qlib_base_stage_archive.md   cajas/docs/dataset_quality_loop.md   cajas/README.md   tasks/phase_5846_5965_eurusd_15m_completed_batch_intake_prompt.md

git commit -m "docs: document EURUSD completed batch intake"
```

Do not perform automated merge operations.

If ready, push the branch and tell the human user to merge manually on GitHub:

```bash
git push origin phase-eurusd-pattern-research-kickoff
```

or, if using a new branch:

```bash
git push origin phase-eurusd-15m-completed-batch-intake
```

## Final Response Required

When finished, report:

- active branch
- commits created
- files changed
- generated artifacts
- batch completion status
- batch merge status
- reviewed count
- pending count
- feedback status
- summary status
- EURUSD research readiness status
- next recommended action
- validation results
- fast validation runtime
- push status
- manual GitHub merge instruction
- confirmation that no labels were invented
- confirmation that no trading signals/orders/model training were produced
- confirmation that no automated merge was performed
