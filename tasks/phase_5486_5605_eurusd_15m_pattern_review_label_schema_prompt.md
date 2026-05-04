# Phase 5486–5605 — EURUSD 15m Pattern Review Pack QA and Label Schema

## Context

You are working in the Qlib Base / qlib-cajas repository.

The active research objective is EURUSD 15m Bid pattern research.

Current baseline from prior phases:

- Raw EURUSD 15m Bid files:
  - `/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv`
  - `/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv`
- Research timeframe is fixed to `15m`.
- Do not aggregate to 1H/4H.
- Do not introduce live trading, paper trading, broker routing, order generation, or Qlib core modifications.
- Raw data has 10 OHLC anomalies and remains immutable.
- Clean view is approved for pattern research:
  - `tmp/eurusd/EURUSD_15m_Bid_clean_view.csv`
  - `tmp/eurusd/EURUSD_15m_Bid_quarantined_rows.csv`
- EURUSD research readiness:
  - `ready_for_pattern_research_with_clean_view`

Current pattern candidate pack from Phase 5366–5485:

- Candidate pack status: `ready`
- Candidate count: `206492`
- Candidate counts by type:
  - `short_trend_up_candidate`: `35289`
  - `short_trend_down_candidate`: `32361`
  - `possible_false_breakout_candidate`: `26987`
  - `lower_wick_rejection_candidate`: `26751`
  - `upper_wick_rejection_candidate`: `26419`
  - `doji_indecision_candidate`: `17891`
  - `mid_trend_up_candidate`: `15134`
  - `mid_trend_down_candidate`: `14176`
  - `expansion_candidate`: `8182`
  - `compression_candidate`: `3302`
- Balanced review samples:
  - `50` per type
  - `10` candidate types
- Candidate outputs:
  - `tmp/eurusd/EURUSD_15m_pattern_candidates.csv`
  - `tmp/eurusd/EURUSD_15m_pattern_review_samples.csv`
  - `tmp/eurusd/EURUSD_15m_pattern_review_samples.jsonl`
- Candidate tags are review-only.
- No trading signals/orders were produced.
- Fast validation from prior phase:
  - total `52.63s`
  - `pytest_fast=48.89s`

Important: This phase should help humans review candidate quality and define labels. It should not turn candidates into strategy signals.

## Goal

Create a deterministic Pattern Review QA and Label Schema layer for EURUSD 15m candidate samples.

The goal is to make the review pack usable for human inspection and future supervised labeling by adding:

1. Candidate sample QA checks.
2. A stable review label schema.
3. A review template/export for manual annotations.
4. Candidate quality summaries by type.
5. Readiness integration that says whether the sample pack is ready for human labeling.

## Required Work

### 1. Add pattern review QA report

Create:

`cajas/reports/validation_eurusd_pattern_review_qa.py`

Input artifacts:

- pattern candidates CSV
- pattern review samples CSV or JSONL
- candidate pack report JSON
- clean view report JSON if useful

The report should validate:

- required sample columns exist:
  - `timestamp`
  - `candidate_type`
  - `confidence_score`
  - `reason_codes`
  - `review_priority`
  - OHLC columns if present
- samples are balanced by candidate type according to expected max count
- no duplicate candidate sample rows by stable sample key
- confidence scores are in `[0, 1]`
- candidate types are known
- no trading action columns exist:
  - forbidden names include `buy`, `sell`, `long`, `short`, `order`, `position`, `target_position`, `signal`, `entry`, `exit`
- samples reference timestamps that exist in clean view when clean view is available
- sample count by type is reported
- candidate count by type is reported
- reason code coverage is reported
- review priority distribution is reported

Report fields:

- `status`
  - `ready` when QA passes
  - `watch` when QA passes but balance/sparsity warnings exist
  - `blocked` when required columns are missing, forbidden trading columns exist, confidence invalid, or samples cannot be loaded
- `sample_count`
- `candidate_count`
- `sample_count_by_type`
- `candidate_count_by_type`
- `known_candidate_types`
- `unknown_candidate_types`
- `duplicate_sample_count`
- `forbidden_trading_column_hits`
- `confidence_invalid_count`
- `missing_clean_view_timestamp_count`
- `reason_code_coverage`
- `review_priority_distribution`
- `recommendation`
  - expected happy path: `start_manual_review`

Generated artifacts:

- `tmp/validation-eurusd-pattern-review-qa.json`
- `tmp/validation-eurusd-pattern-review-qa.md`

### 2. Add review label schema

Create:

`cajas/reports/validation_eurusd_pattern_label_schema.py`

This should define and validate a stable manual review schema.

Suggested schema fields:

Core identity:

- `sample_id`
- `timestamp`
- `candidate_type`

Human labels:

- `human_pattern_label`
  - allowed examples:
    - `valid_pattern`
    - `weak_pattern`
    - `false_positive`
    - `unclear`
    - `skip_bad_context`
- `market_context`
  - allowed examples:
    - `trend`
    - `range`
    - `transition`
    - `high_volatility`
    - `low_volatility`
    - `unclear`
- `direction_context`
  - allowed examples:
    - `up`
    - `down`
    - `sideways`
    - `mixed`
    - `unclear`
- `structure_quality`
  - integer 1–5
- `follow_through_quality`
  - integer 1–5
- `review_confidence`
  - integer 1–5
- `review_notes`
  - free text

Optional future fields, but not required yet:

- `outcome_window_bars`
- `max_favorable_move`
- `max_adverse_move`
- `label_version`

Report fields:

- `status`
  - expected: `ready`
- `schema_version`
  - suggested: `eurusd_15m_pattern_review_v1`
- `required_fields`
- `allowed_values`
- `numeric_ranges`
- `defaults`
- `scope_boundary`
  - manual review labels only
  - no trading signal
  - no order generation
- `recommendation`
  - `use_schema_for_review_template`

Generated artifacts:

- `tmp/validation-eurusd-pattern-label-schema.json`
- `tmp/validation-eurusd-pattern-label-schema.md`

### 3. Add review template/export generator

Create:

`cajas/reports/validation_eurusd_pattern_review_template.py`

And CLI:

`cajas/scripts/build_eurusd_pattern_review_template.py`

Inputs:

- pattern review samples CSV or JSONL
- label schema JSON

Outputs:

- `tmp/eurusd/EURUSD_15m_pattern_review_template.csv`
- `tmp/eurusd/EURUSD_15m_pattern_review_template.jsonl`
- `tmp/validation-eurusd-pattern-review-template.json`
- `tmp/validation-eurusd-pattern-review-template.md`

Template behavior:

- copy stable sample identity and candidate context fields:
  - `sample_id`
  - `timestamp`
  - `candidate_type`
  - `confidence_score`
  - `review_priority`
  - `reason_codes`
  - key supporting metrics
- append empty/default human review fields from label schema
- include `schema_version`
- include `review_status`
  - default: `pending`
- do not include buy/sell/order/signal fields
- preserve deterministic ordering:
  - candidate_type
  - review_priority descending or stable priority order
  - confidence_score descending
  - timestamp ascending

Report fields:

- `status`
  - `ready` if template generated and schema is ready
  - `blocked` if samples/schema missing or invalid
- `template_row_count`
- `schema_version`
- `candidate_types`
- `output_paths`
- `forbidden_trading_column_hits`
- `recommendation`
  - `begin_human_review`

### 4. Add CLI builders

Create:

- `cajas/scripts/build_eurusd_pattern_review_qa_report.py`
- `cajas/scripts/build_eurusd_pattern_label_schema_report.py`
- `cajas/scripts/build_eurusd_pattern_review_template.py`

CLI defaults should use current artifacts:

```text
tmp/eurusd/EURUSD_15m_pattern_candidates.csv
tmp/eurusd/EURUSD_15m_pattern_review_samples.csv
tmp/eurusd/EURUSD_15m_pattern_review_samples.jsonl
tmp/validation-eurusd-pattern-candidate-pack.json
tmp/eurusd/EURUSD_15m_Bid_clean_view.csv
```

### 5. Integrate with EURUSD research readiness

Update:

- `cajas/reports/validation_eurusd_research_readiness.py`
- `cajas/scripts/build_eurusd_research_readiness_report.py`
- `cajas/tests/test_validation_eurusd_research_readiness.py`

Add optional inputs for:

- pattern review QA report
- pattern label schema report
- pattern review template report

Expected readiness behavior:

- If data readiness is `ready_for_pattern_research_with_clean_view`
- and candidate pack is ready/watch
- and review QA is ready/watch
- and label schema is ready
- and review template is ready
- then include:
  - `review_qa_status`
  - `label_schema_status`
  - `review_template_status`
  - `next_action=begin_human_pattern_review`
- Do not downgrade clean-view readiness if review template is absent unless explicitly requested.
- If provided review QA/template is blocked, readiness should become `blocked`.

### 6. Add tests

Create tests:

- `cajas/tests/test_validation_eurusd_pattern_review_qa.py`
- `cajas/tests/test_validation_eurusd_pattern_label_schema.py`
- `cajas/tests/test_validation_eurusd_pattern_review_template.py`

Update:

- `cajas/tests/test_validation_eurusd_research_readiness.py`

Test scenarios:

1. QA ready on valid candidate/sample fixtures.
2. QA blocked when forbidden trading columns exist.
3. QA blocked when confidence score is outside `[0, 1]`.
4. QA detects duplicate sample rows.
5. Label schema report is ready and contains expected schema version.
6. Label schema has allowed values and numeric ranges.
7. Review template generated with expected rows and pending review status.
8. Review template includes schema version.
9. Review template excludes forbidden trading/action columns.
10. Research readiness includes next action `begin_human_pattern_review` when all review artifacts are ready.

### 7. Documentation

Update:

- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `cajas/docs/dataset_quality_loop.md`
- `cajas/docs/current_qlib_base_stage_archive.md`
- `cajas/README.md`

Document:

- candidate samples are now ready for QA/human review
- label schema version
- template output paths
- how human review should be performed
- fixed EURUSD 15m Bid timeframe
- clean view remains the approved research input
- no aggregation
- no trading signals/orders
- no broker/live/paper trading

### 8. Generate real artifacts

Run the builders against current candidate sample artifacts:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_eurusd_pattern_review_qa_report.py   --candidates-csv tmp/eurusd/EURUSD_15m_pattern_candidates.csv   --samples-csv tmp/eurusd/EURUSD_15m_pattern_review_samples.csv   --candidate-pack-report tmp/validation-eurusd-pattern-candidate-pack.json   --clean-view-csv tmp/eurusd/EURUSD_15m_Bid_clean_view.csv   --output-json tmp/validation-eurusd-pattern-review-qa.json   --output-md tmp/validation-eurusd-pattern-review-qa.md
```

```bash
./.venv-qlib313/bin/python cajas/scripts/build_eurusd_pattern_label_schema_report.py   --output-json tmp/validation-eurusd-pattern-label-schema.json   --output-md tmp/validation-eurusd-pattern-label-schema.md
```

```bash
./.venv-qlib313/bin/python cajas/scripts/build_eurusd_pattern_review_template.py   --samples-csv tmp/eurusd/EURUSD_15m_pattern_review_samples.csv   --label-schema tmp/validation-eurusd-pattern-label-schema.json   --output-template-csv tmp/eurusd/EURUSD_15m_pattern_review_template.csv   --output-template-jsonl tmp/eurusd/EURUSD_15m_pattern_review_template.jsonl   --output-json tmp/validation-eurusd-pattern-review-template.json   --output-md tmp/validation-eurusd-pattern-review-template.md
```

Then regenerate EURUSD research readiness with the new optional review artifacts.

Expected outputs:

- `tmp/validation-eurusd-pattern-review-qa.json/.md`
- `tmp/validation-eurusd-pattern-label-schema.json/.md`
- `tmp/validation-eurusd-pattern-review-template.json/.md`
- `tmp/eurusd/EURUSD_15m_pattern_review_template.csv`
- `tmp/eurusd/EURUSD_15m_pattern_review_template.jsonl`
- regenerated `tmp/validation-eurusd-research-readiness.json/.md`

### 9. Validation

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest   cajas/tests/test_validation_eurusd_pattern_review_qa.py   cajas/tests/test_validation_eurusd_pattern_label_schema.py   cajas/tests/test_validation_eurusd_pattern_review_template.py   cajas/tests/test_validation_eurusd_research_readiness.py   cajas/tests/test_validation_eurusd_pattern_candidate_pack.py   cajas/tests/test_eurusd_pattern_candidates.py
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
git checkout -b phase-eurusd-15m-pattern-review-label-schema
```

Suggested commits:

```bash
git add   cajas/reports/validation_eurusd_pattern_review_qa.py   cajas/scripts/build_eurusd_pattern_review_qa_report.py   cajas/tests/test_validation_eurusd_pattern_review_qa.py   cajas/reports/validation_eurusd_pattern_label_schema.py   cajas/scripts/build_eurusd_pattern_label_schema_report.py   cajas/tests/test_validation_eurusd_pattern_label_schema.py   cajas/reports/validation_eurusd_pattern_review_template.py   cajas/scripts/build_eurusd_pattern_review_template.py   cajas/tests/test_validation_eurusd_pattern_review_template.py

git commit -m "feat: add EURUSD pattern review QA and label schema"

git add   cajas/reports/validation_eurusd_research_readiness.py   cajas/scripts/build_eurusd_research_readiness_report.py   cajas/tests/test_validation_eurusd_research_readiness.py

git commit -m "feat: surface EURUSD pattern review readiness"

git add   cajas/docs/eurusd_pattern_research_kickoff.md   cajas/docs/current_qlib_base_stage_archive.md   cajas/docs/dataset_quality_loop.md   cajas/README.md   tasks/phase_5486_5605_eurusd_15m_pattern_review_label_schema_prompt.md

git commit -m "docs: document EURUSD pattern review workflow"
```

Do not perform automated merge operations.

If ready, push the branch and tell the human user to merge manually on GitHub:

```bash
git push origin phase-eurusd-pattern-research-kickoff
```

or, if using a new branch:

```bash
git push origin phase-eurusd-15m-pattern-review-label-schema
```

## Final Response Required

When finished, report:

- active branch
- commits created
- files changed
- generated artifacts
- pattern review QA status
- label schema status and schema version
- review template status
- review template row count
- review template output paths
- EURUSD research readiness status
- next recommended action
- validation results
- fast validation runtime
- push status
- manual GitHub merge instruction
- confirmation that no trading signals/orders were produced
- confirmation that no automated merge was performed
