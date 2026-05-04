# Phase 5606–5725 — EURUSD 15m Human Review Feedback Intake and Summary

## Context

You are working in the Qlib Base / qlib-cajas repository.

The active research objective is EURUSD 15m Bid pattern research.

Current baseline:

- Active branch used so far: `phase-eurusd-pattern-research-kickoff`
- Research timeframe fixed to `15m`
- Price side: `Bid`
- Do not aggregate to 1H/4H.
- Do not introduce live trading, paper trading, broker routing, order generation, or Qlib core modifications.
- Raw EURUSD CSV files are immutable.
- Clean view is approved for pattern research:
  - `tmp/eurusd/EURUSD_15m_Bid_clean_view.csv`
- EURUSD research readiness:
  - `ready_for_pattern_research_with_clean_view`

Current candidate/review state from Phase 5366–5485 and Phase 5486–5605:

- Pattern candidate pack status: `ready`
- Total candidates: `206492`
- Review samples:
  - `500` rows total
  - `50` per candidate type
  - `10` candidate types
- Review template generated:
  - `tmp/eurusd/EURUSD_15m_pattern_review_template.csv`
  - `tmp/eurusd/EURUSD_15m_pattern_review_template.jsonl`
- Pattern review QA status: `ready`
- Label schema status: `ready`
- Label schema version:
  - `eurusd_15m_pattern_review_v1`
- Review template status: `ready`
- Next action from readiness:
  - `begin_human_pattern_review`

Important: This phase should prepare the feedback intake and summary layer. It should not assume that the human has already completed review unless a reviewed file is provided. It should not produce strategy signals.

## Goal

Create a deterministic human review feedback intake and summary layer for EURUSD 15m pattern review templates.

This phase should make it possible to:

1. Validate a human-reviewed template file.
2. Summarize review progress and label distributions.
3. Identify high-quality pattern examples and false-positive candidate types.
4. Generate artifacts that guide the next research step.
5. Keep everything offline, review-only, and non-trading.

## Expected Human Review Input

Default reviewed input path:

`tmp/eurusd/EURUSD_15m_pattern_review_completed.csv`

This file may not exist yet.

If it does not exist:

- produce a status such as `awaiting_review_input`
- do not fail fast validation
- preserve the review template as the next required human action

If it exists:

- validate it against schema version `eurusd_15m_pattern_review_v1`
- summarize labels and review progress

## Required Work

### 1. Add human review feedback validator

Create:

`cajas/reports/validation_eurusd_pattern_review_feedback.py`

Inputs:

- review template CSV or JSONL
- optional completed review CSV
- label schema JSON

Default paths:

- template:
  - `tmp/eurusd/EURUSD_15m_pattern_review_template.csv`
- completed review:
  - `tmp/eurusd/EURUSD_15m_pattern_review_completed.csv`
- schema:
  - `tmp/validation-eurusd-pattern-label-schema.json`

Required behavior:

If completed review file is missing:

- status: `awaiting_review_input`
- blocking: `false`
- reviewed_count: `0`
- pending_count: template row count
- next_action: `complete_human_review_template`

If completed review file exists:

Validate:

- required identity fields exist:
  - `sample_id`
  - `timestamp`
  - `candidate_type`
  - `schema_version`
- required review fields exist:
  - `human_pattern_label`
  - `market_context`
  - `direction_context`
  - `structure_quality`
  - `follow_through_quality`
  - `review_confidence`
  - `review_status`
- schema_version matches `eurusd_15m_pattern_review_v1`
- enum values match allowed schema values
- numeric fields are in allowed ranges
- no duplicate `sample_id`
- completed rows correspond to template sample IDs
- forbidden trading/action columns absent:
  - `buy`, `sell`, `long`, `short`, `order`, `position`, `target_position`, `signal`, `entry`, `exit`
- review_status values are allowed:
  - `pending`
  - `reviewed`
  - `skipped`
- rows with `review_status=reviewed` should have non-empty review labels
- rows with invalid schema values should be reported but not hidden

Report fields:

- `status`
  - `awaiting_review_input`
  - `ready`
  - `watch`
  - `blocked`
- `blocking`
- `schema_version`
- `template_row_count`
- `completed_row_count`
- `reviewed_count`
- `pending_count`
- `skipped_count`
- `invalid_row_count`
- `duplicate_sample_id_count`
- `unknown_sample_id_count`
- `forbidden_trading_column_hits`
- `label_distribution`
- `candidate_type_review_progress`
- `review_confidence_distribution`
- `quality_score_summary`
- `next_action`
  - `complete_human_review_template`
  - `summarize_review_feedback`
  - `fix_review_file`

Generated artifacts:

- `tmp/validation-eurusd-pattern-review-feedback.json`
- `tmp/validation-eurusd-pattern-review-feedback.md`

### 2. Add review feedback summary report

Create:

`cajas/reports/validation_eurusd_pattern_review_summary.py`

Inputs:

- feedback validation report
- completed review CSV if available
- candidate pack report if useful

Behavior:

If feedback status is `awaiting_review_input`:

- status: `awaiting_review_input`
- recommendation: `complete_review_template_first`
- no strategy/ML recommendation yet

If feedback status is `ready` or `watch`:

Summarize:

- reviewed rows by candidate type
- valid/weak/false-positive/unclear rates by candidate type
- average structure quality by candidate type
- average follow-through quality by candidate type
- average review confidence by candidate type
- high-confidence valid examples
- high-confidence false positives
- candidate types needing more review
- suggested next research action:
  - `expand_review_samples`
  - `analyze_valid_pattern_outcomes`
  - `refine_candidate_rules`
  - `continue_manual_review`

Report fields:

- `status`
  - `awaiting_review_input`
  - `ready`
  - `watch`
  - `blocked`
- `reviewed_count`
- `minimum_review_threshold`
  - default: `100`
- `candidate_type_summary`
- `top_valid_pattern_types`
- `top_false_positive_types`
- `high_confidence_examples`
- `needs_more_review`
- `recommendation`
- `scope_boundary`
  - review feedback only
  - no trading signals
  - no order generation
  - no model training in this phase

Generated artifacts:

- `tmp/validation-eurusd-pattern-review-summary.json`
- `tmp/validation-eurusd-pattern-review-summary.md`

### 3. Add CLI builders

Create:

- `cajas/scripts/build_eurusd_pattern_review_feedback_report.py`
- `cajas/scripts/build_eurusd_pattern_review_summary_report.py`

CLI defaults:

Feedback report:

```text
--template-csv tmp/eurusd/EURUSD_15m_pattern_review_template.csv
--completed-review-csv tmp/eurusd/EURUSD_15m_pattern_review_completed.csv
--label-schema tmp/validation-eurusd-pattern-label-schema.json
--output-json tmp/validation-eurusd-pattern-review-feedback.json
--output-md tmp/validation-eurusd-pattern-review-feedback.md
```

Summary report:

```text
--feedback-report tmp/validation-eurusd-pattern-review-feedback.json
--completed-review-csv tmp/eurusd/EURUSD_15m_pattern_review_completed.csv
--candidate-pack-report tmp/validation-eurusd-pattern-candidate-pack.json
--output-json tmp/validation-eurusd-pattern-review-summary.json
--output-md tmp/validation-eurusd-pattern-review-summary.md
```

### 4. Add an example reviewed fixture, not real labels

Add a small example file for tests/docs only:

`cajas/data_examples/eurusd_pattern_review_completed.example.csv`

This should contain a few synthetic/example completed rows.

Do not pretend it represents real human review of the production sample pack.

### 5. Integrate with EURUSD research readiness

Update:

- `cajas/reports/validation_eurusd_research_readiness.py`
- `cajas/scripts/build_eurusd_research_readiness_report.py`
- `cajas/tests/test_validation_eurusd_research_readiness.py`

Add optional inputs for:

- review feedback report
- review summary report

Expected behavior:

- If feedback report is missing, keep current readiness:
  - `ready_for_pattern_research_with_clean_view`
  - next_action may remain `begin_human_pattern_review`
- If feedback report is `awaiting_review_input`:
  - readiness remains non-blocking
  - next_action: `complete_human_review_template`
- If feedback report is ready/watch:
  - include feedback summary fields
  - next_action based on summary recommendation
- If feedback report is blocked:
  - readiness should become `blocked`
  - reason: `review_feedback_blocked`

### 6. Add tests

Create:

- `cajas/tests/test_validation_eurusd_pattern_review_feedback.py`
- `cajas/tests/test_validation_eurusd_pattern_review_summary.py`

Update:

- `cajas/tests/test_validation_eurusd_research_readiness.py`

Test scenarios:

1. Missing completed review file:
   - feedback status `awaiting_review_input`
   - blocking false
   - pending count equals template count
   - next action `complete_human_review_template`

2. Valid completed review fixture:
   - feedback status `ready` or `watch`
   - reviewed count reported
   - label distribution reported

3. Invalid enum value:
   - feedback status `blocked`
   - invalid row count > 0

4. Duplicate sample ID:
   - feedback status `blocked` or `watch` according to severity
   - duplicate count reported

5. Forbidden trading/action columns:
   - feedback status `blocked`

6. Summary awaiting input:
   - summary status `awaiting_review_input`
   - recommendation `complete_review_template_first`

7. Summary with reviewed rows:
   - candidate type summaries generated
   - valid/false-positive rates reported

8. Readiness with awaiting feedback:
   - non-blocking
   - next_action `complete_human_review_template`

9. Readiness with blocked feedback:
   - blocked

### 7. Documentation

Update:

- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `cajas/docs/dataset_quality_loop.md`
- `cajas/docs/current_qlib_base_stage_archive.md`
- `cajas/README.md`

Document:

- how to copy or fill:
  - `tmp/eurusd/EURUSD_15m_pattern_review_template.csv`
- expected completed review path:
  - `tmp/eurusd/EURUSD_15m_pattern_review_completed.csv`
- label schema version:
  - `eurusd_15m_pattern_review_v1`
- feedback report outputs
- summary report outputs
- missing completed review is a normal non-blocking state
- no trading signals/orders/model training are produced

### 8. Generate artifacts

Run feedback report. Since completed review likely does not exist yet, expected status should be `awaiting_review_input`.

```bash
./.venv-qlib313/bin/python cajas/scripts/build_eurusd_pattern_review_feedback_report.py   --template-csv tmp/eurusd/EURUSD_15m_pattern_review_template.csv   --completed-review-csv tmp/eurusd/EURUSD_15m_pattern_review_completed.csv   --label-schema tmp/validation-eurusd-pattern-label-schema.json   --output-json tmp/validation-eurusd-pattern-review-feedback.json   --output-md tmp/validation-eurusd-pattern-review-feedback.md
```

Then:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_eurusd_pattern_review_summary_report.py   --feedback-report tmp/validation-eurusd-pattern-review-feedback.json   --completed-review-csv tmp/eurusd/EURUSD_15m_pattern_review_completed.csv   --candidate-pack-report tmp/validation-eurusd-pattern-candidate-pack.json   --output-json tmp/validation-eurusd-pattern-review-summary.json   --output-md tmp/validation-eurusd-pattern-review-summary.md
```

Regenerate EURUSD readiness with the feedback/summary reports.

Expected outputs:

- `tmp/validation-eurusd-pattern-review-feedback.json/.md`
- `tmp/validation-eurusd-pattern-review-summary.json/.md`
- regenerated `tmp/validation-eurusd-research-readiness.json/.md`

### 9. Validation

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest   cajas/tests/test_validation_eurusd_pattern_review_feedback.py   cajas/tests/test_validation_eurusd_pattern_review_summary.py   cajas/tests/test_validation_eurusd_research_readiness.py   cajas/tests/test_validation_eurusd_pattern_review_template.py   cajas/tests/test_validation_eurusd_pattern_label_schema.py
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
git checkout -b phase-eurusd-15m-review-feedback-intake
```

Suggested commits:

```bash
git add   cajas/reports/validation_eurusd_pattern_review_feedback.py   cajas/scripts/build_eurusd_pattern_review_feedback_report.py   cajas/tests/test_validation_eurusd_pattern_review_feedback.py   cajas/reports/validation_eurusd_pattern_review_summary.py   cajas/scripts/build_eurusd_pattern_review_summary_report.py   cajas/tests/test_validation_eurusd_pattern_review_summary.py   cajas/data_examples/eurusd_pattern_review_completed.example.csv

git commit -m "feat: add EURUSD pattern review feedback intake"

git add   cajas/reports/validation_eurusd_research_readiness.py   cajas/scripts/build_eurusd_research_readiness_report.py   cajas/tests/test_validation_eurusd_research_readiness.py

git commit -m "feat: surface EURUSD review feedback readiness"

git add   cajas/docs/eurusd_pattern_research_kickoff.md   cajas/docs/current_qlib_base_stage_archive.md   cajas/docs/dataset_quality_loop.md   cajas/README.md   tasks/phase_5606_5725_eurusd_15m_review_feedback_intake_prompt.md

git commit -m "docs: document EURUSD review feedback workflow"
```

Do not perform automated merge operations.

If ready, push the branch and tell the human user to merge manually on GitHub:

```bash
git push origin phase-eurusd-pattern-research-kickoff
```

or, if using a new branch:

```bash
git push origin phase-eurusd-15m-review-feedback-intake
```

## Final Response Required

When finished, report:

- active branch
- commits created
- files changed
- generated artifacts
- review feedback status
- reviewed count
- pending count
- review summary status
- EURUSD research readiness status
- next recommended action
- validation results
- fast validation runtime
- push status
- manual GitHub merge instruction
- confirmation that no trading signals/orders/model training were produced
- confirmation that no automated merge was performed
