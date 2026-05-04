# 010 — Automate EURUSD Review Batch Rebuild and Reset Old Review State

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current situation:
- EURUSD GUI works.
- CSV/JSONL persistence works.
- Review batch diversification logic was implemented in commit `207ee206`.
- Diversification settings:
  - `balanced_by_candidate_type=true`
  - `min_gap_bars_between_samples=8`
  - `max_samples_per_day=8`
  - `prefer_time_diversity=true`
- However, the GUI may still read the old `batch_001`, so the user still sees clustered samples.
- Existing review content does not need to be preserved.
- The user explicitly wants to start fresh and remove old review baggage.
- The user does not want to manually run long build commands or manually copy files.
- This should be automated or handled by AI agent.

User preference:
- Work directly on `main`.
- CSV/JSONL only.
- No SQLite.
- Do not create branches.
- Do not push automatically.
- Use simple sequential prompts under `tasks/prompts/`.

## Objective

Create an automated, one-command workflow to reset the EURUSD 15m review state and rebuild a diversified `batch_001` that the GUI reads by default.

The user should not need to manually:
- provide all CLI arguments,
- copy `batch_002` over `batch_001`,
- delete old completed review files by hand,
- edit GUI paths by hand.

## Required Behavior

Add an automation script that does the following safely and deterministically:

1. Optionally backs up old review files if requested.
2. Deletes old review state by default because the user wants a fresh start.
3. Rebuilds diversified review batch as the default GUI batch:
   - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv`
   - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001.jsonl`
4. Deletes old completed review output:
   - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv`
   - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed_events.jsonl`
5. Writes a reset/rebuild report:
   - `tmp/validation-eurusd-review-batch-reset.json`
   - `tmp/validation-eurusd-review-batch-reset.md`
6. Confirms the regenerated first samples are diversified.
7. Ensures the GUI default path points to the regenerated `batch_001`.

## Preferred User Command

Create a simple script:

```bash
./scripts/reset_eurusd_review_batch.sh
```

Default behavior:
- fresh reset
- no old completed review retained
- generate diversified batch_001
- min gap bars = 8
- max samples per day = 8
- batch size = 100

Optional flags:

```text
--backup-old
--batch-size <N>
--min-gap-bars <N>
--max-samples-per-day <N>
--dry-run
```

Example:

```bash
./scripts/reset_eurusd_review_batch.sh
```

After this, the user can immediately run:

```bash
./scripts/run_eurusd_review_gui.sh
```

and the GUI should read the newly diversified batch.

## Required Implementation Details

### 1. Add shell script

Create:

```text
scripts/reset_eurusd_review_batch.sh
```

Use robust shell style:

```bash
#!/usr/bin/env bash
set -euo pipefail
```

The script should:
- run from repo root, or detect repo root,
- use `./.venv-qlib313/bin/python` if present,
- fallback to `python`,
- call Python module form where possible:

```bash
PYTHONPATH=. "$PYTHON_BIN" -m cajas.scripts.build_eurusd_pattern_review_batch ...
```

Required default paths:

```text
template_csv=tmp/eurusd/EURUSD_15m_pattern_review_template.csv
label_schema=tmp/validation-eurusd-pattern-label-schema.json
output_batch_csv=tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv
output_batch_jsonl=tmp/eurusd/EURUSD_15m_pattern_review_batch_001.jsonl
output_json=tmp/validation-eurusd-pattern-review-batch-001.json
output_md=tmp/validation-eurusd-pattern-review-batch-001.md
completed_csv=tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv
completed_events_jsonl=tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed_events.jsonl
reset_json=tmp/validation-eurusd-review-batch-reset.json
reset_md=tmp/validation-eurusd-review-batch-reset.md
```

### 2. Fresh reset behavior

By default:
- remove old default batch outputs
- remove old completed outputs
- do not preserve old review content

If `--backup-old` is passed:
- create timestamped backup dir, for example:

```text
tmp/eurusd/review_reset_backups/YYYYMMDD_HHMMSS/
```

- copy existing batch/completed files there before removal.

If no `--backup-old`:
- delete old files directly.

### 3. Dry-run support

If `--dry-run`:
- print what would be deleted/generated
- do not delete or write files
- do not run batch generation
- exit 0

### 4. Reset report

Implement either in the shell script or a small Python helper.

Report JSON should include:
- `status`
- `reset_mode`
- `backup_enabled`
- `backup_dir`
- `removed_files`
- `generated_files`
- `diversification_settings`
- `batch_csv`
- `batch_jsonl`
- `completed_csv_removed`
- `completed_events_jsonl_removed`
- `first10_unique_days`
- `first10_min_gap_minutes`
- `first10_samples`
- `next_action`

Suggested statuses:
- `reset_complete`
- `dry_run`
- `blocked_missing_template`
- `blocked_missing_label_schema`
- `generation_failed`

Markdown report should summarize the same.

### 5. Add or update Python helper if needed

If shell-only report generation is awkward, add:

```text
cajas/scripts/reset_eurusd_review_batch.py
```

or:

```text
cajas/reports/validation_eurusd_review_batch_reset.py
```

But keep the user-facing command as:

```bash
./scripts/reset_eurusd_review_batch.sh
```

### 6. Verify GUI default batch path

Check:

```bash
grep -R "EURUSD_15m_pattern_review_batch_001.csv" -n cajas/apps scripts
```

Ensure the default GUI launcher still points to:

```text
tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv
```

Do not force user to pass a batch path manually.

### 7. Documentation

Update:
- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `tasks/eurusd_15m_research_end_to_end_roadmap.md`
- `cajas/README.md` if it lists GUI commands
- add this prompt under `tasks/prompts/010_automate_eurusd_review_batch_reset.md`

Document the standard workflow:

```bash
./scripts/reset_eurusd_review_batch.sh
./scripts/run_eurusd_review_gui.sh
```

State clearly:
- reset deletes old completed review CSV/JSONL by default
- use `--backup-old` if old review files should be retained
- default diversified spacing is 8 bars / 2 hours

## Tests Required

Add tests where appropriate.

Suggested tests:

### Shell/script smoke tests
If existing test style supports shell scripts:
1. `--dry-run` prints planned operations and exits 0.
2. missing template/schema produces blocked status or clear error.
3. default args include `--min-gap-bars 8` and `--max-samples-per-day 8`.

### Python helper tests
If adding Python report helper, test:
1. reset report marks old completed files as removed.
2. first10 diversity summary is computed.
3. reset report includes generated paths.
4. dry-run does not remove files.
5. backup mode creates backup path metadata.

### Regression tests
Preserve existing:
- batch diversification tests
- GUI persistence tests
- chart gap compression tests

## Validation Commands

Run script dry-run:

```bash
./scripts/reset_eurusd_review_batch.sh --dry-run
```

Run real reset:

```bash
./scripts/reset_eurusd_review_batch.sh
```

Inspect first samples:

```bash
./.venv-qlib313/bin/python - <<'PY'
import pandas as pd
p = "tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv"
df = pd.read_csv(p)
print(df[["sample_id", "timestamp", "candidate_type"]].head(20).to_string(index=False))
print("first10 unique days:", pd.to_datetime(df["timestamp"].head(10)).dt.date.nunique())
PY
```

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_eurusd_pattern_review_batch.py cajas/tests/test_eurusd_pattern_review_gui.py cajas/tests/test_validation_eurusd_pattern_review_gui.py
```

Run py_compile:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/reports/validation_eurusd_pattern_review_batch.py cajas/scripts/build_eurusd_pattern_review_batch.py
```

Compile any new Python files.

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

Manual check:
1. GUI starts from sample 1 using regenerated `batch_001`.
2. First several `Next Sample` clicks are not all in the same local market area.
3. Save works.
4. Save and Next works.
5. Previous Sample works.
6. Completed CSV starts fresh.
7. JSONL events start fresh.

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add scripts/reset_eurusd_review_batch.sh cajas docs tasks
git commit -m "feat: automate EURUSD review batch reset"
```

Only add files that changed.

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Reset command added
- Old review data deletion behavior
- Backup option behavior
- Regenerated batch path
- Diversification settings
- First 10 sample diversity result
- GUI default batch confirmation
- Validation command results
- Manual GUI smoke result if run
- `git status --short`
- Push status: not pushed
- Manual push command:

```bash
git push origin main
```

## Hard Boundaries

Do not:
- add SQLite
- create branches
- push automatically
- merge automatically
- train models
- produce trading signals/orders
- modify Qlib core
- preserve old review data by default
- require the user to manually copy batch files
- require the user to manually pass long CLI args for normal use
