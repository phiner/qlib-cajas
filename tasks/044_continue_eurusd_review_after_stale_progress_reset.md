# Task 044 — Continue EURUSD 15m Review After Stale Progress Reset

## Context

You are working in the Qlib Base / qlib-cajas repository.

Active branch:

- `main`

Current completed review progress state after the reset:

- `status=awaiting_review_input`
- `blocking=false`
- `completed_count=0`
- `pending_count=100`
- `csv_schema_status=not_applicable`
- `jsonl_audit_status=not_applicable`

The prior stale completed review rows were intentionally archived, not kept in the active completed file.

Backup directory:

- `tmp/eurusd/review_reset_backups/20260505_104400_stale_completed_progress/`

Archived files:

- `tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv`
- `tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed_events.jsonl`
- `tmp/validation-eurusd-completed-review-progress.json`
- `tmp/validation-eurusd-completed-review-progress.md`

Candidate audit status after reset:

- `watch`, not blocked
- Tail-bias remains `pass`

Known current git status:

- No tracked code/docs changed
- One untracked task file may exist:
  - `tasks/043_resolve_eurusd_completed_progress_block.md`

## Goal

Continue from the clean active review state without reintroducing stale completed rows.

The next useful step is to confirm the active batch is clean, keep the archive intact, and prepare the GUI review workflow for the first real human-reviewed rows in the current active batch.

## Hard constraints

Do not invent human labels.

Do not copy archived stale completed rows back into the active completed CSV or JSONL.

Do not reset the active batch automatically.

Do not add SQLite or any new storage backend.

Keep durable review storage as CSV + JSONL only.

Do not modify Qlib core.

Do not add trading signals, orders, broker logic, model training, or live/paper trading behavior.

Work directly on `main` unless the user explicitly says otherwise.

Do not perform automated merge operations.

## Required checks

1. Inspect current state:

```bash
git status --short
ls -la tmp/eurusd/review_reset_backups/20260505_104400_stale_completed_progress/ || true
```

2. Confirm active completed files are absent or empty/clean as expected:

```bash
ls -la tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed_events.jsonl 2>/dev/null || true
```

3. Rebuild completed progress report:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_completed_review_progress_report
```

Expected result:

- `status=awaiting_review_input`
- `blocking=false`
- `completed_count=0`
- `pending_count=100`

4. Run the local GUI launcher only if a human reviewer is ready to review samples:

```bash
./scripts/run_eurusd_review_gui.sh
```

Important:

- The GUI launcher must not reset the batch.
- Save actions should persist only the current active batch sample IDs.
- JSONL should append audit events for real saves.

## Optional tracked cleanup

If `tasks/043_resolve_eurusd_completed_progress_block.md` is intentionally part of the project history, add and commit it.

Suggested commit message:

```bash
git add tasks/043_resolve_eurusd_completed_progress_block.md
git commit -m "document EURUSD completed progress reset"
```

If it is just a temporary prompt, leave it untracked or remove it only after user approval.

## Validation after any tracked change

If you commit the task doc or make any tracked changes, run:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_completed_review_progress_report
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_candidate_audit_report
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_eurusd_completed_review_progress.py cajas/tests/test_validation_eurusd_candidate_audit.py cajas/tests/test_validation_eurusd_candidate_selection_standards.py cajas/tests/test_validation_eurusd_pattern_review_batch.py cajas/tests/test_eurusd_pattern_review_gui.py cajas/tests/test_validation_eurusd_pattern_review_gui.py
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/fast_validation_latest.json
git diff --check
find cajas -path "*/init.py" -print
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

## Final response format

Report:

- Active branch
- Whether work was done on `main`
- Whether tracked files changed
- Commit hash, if any
- Current completed progress status
- Current completed_count / pending_count
- Whether archived stale rows remained archived
- Candidate audit status
- Validation results
- `git status --short`
- Push status

Do not claim human review progress unless real rows were reviewed and saved by a human.
