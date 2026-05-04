# Phase 5726–5845 — EURUSD 15m Human Review Batch Guide and First Review Packet

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
- EURUSD research readiness:
  - `ready_for_pattern_research_with_clean_view`

Current sample/review state:

- Pattern candidate pack: `ready`
- Pattern review QA: `ready`
- Label schema: `ready`
- Label schema version:
  - `eurusd_15m_pattern_review_v1`
- Review template:
  - `ready`
  - row count: `500`
  - paths:
    - `tmp/eurusd/EURUSD_15m_pattern_review_template.csv`
    - `tmp/eurusd/EURUSD_15m_pattern_review_template.jsonl`
- Review feedback status:
  - `awaiting_review_input`
- Reviewed count:
  - `0`
- Pending count:
  - `500`
- Review summary status:
  - `awaiting_review_input`
- Current next action:
  - `complete_human_review_template`

Important: This phase should make human review easier and safer. It should not invent labels, auto-label samples, or convert candidates into trading signals.

## Goal

Create a human-friendly EURUSD 15m review batch workflow for the first manual review pass.

This phase should produce:

1. A smaller first review batch from the 500-row template.
2. A review guide explaining how to label samples consistently.
3. A batch manifest/report that tracks which rows were selected and why.
4. A safe completed-review placeholder file path and instructions.
5. Readiness integration that says human review can start with the first batch.

The aim is to help the human review 50–100 samples first, not force all 500 at once.

## Required Work

### 1. Add review batch builder

Create:

`cajas/reports/validation_eurusd_pattern_review_batch.py`

Inputs:

- full review template CSV:
  - `tmp/eurusd/EURUSD_15m_pattern_review_template.csv`
- label schema JSON:
  - `tmp/validation-eurusd-pattern-label-schema.json`
- optional batch size:
  - default: `100`
- optional per-type target:
  - default: `10`

Output:

- first review batch CSV:
  - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv`
- first review batch JSONL:
  - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001.jsonl`
- batch report:
  - `tmp/validation-eurusd-pattern-review-batch-001.json`
  - `tmp/validation-eurusd-pattern-review-batch-001.md`

Batch selection rules:

- Deterministic.
- Prefer balanced candidate types:
  - default 10 samples per candidate type across 10 candidate types = 100 rows.
- Within each candidate type, sort by:
  - review priority
  - confidence score descending
  - timestamp ascending
- Preserve all schema/review fields.
- Keep `review_status=pending`.
- Include sample identity fields.
- Do not include forbidden trading/action columns:
  - `buy`, `sell`, `long`, `short`, `order`, `position`, `target_position`, `signal`, `entry`, `exit`

Report fields:

- `status`
  - `ready`
  - `watch`
  - `blocked`
- `batch_id`
  - `eurusd_15m_pattern_review_batch_001`
- `schema_version`
- `template_row_count`
- `batch_row_count`
- `candidate_type_count`
- `batch_count_by_type`
- `selection_policy`
- `output_paths`
- `forbidden_trading_column_hits`
- `recommendation`
  - `review_batch_001`

Status rules:

- `ready` if batch is created and has rows.
- `watch` if some candidate types have fewer than requested rows.
- `blocked` if template/schema missing or forbidden trading columns exist.

### 2. Add CLI builder

Create:

`cajas/scripts/build_eurusd_pattern_review_batch.py`

CLI defaults:

```text
--template-csv tmp/eurusd/EURUSD_15m_pattern_review_template.csv
--label-schema tmp/validation-eurusd-pattern-label-schema.json
--batch-id eurusd_15m_pattern_review_batch_001
--batch-size 100
--per-type-target 10
--output-batch-csv tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv
--output-batch-jsonl tmp/eurusd/EURUSD_15m_pattern_review_batch_001.jsonl
--output-json tmp/validation-eurusd-pattern-review-batch-001.json
--output-md tmp/validation-eurusd-pattern-review-batch-001.md
```

### 3. Add human review guide report

Create:

`cajas/reports/validation_eurusd_pattern_review_guide.py`

The guide should be generated as JSON/Markdown and explain the label schema in practical language.

Outputs:

- `tmp/validation-eurusd-pattern-review-guide.json`
- `tmp/validation-eurusd-pattern-review-guide.md`

Guide content should include:

- scope:
  - EURUSD 15m Bid only
  - human review only
  - no trading signals
- how to fill:
  - `human_pattern_label`
  - `market_context`
  - `direction_context`
  - `structure_quality`
  - `follow_through_quality`
  - `review_confidence`
  - `review_notes`
  - `review_status`
- suggested interpretation:
  - `valid_pattern`
  - `weak_pattern`
  - `false_positive`
  - `unclear`
  - `skip_bad_context`
- rating rules:
  - 1 = poor/unclear
  - 3 = moderate
  - 5 = strong/clear
- review workflow:
  1. open batch CSV
  2. inspect timestamp/candidate type/reason codes/supporting metrics
  3. optionally inspect nearby bars in charting software
  4. fill human fields
  5. save completed batch as:
     - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv`
  6. later merge completed batch into:
     - `tmp/eurusd/EURUSD_15m_pattern_review_completed.csv`
- warning:
  - candidate tags are not trading actions
  - do not label based on hindsight profit only
  - focus on structure clarity and follow-through quality

Report fields:

- `status`
  - `ready`
- `schema_version`
- `batch_id`
- `guide_sections`
- `output_paths`
- `recommendation`
  - `start_batch_review`

### 4. Add completed batch placeholder validator

Create:

`cajas/reports/validation_eurusd_pattern_review_batch_completion.py`

Inputs:

- batch CSV:
  - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv`
- completed batch CSV:
  - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv`
- label schema JSON

Behavior:

If completed batch file is missing:

- status: `awaiting_completed_batch`
- blocking: `false`
- batch_row_count reported
- reviewed_count=0
- pending_count=batch_row_count
- next_action=`fill_batch_001_review`

If completed batch exists:

- validate same schema rules as feedback intake
- report reviewed/pending/skipped/invalid counts
- status:
  - `ready` if completed batch is valid and has reviewed rows
  - `watch` if partially reviewed
  - `blocked` if invalid schema/forbidden columns/etc.

Outputs:

- `tmp/validation-eurusd-pattern-review-batch-001-completion.json`
- `tmp/validation-eurusd-pattern-review-batch-001-completion.md`

### 5. Add CLI builders for guide and completion

Create:

- `cajas/scripts/build_eurusd_pattern_review_guide.py`
- `cajas/scripts/build_eurusd_pattern_review_batch_completion_report.py`

### 6. Integrate with EURUSD research readiness

Update:

- `cajas/reports/validation_eurusd_research_readiness.py`
- `cajas/scripts/build_eurusd_research_readiness_report.py`
- `cajas/tests/test_validation_eurusd_research_readiness.py`

Add optional inputs:

- review batch report
- review guide report
- review batch completion report

Expected readiness behavior:

- If review batch and guide are ready:
  - include `review_batch_status`
  - include `review_guide_status`
  - next_action=`review_batch_001`
- If batch completion is awaiting:
  - readiness remains non-blocking
  - next_action=`fill_batch_001_review`
- If batch completion is blocked:
  - readiness becomes `blocked`
  - reason=`review_batch_completion_blocked`

### 7. Add tests

Create:

- `cajas/tests/test_validation_eurusd_pattern_review_batch.py`
- `cajas/tests/test_validation_eurusd_pattern_review_guide.py`
- `cajas/tests/test_validation_eurusd_pattern_review_batch_completion.py`

Update:

- `cajas/tests/test_validation_eurusd_research_readiness.py`

Test scenarios:

1. Batch builder creates deterministic 100-row batch from balanced fixture.
2. Batch report ready and has expected candidate type counts.
3. Batch builder blocks on forbidden trading columns.
4. Guide report status ready and includes schema version.
5. Guide Markdown contains no trading signal instructions.
6. Completion report missing completed file:
   - status `awaiting_completed_batch`
   - blocking false
7. Completion report valid completed file:
   - status ready/watch
   - reviewed count reported
8. Completion report invalid enum:
   - blocked
9. Readiness with batch+guide ready:
   - next_action `review_batch_001`
10. Readiness with awaiting batch completion:
   - next_action `fill_batch_001_review`

### 8. Documentation

Update:

- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `cajas/docs/dataset_quality_loop.md`
- `cajas/docs/current_qlib_base_stage_archive.md`
- `cajas/README.md`

Document:

- first review batch output paths
- how to open/fill batch CSV
- completed batch expected path
- how batch completion differs from full review completion
- labels are structure review labels, not strategy labels
- no trading signals/orders/model training are produced

### 9. Generate artifacts

Run:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_eurusd_pattern_review_batch.py   --template-csv tmp/eurusd/EURUSD_15m_pattern_review_template.csv   --label-schema tmp/validation-eurusd-pattern-label-schema.json   --batch-id eurusd_15m_pattern_review_batch_001   --batch-size 100   --per-type-target 10   --output-batch-csv tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv   --output-batch-jsonl tmp/eurusd/EURUSD_15m_pattern_review_batch_001.jsonl   --output-json tmp/validation-eurusd-pattern-review-batch-001.json   --output-md tmp/validation-eurusd-pattern-review-batch-001.md
```

Then:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_eurusd_pattern_review_guide.py   --label-schema tmp/validation-eurusd-pattern-label-schema.json   --batch-report tmp/validation-eurusd-pattern-review-batch-001.json   --output-json tmp/validation-eurusd-pattern-review-guide.json   --output-md tmp/validation-eurusd-pattern-review-guide.md
```

Then:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_eurusd_pattern_review_batch_completion_report.py   --batch-csv tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv   --completed-batch-csv tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv   --label-schema tmp/validation-eurusd-pattern-label-schema.json   --output-json tmp/validation-eurusd-pattern-review-batch-001-completion.json   --output-md tmp/validation-eurusd-pattern-review-batch-001-completion.md
```

Regenerate EURUSD research readiness with the new review batch/guide/completion reports.

Expected outputs:

- `tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv`
- `tmp/eurusd/EURUSD_15m_pattern_review_batch_001.jsonl`
- `tmp/validation-eurusd-pattern-review-batch-001.json/.md`
- `tmp/validation-eurusd-pattern-review-guide.json/.md`
- `tmp/validation-eurusd-pattern-review-batch-001-completion.json/.md`
- regenerated `tmp/validation-eurusd-research-readiness.json/.md`

### 10. Validation

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest   cajas/tests/test_validation_eurusd_pattern_review_batch.py   cajas/tests/test_validation_eurusd_pattern_review_guide.py   cajas/tests/test_validation_eurusd_pattern_review_batch_completion.py   cajas/tests/test_validation_eurusd_research_readiness.py   cajas/tests/test_validation_eurusd_pattern_review_feedback.py
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
git checkout -b phase-eurusd-15m-review-batch-guide
```

Suggested commits:

```bash
git add   cajas/reports/validation_eurusd_pattern_review_batch.py   cajas/scripts/build_eurusd_pattern_review_batch.py   cajas/tests/test_validation_eurusd_pattern_review_batch.py   cajas/reports/validation_eurusd_pattern_review_guide.py   cajas/scripts/build_eurusd_pattern_review_guide.py   cajas/tests/test_validation_eurusd_pattern_review_guide.py   cajas/reports/validation_eurusd_pattern_review_batch_completion.py   cajas/scripts/build_eurusd_pattern_review_batch_completion_report.py   cajas/tests/test_validation_eurusd_pattern_review_batch_completion.py

git commit -m "feat: add EURUSD first review batch workflow"

git add   cajas/reports/validation_eurusd_research_readiness.py   cajas/scripts/build_eurusd_research_readiness_report.py   cajas/tests/test_validation_eurusd_research_readiness.py

git commit -m "feat: surface EURUSD review batch readiness"

git add   cajas/docs/eurusd_pattern_research_kickoff.md   cajas/docs/current_qlib_base_stage_archive.md   cajas/docs/dataset_quality_loop.md   cajas/README.md   tasks/phase_5726_5845_eurusd_15m_review_batch_guide_prompt.md

git commit -m "docs: document EURUSD first review batch"
```

Do not perform automated merge operations.

If ready, push the branch and tell the human user to merge manually on GitHub:

```bash
git push origin phase-eurusd-pattern-research-kickoff
```

or, if using a new branch:

```bash
git push origin phase-eurusd-15m-review-batch-guide
```

## Final Response Required

When finished, report:

- active branch
- commits created
- files changed
- generated artifacts
- review batch status
- batch row count
- batch counts by type
- review guide status
- batch completion status
- reviewed count
- pending count
- EURUSD research readiness status
- next recommended action
- validation results
- fast validation runtime
- push status
- manual GitHub merge instruction
- confirmation that no labels were invented
- confirmation that no trading signals/orders/model training were produced
- confirmation that no automated merge was performed
