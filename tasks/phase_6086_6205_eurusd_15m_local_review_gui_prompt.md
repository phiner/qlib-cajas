# Phase 6086–6205 — EURUSD 15m Local GUI Pattern Review App

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

Current review workflow state:

- Pattern candidate pack exists.
- Review template exists.
- First review batch exists:
  - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv`
  - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001.jsonl`
- Review guide exists:
  - `tmp/validation-eurusd-pattern-review-guide.md`
- Batch completion currently awaits human input:
  - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv`
- Existing CSV/JSONL workflow is functionally correct but not ergonomic.
- Human user explicitly rejected text/CSV-only and static HTML-only workflows as too primitive.
- Human user wants a real local GUI to:
  - display generated/candidate patterns on charts
  - review samples visually
  - enter labels in a form
  - automatically write back completed review data

Important design decision:

- CSV/JSONL remain storage and interchange formats.
- GUI becomes the primary human review interface.
- This should be a local offline app, not a deployed web service.
- No live market data, broker integration, order execution, or model training.

## Goal

Build a minimal local GUI review app for EURUSD 15m pattern annotation.

The app should let a human:

1. Load the clean EURUSD 15m Bid dataset.
2. Load the first review batch.
3. Navigate sample-by-sample.
4. See an interactive candlestick chart around the sample timestamp.
5. See candidate metadata/reason codes/supporting metrics.
6. Fill the review label schema fields.
7. Save progress automatically or by explicit Save button.
8. Write/update:
   - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv`
9. Resume later without losing progress.
10. Run fully offline.

This phase should create the first usable local GUI, not a perfect production app.

## Recommended Stack

Use Streamlit + Plotly unless there is a strong repo-specific reason not to.

Rationale:

- Streamlit is quick for local Python data apps.
- Plotly supports interactive candlestick charts.
- Existing repo is Python/report-centric.
- The GUI can read/write the existing CSV artifacts.
- The app can run locally with one command.

Do not build a complex custom frontend in this phase.

Do not require Label Studio in this phase. Label Studio may remain a future integration option, but the first app should be custom because the current review schema and candidate metadata are already repository-specific.

## Required Work

### 1. Add GUI app module

Create:

`cajas/apps/eurusd_pattern_review_app.py`

If `cajas/apps/` does not exist, create it without adding `__init__.py` if the project hygiene policy forbids it.

The app should be runnable with:

```bash
./.venv-qlib313/bin/python -m streamlit run cajas/apps/eurusd_pattern_review_app.py
```

If Streamlit is not currently installed in the environment, do not break validation. Add graceful dependency handling and documentation.

App inputs/default paths:

```text
clean_view_csv = tmp/eurusd/EURUSD_15m_Bid_clean_view.csv
review_batch_csv = tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv
completed_output_csv = tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv
label_schema_json = tmp/validation-eurusd-pattern-label-schema.json
```

The app should also allow overriding paths from sidebar text inputs.

### 2. Add chart rendering helper

Create:

`cajas/research/eurusd_pattern_review_gui.py`

Responsibilities:

- Load clean view CSV.
- Load review batch CSV.
- Load existing completed output CSV if available.
- Merge completed labels into current sample state by `sample_id`.
- Extract chart window around sample timestamp.
- Build Plotly candlestick figure.
- Add visual marker for target sample bar.
- Optionally display:
  - lookback bars default 60
  - forward bars default 30
  - candidate type
  - confidence
  - reason codes
- Provide save/update helpers for completed review CSV.
- Do not mutate raw/clean input files.

### 3. GUI layout requirements

The local app should include:

Sidebar:

- path inputs
- load/reload button
- candidate type filter
- review status filter:
  - all
  - pending
  - reviewed
  - skipped
- sample selector:
  - by index
  - previous/next buttons if easy
- progress summary:
  - total
  - reviewed
  - pending
  - skipped

Main area:

- chart title with:
  - sample_id
  - timestamp
  - candidate_type
- Plotly candlestick chart
- candidate metadata:
  - confidence_score
  - review_priority
  - reason_codes
  - supporting metrics
- form fields:
  - `human_pattern_label`
  - `market_context`
  - `direction_context`
  - `structure_quality`
  - `follow_through_quality`
  - `review_confidence`
  - `review_notes`
  - `review_status`
- Save button:
  - writes/updates completed output CSV
- Save and Next button if simple
- Clear/Reset current form button if simple

Allowed label values should be read from schema when possible, with safe fallback values matching `eurusd_15m_pattern_review_v1`.

### 4. Completed output behavior

The app must write:

`tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv`

Rules:

- One row per reviewed/skipped/pending sample from the batch.
- Preserve sample identity and candidate metadata columns.
- Add or update human review fields.
- Use `sample_id` as stable key.
- Do not duplicate sample rows.
- Do not write forbidden trading/action columns:
  - `buy`, `sell`, `long`, `short`, `order`, `position`, `target_position`, `signal`, `entry`, `exit`
- Do not auto-invent labels.
- Only save values selected/entered by the human.
- If output file exists, load it and resume progress.

### 5. Add GUI validation/report

Create:

`cajas/reports/validation_eurusd_pattern_review_gui.py`

This report should validate that the GUI workflow files exist and that the app module/helpers can be imported.

Report fields:

- `status`
  - `ready`
  - `watch`
  - `blocked`
- `app_path`
- `helper_path`
- `streamlit_available`
- `plotly_available`
- `input_batch_path`
- `clean_view_path`
- `completed_output_path`
- `can_import_app`
- `can_import_helper`
- `forbidden_trading_column_policy`
- `run_command`
- `recommendation`
  - expected: `run_local_review_app`

Status rules:

- `ready` if app/helper import and dependencies are available.
- `watch` if app/helper import but optional GUI dependency is missing; app should still fail gracefully with instructions.
- `blocked` if app/helper cannot import or required input artifacts are missing.

Generated artifacts:

- `tmp/validation-eurusd-pattern-review-gui.json`
- `tmp/validation-eurusd-pattern-review-gui.md`

### 6. Add CLI builder

Create:

`cajas/scripts/build_eurusd_pattern_review_gui_report.py`

Defaults:

```text
--app-path cajas/apps/eurusd_pattern_review_app.py
--clean-view-csv tmp/eurusd/EURUSD_15m_Bid_clean_view.csv
--review-batch-csv tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv
--completed-output-csv tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv
--output-json tmp/validation-eurusd-pattern-review-gui.json
--output-md tmp/validation-eurusd-pattern-review-gui.md
```

### 7. Add tests

Create:

- `cajas/tests/test_eurusd_pattern_review_gui.py`
- `cajas/tests/test_validation_eurusd_pattern_review_gui.py`

Test scenarios:

1. Helper loads a clean view and batch fixture.
2. Helper extracts chart window around timestamp.
3. Helper merges completed labels by sample_id without duplicates.
4. Helper save/update creates completed CSV.
5. Forbidden trading/action columns are not written.
6. Missing optional Streamlit dependency does not break non-GUI tests.
7. GUI validation report returns ready/watch appropriately.
8. App module has a clear `main()` or guarded execution path.
9. Label schema fallback values are stable.

Important:

- Do not require launching Streamlit during tests.
- Do not require browser automation.
- Do not require real GUI interaction in tests.
- Tests should validate pure helper functions and report behavior.

### 8. Integrate with EURUSD research readiness

Update:

- `cajas/reports/validation_eurusd_research_readiness.py`
- `cajas/scripts/build_eurusd_research_readiness_report.py`
- `cajas/tests/test_validation_eurusd_research_readiness.py`

Add optional input:

- pattern review GUI report

Expected behavior:

- If GUI report is ready/watch:
  - include `pattern_review_gui_status`
  - include `review_app_run_command`
  - set next_action to `run_local_review_app` when review input is still awaiting
- If GUI report is blocked:
  - readiness may become `blocked` only if GUI workflow is explicitly required by CLI args; otherwise surface as warning.
- Missing GUI report should not break existing readiness.

### 9. Documentation

Update:

- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `cajas/docs/dataset_quality_loop.md`
- `cajas/docs/current_qlib_base_stage_archive.md`
- `cajas/README.md`

Document:

- why GUI review app exists
- run command:
  - `./.venv-qlib313/bin/python -m streamlit run cajas/apps/eurusd_pattern_review_app.py`
- input paths
- output completed review path
- how to review:
  1. start app
  2. choose sample
  3. inspect chart
  4. fill labels
  5. save
  6. continue
  7. later run completed-batch intake
- no trading/order/model-training scope
- CSV remains durable storage, GUI is the human interface

If Streamlit/Plotly are not in requirements, document installation separately rather than silently changing heavy dependencies. If adding dependencies is acceptable in this repo, update the appropriate requirements file minimally.

### 10. Generate artifacts

Run GUI report builder:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_eurusd_pattern_review_gui_report.py   --app-path cajas/apps/eurusd_pattern_review_app.py   --clean-view-csv tmp/eurusd/EURUSD_15m_Bid_clean_view.csv   --review-batch-csv tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv   --completed-output-csv tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv   --output-json tmp/validation-eurusd-pattern-review-gui.json   --output-md tmp/validation-eurusd-pattern-review-gui.md
```

Regenerate EURUSD research readiness with GUI report input.

Expected outputs:

- `tmp/validation-eurusd-pattern-review-gui.json`
- `tmp/validation-eurusd-pattern-review-gui.md`
- regenerated:
  - `tmp/validation-eurusd-research-readiness.json/.md`

### 11. Validation

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest   cajas/tests/test_eurusd_pattern_review_gui.py   cajas/tests/test_validation_eurusd_pattern_review_gui.py   cajas/tests/test_validation_eurusd_research_readiness.py
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
git checkout -b phase-eurusd-15m-local-review-gui
```

Suggested commits:

```bash
git add   cajas/apps/eurusd_pattern_review_app.py   cajas/research/eurusd_pattern_review_gui.py   cajas/tests/test_eurusd_pattern_review_gui.py

git commit -m "feat: add EURUSD local pattern review GUI"

git add   cajas/reports/validation_eurusd_pattern_review_gui.py   cajas/scripts/build_eurusd_pattern_review_gui_report.py   cajas/tests/test_validation_eurusd_pattern_review_gui.py   cajas/reports/validation_eurusd_research_readiness.py   cajas/scripts/build_eurusd_research_readiness_report.py   cajas/tests/test_validation_eurusd_research_readiness.py

git commit -m "feat: surface EURUSD GUI review readiness"

git add   cajas/docs/eurusd_pattern_research_kickoff.md   cajas/docs/current_qlib_base_stage_archive.md   cajas/docs/dataset_quality_loop.md   cajas/README.md   tasks/phase_6086_6205_eurusd_15m_local_review_gui_prompt.md

git commit -m "docs: document EURUSD local review GUI"
```

Do not perform automated merge operations.

If ready, push the branch and tell the human user to merge manually on GitHub:

```bash
git push origin phase-eurusd-pattern-research-kickoff
```

or, if using a new branch:

```bash
git push origin phase-eurusd-15m-local-review-gui
```

## Final Response Required

When finished, report:

- active branch
- commits created
- files changed
- generated artifacts
- GUI report status
- Streamlit availability
- Plotly availability
- run command
- completed review output path
- EURUSD research readiness status
- next recommended action
- validation results
- fast validation runtime
- push status
- manual GitHub merge instruction
- confirmation that CSV remains durable storage and GUI is the review interface
- confirmation that no labels were invented
- confirmation that no trading signals/orders/model training were produced
- confirmation that no automated merge was performed
