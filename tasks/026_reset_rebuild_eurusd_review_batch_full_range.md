# 026 — Explicitly Reset and Rebuild EURUSD Review Batch From Full-Range Sampling

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

User decision:
- User explicitly wants to restart the EURUSD review.
- It is now allowed to delete old completed review artifacts and rebuild the active review batch.
- This is a deliberate reset requested by the user, not automatic GUI startup behavior.

Recent source-range audit result:
- Raw 2020–2024 source exists and covers full range:
  - `/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv`
  - coverage: 2020–2024
- Clean view covers 2020–2025.
- Candidate pack covers 2020–2025.
- Current template/batch are truncated:
  - template only covers 2020-01 to 2020-04
  - batch_001 only covers 2020-01 to 2020-02
- This truncation explains repeated/concentrated samples.
- Candidate sampling logic was hardened in commit `e301fa0f` to spread picks over each candidate type timeline instead of earliest `head(...)` rows.

Important policy:
- GUI startup must remain non-destructive.
- Reset happens only through explicit reset/rebuild command or this explicit user-requested agent task.
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only; no SQLite.
- No model training.
- No trading signals/orders.
- No Qlib core changes.

## Objective

Explicitly reset the active EURUSD review state and rebuild `batch_001` from full-range, diversified sampling.

After this task:
1. Old completed review CSV/JSONL are removed or backed up.
2. Active `batch_001` is rebuilt with diversified, full-range samples.
3. New batch is no longer concentrated in early 2020.
4. GUI opens on the new fresh batch.
5. Completed review starts from 0.
6. Validation reports confirm full-range coverage and non-destructive GUI startup policy.

## Required Behavior

### 1. Backup old review artifacts before deletion

Even though the user wants to restart, make a safety backup by default before deletion.

Create backup directory:

```text
tmp/eurusd/review_reset_backups/YYYYMMDD_HHMMSS/
```

Backup if present:
```text
tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv
tmp/eurusd/EURUSD_15m_pattern_review_batch_001.jsonl
tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv
tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed_events.jsonl
tmp/validation-eurusd-pattern-review-batch-001.json
tmp/validation-eurusd-pattern-review-batch-001.md
tmp/validation-eurusd-completed-review-progress.json
tmp/validation-eurusd-completed-review-progress.md
tmp/validation-eurusd-review-summary-current.json
tmp/validation-eurusd-review-summary-current.md
```

Then delete old active review artifacts:
```text
tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv
tmp/eurusd/EURUSD_15m_pattern_review_batch_001.jsonl
tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv
tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed_events.jsonl
```

Do not delete raw data, clean view, candidates, or docs.

### 2. Rebuild review template if needed

Current template is truncated. Rebuild or regenerate the review template so it is not limited to 2020-01–2020-04.

Expected output:
```text
tmp/eurusd/EURUSD_15m_pattern_review_template.csv
tmp/eurusd/EURUSD_15m_pattern_review_template.jsonl
tmp/validation-eurusd-pattern-review-template.json
tmp/validation-eurusd-pattern-review-template.md
```

Ensure template sampling:
- uses full candidate timeline,
- balances candidate types,
- avoids earliest-head truncation,
- reports year coverage.

If existing template builder now uses updated candidate sampling from `e301fa0f`, run it.
If there is no easy one-command template rebuild, add/update one.

### 3. Rebuild active batch_001 from full-range template

Generate:
```text
tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv
tmp/eurusd/EURUSD_15m_pattern_review_batch_001.jsonl
tmp/validation-eurusd-pattern-review-batch-001.json
tmp/validation-eurusd-pattern-review-batch-001.md
```

Use diversification defaults:
```text
batch_size=100
min_gap_bars=8
max_samples_per_day=8
same_region_cooldown_bars=48
window_overlap_max_ratio=0.35
dedupe_overlapping_windows=true
balanced_by_candidate_type=true
prefer_time_diversity=true
```

If some flags do not exist yet, implement or map to existing logic.
Graceful fallback is acceptable, but report fallback counts.

### 4. Validate new sampling coverage

Run source-range audit:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_sampling_source_range_report
```

Expected improvement:
- template should cover multiple years, ideally 2020–2025 or at least 2020–2024.
- batch should cover multiple years/dates, not only Jan–Feb 2020.

The report should no longer show active template/batch as severely truncated. Acceptable statuses:
- `full_range_ready`
- `watch` if distribution is imperfect but covers multiple years

Not acceptable:
- `derived_artifacts_truncated` due to template/batch still only covering early 2020.

### 5. Validate duplicate/overlap status

If task 024 duplicate report exists, run it.
If not yet implemented, at minimum compute and print:
- first 20 sample timestamps
- first 20 unique days
- batch min/max timestamp
- batch year coverage
- duplicate/near-duplicate summary if available

Expected:
- first 20 samples span multiple dates/regions
- batch spans broad time range
- not concentrated in one week/month

### 6. Validate completed progress is fresh

After reset/rebuild, completed artifacts should be absent or empty.

Run completed progress report:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_completed_review_progress_report
```

Expected:
```text
completed_count=0
pending_count=100
status=awaiting_review_input or valid_in_progress with completed=0
next_action=continue_human_review or begin_human_review
```

If the report expects completed CSV to exist, update it to treat missing completed CSV as fresh/awaiting input, not an error.

### 7. Ensure GUI reads new batch_001

Confirm default GUI still reads:
```text
tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv
```

Run static check:
```bash
rg -n "EURUSD_15m_pattern_review_batch_001" scripts/run_eurusd_review_gui.sh cajas/apps/eurusd_pattern_review_app.py
```

Do not make GUI startup reset data.

### 8. Add/update explicit reset script

Update:
```text
scripts/reset_eurusd_review_batch.sh
```

so this exact rebuild can be repeated by user with one command:

```bash
./scripts/reset_eurusd_review_batch.sh --backup-old
```

Default behavior can remain explicit reset. Ensure:
- it backs up old review files by default or supports `--backup-old`
- it rebuilds template/batch from full-range sampling
- it uses current diversification defaults
- it writes reset report:
  - `tmp/validation-eurusd-review-batch-reset.json`
  - `tmp/validation-eurusd-review-batch-reset.md`
- it does not run on GUI startup

### 9. Documentation

Update:
- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `tasks/eurusd_15m_research_end_to_end_roadmap.md`
- `cajas/README.md` if applicable

Document:
- user chose explicit restart due truncated early-2020 batch
- reset is explicit and destructive to active completed review files
- backup directory is created
- new batch should use full-range sampling
- normal GUI startup remains non-destructive

### 10. Tests

Add/update tests for:
1. reset script dry-run / backup behavior
2. missing completed CSV treated as fresh review start
3. template/batch source-range audit detects full-range batch after rebuild
4. reset script does not modify raw/clean/candidate files
5. GUI launcher does not call reset
6. batch builder does not use earliest-head truncation
7. first N sample coverage spans multiple days/years when candidate pool supports it

## Suggested Commands

Run explicit reset/rebuild:

```bash
./scripts/reset_eurusd_review_batch.sh --backup-old
```

If script is not yet full-range aware, update it first, then run.

Run source range audit:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_sampling_source_range_report
```

Run completed progress report:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_completed_review_progress_report
```

Print new batch first 30:

```bash
./.venv-qlib313/bin/python - <<'PY'
import pandas as pd
p = "tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv"
df = pd.read_csv(p)
cols = [c for c in ["sample_id", "timestamp", "candidate_type"] if c in df.columns]
print("rows:", len(df))
print("min:", pd.to_datetime(df["timestamp"], utc=True).min())
print("max:", pd.to_datetime(df["timestamp"], utc=True).max())
print("years:", sorted(pd.to_datetime(df["timestamp"], utc=True).dt.year.dropna().unique().tolist()))
print(df[cols].head(30).to_string(index=False))
PY
```

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_validation_eurusd_sampling_source_range.py \
  cajas/tests/test_validation_eurusd_pattern_review_batch.py \
  cajas/tests/test_validation_eurusd_completed_review_progress.py \
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

Manual GUI smoke:

```bash
./scripts/run_eurusd_review_gui.sh
```

Manual checks:
1. GUI starts with new batch_001.
2. Completed progress shows 0 reviewed.
3. First several samples are not clustered in one local window.
4. Sample Number / Go to Sample works.
5. Save / Save and Next works.
6. Review dropdown schema v2 options still appear.
7. No old completed values load.

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas scripts tasks
git commit -m "feat: reset EURUSD review batch from full range"
```

If only generated `tmp/` artifacts changed and source already supports everything, commit docs/tasks/scripts as appropriate.

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Backup directory created
- Old review artifacts removed
- New template coverage
- New batch coverage
- New batch first20/first30 diversity
- Source range audit status
- Completed progress after reset
- GUI default batch confirmation
- Reset script behavior
- Validation command results
- Manual GUI smoke result if run
- `git status --short`
- Push status: not pushed
- Manual push command:

```bash
git push origin main
```

## Hard Boundaries Reminder

Do not:
- reset automatically on GUI startup
- delete raw source data
- delete clean view or candidates
- add SQLite
- create branches
- push automatically
- train models
- produce trading signals/orders
- modify Qlib core
