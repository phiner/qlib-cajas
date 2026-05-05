# 034 — Rebuild EURUSD Artifacts to Close Candidate Audit Gates

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Recent task 033:
- Added deterministic candidate-audit gates.
- Added warning inventory and hardening roadmap report generators.
- Hardened `validation_eurusd_candidate_audit.py`.
- Tests/docs were updated.
- However final audit status is currently `blocked`.

Reason for blocked status:
- Current on-disk candidate artifact is stale:
  - `tmp/eurusd/EURUSD_15m_pattern_candidates.csv`
- It is missing newly required causality/explainability fields.
- The code now requires these fields, but artifacts were not regenerated after the schema/gate hardening.
- Therefore the next step is to rebuild derived candidate/template/batch artifacts from current code and re-run audit gates.

User rule:
- Do not ask for confirmation before generating/using the next prompt.
- Proceed with the next prompt/action plan directly.

Hard boundaries:
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only; no SQLite.
- No model training.
- No trading signals/orders.
- No Qlib core changes.
- GUI startup must remain non-destructive.
- Reset/rebuild is allowed in this task because the user already requested fixing audit gates before proceeding and current artifacts are stale.

## Objective

Regenerate the EURUSD derived artifacts with the current candidate generator and audit schema so deterministic candidate audit gates are no longer blocked by stale files.

Target final state:
- active batch rebuilt from current segment-aware, causality/explainability-aware candidates
- candidate audit status is `pass` or acceptable `watch`
- `causality_columns_missing` is gone
- selected-row explainability gaps are gone or explicitly classified as non-blocking
- completed progress returns to clean fresh-start state
- all validations pass
- changes are committed on `main`
- no push is performed

## Required Work

### 1. Inspect current git state

Run:

```bash
git status --short
git log --oneline -8
```

If task 033 changes are uncommitted:
- include them in the final commit or create a commit before reset if needed.
- Do not lose any work.

### 2. Back up and explicitly reset/rebuild active artifacts

Run:

```bash
./scripts/reset_eurusd_review_batch.sh --backup-old
```

This must:
- back up current active review artifacts
- remove old active batch/completed artifacts
- regenerate candidate pack with current code
- regenerate review samples/template
- regenerate active `batch_001`
- leave GUI startup non-destructive

Expected generated files include:

```text
tmp/eurusd/EURUSD_15m_pattern_candidates.csv
tmp/eurusd/EURUSD_15m_pattern_review_template.csv
tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv
tmp/validation-eurusd-pattern-candidate-pack.json
tmp/validation-eurusd-pattern-candidate-pack.md
tmp/validation-eurusd-pattern-review-template.json
tmp/validation-eurusd-pattern-review-template.md
tmp/validation-eurusd-pattern-review-batch-001.json
tmp/validation-eurusd-pattern-review-batch-001.md
```

### 3. Verify candidate artifact has required new columns

Run a quick check:

```bash
./.venv-qlib313/bin/python - <<'PY'
import pandas as pd

p = "tmp/eurusd/EURUSD_15m_pattern_candidates.csv"
df = pd.read_csv(p, nrows=5)
required = [
    "causal_candidate",
    "candidate_logic_uses_future_bars",
    "candidate_logic_future_bars_used",
    "review_filter_uses_future_bars",
    "review_filter_future_bars_used",
    "label_uses_future_bars",
    "future_usage_role",
    "not_for_live_signal",
    "candidate_reason_codes",
    "primary_selection_reason",
]
missing = [c for c in required if c not in df.columns]
print("missing_required_columns:", missing)
print("columns_count:", len(df.columns))
if missing:
    raise SystemExit(1)
PY
```

Also inspect trend metadata exists:

```bash
./.venv-qlib313/bin/python - <<'PY'
import pandas as pd

p = "tmp/eurusd/EURUSD_15m_pattern_candidates.csv"
df = pd.read_csv(p, nrows=1000)
trend_cols = [
    "segment_id",
    "segment_position_fraction",
    "representative_anchor",
    "late_segment_anchor",
    "rebound_after_anchor",
    "excluded_late_reversal_anchor",
    "preferred_review_candidate",
]
missing = [c for c in trend_cols if c not in df.columns]
print("missing_trend_columns:", missing)
if missing:
    raise SystemExit(1)
PY
```

### 4. Re-run candidate audit and hardening reports

Run:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_candidate_audit_report
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_candidate_audit_warning_inventory
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_candidate_hardening_roadmap
```

Inspect outputs:

```text
tmp/validation-eurusd-candidate-audit.json
tmp/validation-eurusd-candidate-audit.md
tmp/validation-eurusd-candidate-audit-warning-inventory.json
tmp/validation-eurusd-candidate-audit-warning-inventory.md
tmp/validation-eurusd-candidate-hardening-roadmap.json
tmp/validation-eurusd-candidate-hardening-roadmap.md
```

### 5. Required audit outcomes

The final audit must not be `blocked`.

Acceptable:
```text
status=pass
```

or:
```text
status=watch
```

Not acceptable:
```text
status=blocked
```

If final status remains `needs_rule_refinement`:
- inspect warning inventory
- fix must-fix items if practical
- if some should-fix remain, justify them as watch only if they are non-blocking and documented.

Must be resolved:
- `causality_columns_missing`
- missing selected-row `primary_selection_reason`
- selected trend rows without segment metadata
- selected trend rows with `excluded_late_reversal_anchor=true`
- selected trend rows with `preferred_review_candidate=false` without fallback reason
- exact duplicate sample IDs in active batch
- same timestamp duplicate rows in active batch unless explicit fallback is documented

### 6. Validate source range and fresh progress

Run:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_sampling_source_range_report
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_completed_review_progress_report
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_rejected_samples_report
```

Expected:
- source range: `full_range_ready` or non-truncated acceptable status
- completed progress:
  - `status=awaiting_review_input`
  - `blocking=false`
  - `completed_count=0`
  - `pending_count=100`
  - `csv_schema_status=not_applicable`
  - `jsonl_audit_status=not_applicable`
- rejected samples:
  - fresh empty state if rejected registry was reset/backed up
  - no blocking status

### 7. Validate new batch quality

Run:

```bash
./.venv-qlib313/bin/python - <<'PY'
import pandas as pd

p = "tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv"
df = pd.read_csv(p)
ts = pd.to_datetime(df["timestamp"], utc=True)
print("rows:", len(df))
print("min:", ts.min())
print("max:", ts.max())
print("years:", sorted(ts.dt.year.dropna().unique().tolist()))
print("first20_unique_days:", ts.head(20).dt.date.nunique())
print("first20_years:", sorted(ts.head(20).dt.year.dropna().unique().tolist()))

cols = [
    "sample_id",
    "timestamp",
    "candidate_type",
    "primary_selection_reason",
    "preferred_review_candidate",
    "late_segment_anchor",
    "rebound_after_anchor",
    "excluded_late_reversal_anchor",
]
cols = [c for c in cols if c in df.columns]
print(df[cols].head(30).to_string(index=False))

trend = df[df["candidate_type"].astype(str).str.contains("trend", na=False)]
print("trend rows:", len(trend))
for col in [
    "preferred_review_candidate",
    "late_segment_anchor",
    "rebound_after_anchor",
    "excluded_late_reversal_anchor",
]:
    if col in trend.columns:
        print(col, trend[col].value_counts(dropna=False).to_dict())
PY
```

Expected:
- 100 rows
- multiple years covered
- first20 spans multiple dates/years
- no trend rows selected with `excluded_late_reversal_anchor=true`
- selected rows should have `primary_selection_reason`

### 8. Run validation tests

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_validation_eurusd_candidate_audit.py \
  cajas/tests/test_validation_eurusd_candidate_hardening_reports.py \
  cajas/tests/test_validation_eurusd_pattern_candidate_pack.py \
  cajas/tests/test_eurusd_trend_segment_candidates.py \
  cajas/tests/test_validation_eurusd_pattern_review_batch.py \
  cajas/tests/test_validation_eurusd_sampling_source_range.py \
  cajas/tests/test_validation_eurusd_completed_review_progress.py \
  cajas/tests/test_validation_eurusd_rejected_samples.py
```

Run GUI/review tests:

```bash
./.venv-qlib313/bin/python -m pytest \
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

### 9. Documentation / report update if needed

If final audit status is `watch`, update docs/roadmap to state:
- which warnings remain
- why they are non-blocking
- next improvement phase

If status is `pass`, document that review can resume from the rebuilt batch.

Update as needed:
```text
cajas/docs/eurusd_pattern_research_kickoff.md
tasks/eurusd_15m_research_end_to_end_roadmap.md
cajas/README.md
```

### 10. Commit

If source/scripts/docs/tests changed or task 033/034 changes are uncommitted, commit them.

Suggested commit:

```bash
git add cajas scripts tasks
git commit -m "chore: rebuild EURUSD artifacts for candidate audit gates"
```

If substantial source fixes were required:

```bash
git commit -m "fix: close EURUSD candidate audit gates"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash(es)
- Backup directory created
- Candidate/template/batch regenerated
- Required candidate columns check
- Final candidate audit status
- Warning inventory summary
- Hardening roadmap status
- Source range status
- Completed progress fresh-start status
- Rejected report status
- New batch coverage
- Trend candidate quality in new batch
- Validation command results
- Whether GUI startup remains non-destructive
- `git status --short`
- Push status: not pushed
- Manual push command:

```bash
git push origin main
```

## Hard Boundaries Reminder

Do not:
- push automatically
- create branches
- add SQLite
- train models
- produce trading signals/orders
- modify Qlib core
- use future-aware review filters as live candidate logic
- reset automatically on GUI startup
