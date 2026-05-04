# 025 — Ensure EURUSD Review Sampling Uses Full 2020–2024 Data Range

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

User confirmed available raw EURUSD data files:

```text
/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv
/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv
```

Current active review target:
- EURUSD 15m pattern review.
- Current intended historical scope should use 2020–2024 data.
- User noticed many reviewed samples appear repeated / concentrated.
- User explicitly says the system should read the large 2020–2024 dataset and not be limited to a small time segment.

Important:
- Do not automatically reset current review data.
- Do not delete completed CSV/JSONL.
- Do not regenerate active batch unless explicitly requested.
- First diagnose whether source/template/candidate/batch generation is using the full 2020–2024 range.
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only; no SQLite.
- No model training, no trading signals/orders, no Qlib core changes.

## Objective

Audit and harden the EURUSD review sampling data lineage so future candidate/template/batch generation uses the full intended 2020–2024 data range, not a small pre-sliced segment.

The pipeline should be clear:

```text
raw 2020–2024 CSV
→ clean view
→ pattern candidates
→ review template
→ diversified / de-duplicated review batch
→ GUI batch_001
```

## Required Work

### 1. Audit current data lineage

Inspect all relevant scripts/reports/docs that build:

```text
tmp/eurusd/EURUSD_15m_Bid_clean_view.csv
tmp/eurusd/EURUSD_15m_pattern_candidates.csv
tmp/eurusd/EURUSD_15m_pattern_review_template.csv
tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv
```

Search:

```bash
grep -R "EURUSD_15 Mins_Bid" -n .
grep -R "EURUSD_15m_Bid_clean_view" -n cajas scripts tasks
grep -R "pattern_candidates" -n cajas scripts tasks
grep -R "pattern_review_template" -n cajas scripts tasks
grep -R "pattern_review_batch" -n cajas scripts tasks
```

Confirm:
- raw input path currently used
- clean view source
- min/max timestamp in clean view
- min/max timestamp in candidates
- min/max timestamp in review template
- min/max timestamp in review batch
- whether any `head`, `sample`, test fixture, early stop, or date filter limits data to 2020-01 only

### 2. Add source range audit report

Create or reuse a report:

```text
cajas/reports/validation_eurusd_sampling_source_range.py
cajas/scripts/build_eurusd_sampling_source_range_report.py
cajas/tests/test_validation_eurusd_sampling_source_range.py
```

Default raw source:

```text
/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv
```

Default derived files:

```text
tmp/eurusd/EURUSD_15m_Bid_clean_view.csv
tmp/eurusd/EURUSD_15m_pattern_candidates.csv
tmp/eurusd/EURUSD_15m_pattern_review_template.csv
tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv
```

Output artifacts:

```text
tmp/validation-eurusd-sampling-source-range.json
tmp/validation-eurusd-sampling-source-range.md
```

Report fields:
- `status`
- `raw_source_path`
- `raw_exists`
- `raw_row_count`
- `raw_min_timestamp`
- `raw_max_timestamp`
- `clean_view_path`
- `clean_view_row_count`
- `clean_view_min_timestamp`
- `clean_view_max_timestamp`
- `candidate_path`
- `candidate_count`
- `candidate_min_timestamp`
- `candidate_max_timestamp`
- `template_path`
- `template_count`
- `template_min_timestamp`
- `template_max_timestamp`
- `batch_path`
- `batch_count`
- `batch_min_timestamp`
- `batch_max_timestamp`
- `year_coverage`
- `candidate_year_coverage`
- `template_year_coverage`
- `batch_year_coverage`
- `coverage_warnings`
- `likely_truncation_detected`
- `next_action`

Suggested statuses:
- `full_range_ready`: source and derived artifacts cover expected 2020–2024 span.
- `derived_artifacts_truncated`: raw covers full range but candidates/template/batch do not.
- `raw_source_missing`: raw source not found.
- `blocked`: files unreadable or timestamps missing.
- `watch`: some coverage imbalance but not clearly broken.

### 3. Define expected coverage

For this phase, expected historical source coverage is:

```text
start_year=2020
end_year=2024
```

The clean view should roughly cover 2020–2024.

Candidates/template/batch do not need equal rows per year, but they should not all cluster in one small early segment unless intentionally configured.

Flag warning if:
- candidate/template/batch max timestamp is far before 2024
- first/last span is less than e.g. 180 days when source spans years
- batch samples all fall in a narrow date range
- candidate pool only covers 2020-01 while raw covers 2020–2024

### 4. Hard-code no small test window in production scripts

Find and remove or guard production code patterns like:
- `head(5000)`
- `df.iloc[:...]`
- fixed January 2020 filters
- `sample_count` defaults that only read early rows
- test fixture paths used in normal scripts

If such limits are needed for tests, make them explicit test-only options, not default production behavior.

### 5. Update batch duplicate report to include source range context

If task 024 duplicate detection has been or will be implemented, ensure it includes:
- raw/clean/candidate/template/batch timestamp span
- year coverage
- whether duplicates may be caused by truncated source/candidate pool

Do not duplicate logic if source range report already exists; link/summarize it.

### 6. Add one-command audit

If useful, update the read-only validation script:

```text
scripts/validate_eurusd_review_progress.sh
```

to also run source range audit, or create:

```text
scripts/validate_eurusd_sampling_source_range.sh
```

The script should be read-only.

### 7. Documentation

Update:
- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `tasks/eurusd_15m_research_end_to_end_roadmap.md`
- `cajas/README.md` if appropriate

Document:
- expected raw data path
- expected 2020–2024 source coverage
- how to run source range audit
- normal GUI does not reset/regenerate data
- explicit reset/rebuild remains user-triggered only

## Tests Required

Add tests for:

1. Full source coverage:
   - synthetic raw/derived files covering 2020–2024 return `full_range_ready`.

2. Derived truncation:
   - raw covers 2020–2024 but candidate/template/batch only cover 2020-01.
   - status should be `derived_artifacts_truncated`.

3. Missing raw:
   - status `raw_source_missing` or blocked/warning as designed.

4. Timestamp parsing:
   - supports the timestamp format used by raw Dukascopy-style file if applicable.

5. Year coverage:
   - computes year counts/distribution.

6. Read-only behavior:
   - report generation does not modify batch/completed files.

7. Integration with duplicate/batch report if modified.

## Validation Commands

Run source range report:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_sampling_source_range_report
```

Run tests:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_eurusd_sampling_source_range.py
```

Run relevant existing tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_validation_eurusd_pattern_review_batch.py \
  cajas/tests/test_validation_eurusd_completed_review_progress.py \
  cajas/tests/test_validation_eurusd_review_summary_current.py \
  cajas/tests/test_eurusd_pattern_review_gui.py \
  cajas/tests/test_validation_eurusd_pattern_review_gui.py
```

Run py_compile for changed Python:

```bash
./.venv-qlib313/bin/python -m py_compile <changed-python-files>
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

## Manual/Terminal Data Check

Print source spans:

```bash
./.venv-qlib313/bin/python - <<'PY'
import pandas as pd
from pathlib import Path

paths = [
    "/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv",
    "tmp/eurusd/EURUSD_15m_Bid_clean_view.csv",
    "tmp/eurusd/EURUSD_15m_pattern_candidates.csv",
    "tmp/eurusd/EURUSD_15m_pattern_review_template.csv",
    "tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv",
]
for p in paths:
    path = Path(p)
    print("\\n", p, "exists=", path.exists())
    if not path.exists():
        continue
    df = pd.read_csv(path)
    ts_col = "timestamp" if "timestamp" in df.columns else df.columns[0]
    ts = pd.to_datetime(df[ts_col], errors="coerce", utc=True)
    print("rows", len(df), "ts_col", ts_col, "min", ts.min(), "max", ts.max(), "years", sorted(ts.dt.year.dropna().unique().tolist())[:10], "...", sorted(ts.dt.year.dropna().unique().tolist())[-10:])
PY
```

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas scripts tasks
git commit -m "feat: audit EURUSD sampling source range"
```

Since user allows committing all `tasks/**/*.md`, include task prompt markdowns as appropriate.

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Raw source path
- Raw source coverage
- Clean view coverage
- Candidate coverage
- Template coverage
- Batch coverage
- Whether truncation was detected
- Duplicate/repetition implication
- Report artifact paths
- Validation command results
- `git status --short`
- Push status: not pushed
- Manual push command:

```bash
git push origin main
```

## Hard Boundaries Reminder

Do not:
- reset review data
- regenerate active batch automatically
- delete completed CSV/JSONL
- add SQLite
- create branches
- push automatically
- train models
- produce trading signals/orders
- modify Qlib core
