# Phase 5246–5365 — EURUSD 15m Data Anomaly Triage and Clean Dataset View

## Context

You are working in the Qlib Base / qlib-cajas repository.

The project has returned from infrastructure maintenance to the original research objective:

- Study EURUSD historical data.
- Research K-line / candlestick forms, market structure, and offline strategy hypotheses.
- Work only on EURUSD 15m Bid data unless the human user explicitly requests otherwise.
- Do not aggregate to 1H/4H.
- Do not introduce live trading, paper trading, broker routing, order generation, or Qlib core modifications.

Current EURUSD research baseline from Phase 5126–5245:

- Branch: `phase-eurusd-pattern-research-kickoff`
- Dataset files:
  - `/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv`
  - `/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv`
- Combined coverage:
  - `149724` rows
  - `2020-01-01T22:00:00+00:00` to `2025-12-31T21:45:00+00:00`
  - `file_count=2`
- EURUSD dataset contract status: `ready`
- EURUSD dataset audit status: `blocked`
- EURUSD research readiness status: `blocked`
- Blocking reason:
  - 2020–2024 file has `10` real-data OHLC constraint violations
  - `invalid_ohlc_relation_count=10`
- Feature scaffold status: `pass`
- Existing features are deterministic and non-trading:
  - candle geometry
  - direction flags
  - 15m multi-horizon features over `3,5,8,13,21,34,55`
- Validation from prior phase passed:
  - focused EURUSD tests passed
  - fast validation total around `56.21s`
  - hygiene clean

Important: This phase should not hide or overwrite the raw data issue. It should triage and isolate it.

## Goal

Create an EURUSD 15m anomaly triage and clean dataset view layer.

The goal is to make the raw dataset issue reviewable and allow downstream pattern research to use a deterministic cleaned view without mutating the original CSV files.

This phase should produce:

1. A detailed invalid OHLC row report.
2. A quarantine list for bad bars.
3. A clean dataset view generator or report.
4. Updated EURUSD readiness behavior that distinguishes:
   - raw dataset audit blocked
   - cleaned view ready/watch
5. Documentation explaining how to proceed safely.

## Required Work

### 1. Add invalid OHLC triage report

Create:

`cajas/reports/validation_eurusd_ohlc_anomaly_triage.py`

The report should inspect one or more EURUSD 15m Bid CSV files and identify rows where OHLC constraints are violated.

Required detection rules:

- `high < open`
- `high < close`
- `high < low`
- `low > open`
- `low > close`
- `low > high`
- missing required OHLC values
- non-numeric OHLC values after normalization

For each anomaly row, include:

- source file path
- row index in source file
- normalized timestamp if available
- raw timestamp value
- open
- high
- low
- close
- violated constraints list
- severity:
  - `blocking`
- suggested action:
  - default: `quarantine_row`
- notes:
  - do not mutate original file

The report should also include:

- total input rows
- total anomaly rows
- anomaly count by file
- anomaly count by violation type
- earliest anomaly timestamp
- latest anomaly timestamp
- status:
  - `clean` if zero anomaly rows
  - `blocked` if anomaly rows exist
- recommendation:
  - `create_clean_view`

Generated artifacts:

- `tmp/validation-eurusd-ohlc-anomaly-triage.json`
- `tmp/validation-eurusd-ohlc-anomaly-triage.md`

### 2. Add CLI builder for anomaly triage

Create:

`cajas/scripts/build_eurusd_ohlc_anomaly_triage_report.py`

CLI requirements:

- supports repeated `--input` values for multiple CSV files
- supports explicit:
  - `--symbol EURUSD`
  - `--timeframe 15m`
  - `--price-side Bid`
  - `--output-json`
  - `--output-md`
- should not modify input files
- should work with real paths:
  - `/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv`
  - `/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv`

### 3. Add clean dataset view report / generator

Create:

`cajas/reports/validation_eurusd_clean_dataset_view.py`

The clean view should be deterministic and non-destructive.

Accept:

- raw dataset input paths
- anomaly triage report path
- output cleaned CSV path, default:
  - `tmp/eurusd/EURUSD_15m_Bid_clean_view.csv`
- output quarantine CSV path, default:
  - `tmp/eurusd/EURUSD_15m_Bid_quarantined_rows.csv`

Behavior:

- read all raw input files
- normalize schema as the audit currently does
- remove/quarantine rows listed in anomaly triage
- do not mutate raw files
- preserve source metadata:
  - source file
  - source row index
- write:
  - clean view CSV
  - quarantined rows CSV
  - JSON/Markdown report

Report fields:

- status:
  - `ready` if clean view has zero invalid OHLC rows after quarantine and enough rows
  - `watch` if clean view is valid but has gaps caused by quarantine
  - `blocked` if clean view still has invalid OHLC rows or cannot be generated
- raw_row_count
- quarantined_row_count
- clean_row_count
- removed_ratio
- clean_start_timestamp
- clean_end_timestamp
- clean_invalid_ohlc_relation_count
- clean_duplicate_timestamp_count
- gap summary after quarantine
- quarantine reason summary
- output paths
- recommendation:
  - `use_clean_view_for_pattern_research` when ready/watch non-blocking
  - `fix_dataset_source` when blocked

Generated artifacts:

- `tmp/validation-eurusd-clean-dataset-view.json`
- `tmp/validation-eurusd-clean-dataset-view.md`
- `tmp/eurusd/EURUSD_15m_Bid_clean_view.csv`
- `tmp/eurusd/EURUSD_15m_Bid_quarantined_rows.csv`

### 4. Add CLI builder for clean view

Create:

`cajas/scripts/build_eurusd_clean_dataset_view_report.py`

CLI requirements:

- repeated `--input`
- `--anomaly-triage-report`
- `--output-clean-csv`
- `--output-quarantine-csv`
- `--output-json`
- `--output-md`
- no raw input mutation

### 5. Update EURUSD dataset audit/readiness integration

Update existing EURUSD reports where appropriate:

- `cajas/reports/validation_eurusd_dataset_audit.py`
- `cajas/scripts/build_eurusd_dataset_audit_report.py`
- `cajas/reports/validation_eurusd_research_readiness.py`
- `cajas/scripts/build_eurusd_research_readiness_report.py`
- corresponding tests

Required behavior:

- Raw dataset audit may remain `blocked`.
- Clean dataset view can be `ready` or `watch`.
- EURUSD research readiness should support a clean-view input:
  - if raw audit is blocked only due quarantined OHLC anomalies,
  - and clean view is ready/watch non-blocking,
  - and feature scaffold is pass,
  - then readiness can be:
    - `ready_for_pattern_research_with_clean_view`
  - otherwise remain `blocked`.

Do not silently treat raw data as clean.

The readiness report should clearly state:

- raw dataset audit status
- clean dataset view status
- whether raw data is blocked
- whether clean view is approved for pattern research
- clean view path
- quarantine count

### 6. Add tests

Add tests for new modules:

- `cajas/tests/test_validation_eurusd_ohlc_anomaly_triage.py`
- `cajas/tests/test_validation_eurusd_clean_dataset_view.py`

Update existing tests:

- `cajas/tests/test_validation_eurusd_dataset_audit.py`
- `cajas/tests/test_validation_eurusd_research_readiness.py`

Test scenarios:

1. Triage happy path with clean fixture:
   - zero anomalies
   - status `clean`

2. Triage blocked fixture:
   - at least one row where high < close or low > open
   - status `blocked`
   - row-level details include timestamp, source row index, and violated constraints

3. Clean view fixture:
   - raw fixture has one invalid row
   - clean view removes exactly one row
   - quarantine CSV contains exactly one row
   - clean view status `ready` or `watch`

4. Clean view does not mutate raw input:
   - read raw fixture before and after
   - content unchanged

5. Readiness with raw blocked but clean view ready:
   - readiness status `ready_for_pattern_research_with_clean_view`
   - report contains raw blocked and clean view ready

6. Readiness remains blocked when clean view blocked.

7. Real-data smoke test is optional:
   - If real files exist at the known paths, run report generation against them.
   - Tests should not require real files to exist.

### 7. Documentation

Update:

- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `cajas/docs/dataset_quality_loop.md`
- `cajas/docs/current_qlib_base_stage_archive.md`
- `cajas/README.md`

Document:

- the raw EURUSD 15m Bid dataset currently has 10 OHLC anomalies in the 2020–2024 file
- raw dataset remains immutable
- anomaly rows are quarantined into a reviewable artifact
- clean view is allowed for pattern research only if the clean view report is ready/watch non-blocking
- all research remains 15m only
- no aggregation, no live trading, no broker routing, no order generation

### 8. Run real-data artifact generation

After implementation, generate artifacts using the real paths:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_eurusd_ohlc_anomaly_triage_report.py   --input "/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv"   --input "/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv"   --symbol EURUSD   --timeframe 15m   --price-side Bid   --output-json tmp/validation-eurusd-ohlc-anomaly-triage.json   --output-md tmp/validation-eurusd-ohlc-anomaly-triage.md
```

Then:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_eurusd_clean_dataset_view_report.py   --input "/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv"   --input "/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv"   --anomaly-triage-report tmp/validation-eurusd-ohlc-anomaly-triage.json   --output-clean-csv tmp/eurusd/EURUSD_15m_Bid_clean_view.csv   --output-quarantine-csv tmp/eurusd/EURUSD_15m_Bid_quarantined_rows.csv   --output-json tmp/validation-eurusd-clean-dataset-view.json   --output-md tmp/validation-eurusd-clean-dataset-view.md
```

Regenerate readiness with clean view input according to the implemented CLI.

### 9. Validation

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest   cajas/tests/test_validation_eurusd_ohlc_anomaly_triage.py   cajas/tests/test_validation_eurusd_clean_dataset_view.py   cajas/tests/test_validation_eurusd_dataset_audit.py   cajas/tests/test_validation_eurusd_research_readiness.py   cajas/tests/test_eurusd_pattern_features.py
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

Start from the current EURUSD kickoff branch if it has not been merged yet:

```bash
git checkout phase-eurusd-pattern-research-kickoff
git status --short --branch
```

If the kickoff branch has already been merged to main, start from latest main:

```bash
git checkout main
git pull origin main
git checkout -b phase-eurusd-15m-anomaly-triage-clean-view
```

Suggested commits:

```bash
git add   cajas/reports/validation_eurusd_ohlc_anomaly_triage.py   cajas/scripts/build_eurusd_ohlc_anomaly_triage_report.py   cajas/tests/test_validation_eurusd_ohlc_anomaly_triage.py   cajas/reports/validation_eurusd_clean_dataset_view.py   cajas/scripts/build_eurusd_clean_dataset_view_report.py   cajas/tests/test_validation_eurusd_clean_dataset_view.py

git commit -m "feat: add EURUSD 15m anomaly triage and clean view"

git add   cajas/reports/validation_eurusd_dataset_audit.py   cajas/scripts/build_eurusd_dataset_audit_report.py   cajas/reports/validation_eurusd_research_readiness.py   cajas/scripts/build_eurusd_research_readiness_report.py   cajas/tests/test_validation_eurusd_dataset_audit.py   cajas/tests/test_validation_eurusd_research_readiness.py

git commit -m "feat: support EURUSD clean-view research readiness"

git add   cajas/docs/eurusd_pattern_research_kickoff.md   cajas/docs/current_qlib_base_stage_archive.md   cajas/docs/dataset_quality_loop.md   cajas/README.md   tasks/phase_5246_5365_eurusd_15m_anomaly_triage_clean_view_prompt.md

git commit -m "docs: document EURUSD anomaly triage clean view"
```

Do not perform automated merge operations.

If ready, push the branch and tell the human user to merge manually on GitHub:

```bash
git push origin phase-eurusd-pattern-research-kickoff
```

or, if using a new branch:

```bash
git push origin phase-eurusd-15m-anomaly-triage-clean-view
```

## Final Response Required

When finished, report:

- active branch
- commits created
- files changed
- generated artifacts
- anomaly triage status
- anomaly row count
- anomaly timestamps summary
- clean dataset view status
- raw row count
- quarantined row count
- clean row count
- clean view path
- quarantine path
- EURUSD research readiness status
- whether pattern research can proceed using clean view
- validation results
- fast validation runtime
- push status
- manual GitHub merge instruction
- confirmation that raw CSV files were not modified
- confirmation that no automated merge was performed
