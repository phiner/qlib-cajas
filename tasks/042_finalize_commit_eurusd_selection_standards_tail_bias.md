# 042 — Finalize and Commit EURUSD Selection Standards / Tail-Bias Hardening

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Task 041 has been implemented and validated, but not committed yet.

Current Task 041 result summary:
- Candidate-selection standards report added.
- Trend anti-tail defaults tightened.
- Tail-bias metrics added.
- `why_selected_summary` added and propagated.
- Candidate/template/batch rebuilt via:
  ```bash
  ./scripts/reset_eurusd_review_batch.sh --backup-old
  ```
- Tail-bias audit result:
  - `trend_batch_count=40`
  - `trend_near_tail_count=0`
  - `trend_near_tail_ratio=0.0`
  - `trend_ideal_mid_ratio=0.65`
  - `tail_bias_status=pass`
- Final candidate audit status:
  - `watch`, not blocked
  - warning inventory status `watch`, `warning_count=4`
- Validation passed:
  - py_compile
  - requested pytest bundle: `109 passed`
  - candidate selection standards report
  - reset script
  - candidate audit report
  - warning inventory
  - fast validation
  - hygiene

Important current issue:
- Task 041 changes are uncommitted.
- `git status --short` shows modified/untracked files.
- Need to commit the completed work cleanly before moving on.

Hard boundaries:
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only; no SQLite.
- No model training.
- No trading signals/orders.
- No Qlib core changes.
- Do not reset/rebuild again unless validation shows stale artifacts or broken reports.
- GUI startup must remain non-destructive.

## Objective

Finalize Task 041 by:
1. Verifying current reports still reflect the successful state.
2. Committing all Task 041 code/tests/docs/prompt files.
3. Reporting clean final status and manual push command.

This is a closure task, not a new feature task.

## Required Work

### 1. Inspect git state

Run:

```bash
git status --short
git diff --stat
```

Expected uncommitted files include:
```text
cajas/research/eurusd_pattern_candidates.py
cajas/reports/validation_eurusd_pattern_review_batch.py
cajas/reports/validation_eurusd_candidate_audit.py
cajas/reports/validation_eurusd_candidate_selection_standards.py
cajas/scripts/build_eurusd_candidate_selection_standards_report.py
cajas/tests/test_validation_eurusd_candidate_selection_standards.py
cajas/tests/test_eurusd_trend_segment_candidates.py
cajas/tests/test_validation_eurusd_pattern_review_batch.py
cajas/tests/test_validation_eurusd_candidate_audit.py
cajas/docs/eurusd_pattern_research_kickoff.md
tasks/eurusd_15m_research_end_to_end_roadmap.md
cajas/README.md
tasks/041_audit_selection_standards_and_reduce_trend_tail_bias.md
```

Include all relevant task markdown under `tasks/`.

### 2. Re-run key reports without resetting

Do not run reset again unless needed.

Run:

```bash
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_candidate_selection_standards_report
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_candidate_audit_report
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_candidate_audit_warning_inventory
./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_completed_review_progress_report
```

Confirm:
- selection standards report builds.
- candidate audit is not `blocked`.
- candidate audit is `watch` or `pass`.
- tail-bias status remains `pass`.
- completed progress is fresh/non-blocking:
  ```text
  status=awaiting_review_input
  blocking=false
  completed_count=0
  pending_count=100
  ```

### 3. Inspect final audit values

Run a quick JSON check:

```bash
./.venv-qlib313/bin/python - <<'PY'
import json
from pathlib import Path

audit = json.loads(Path("tmp/validation-eurusd-candidate-audit.json").read_text())
print("candidate_audit_status:", audit.get("status"))
print("must_fix_failures:", audit.get("must_fix_failures"))
print("tail_bias_summary:", audit.get("tail_bias_summary") or audit.get("trend_tail_bias_summary"))

progress = json.loads(Path("tmp/validation-eurusd-completed-review-progress.json").read_text())
print("progress_status:", progress.get("status"))
print("progress_blocking:", progress.get("blocking"))
print("completed_count:", progress.get("completed_count"))
print("pending_count:", progress.get("pending_count"))
PY
```

If key names differ, inspect and report actual structure.

### 4. Run validation

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_validation_eurusd_candidate_selection_standards.py \
  cajas/tests/test_validation_eurusd_candidate_audit.py \
  cajas/tests/test_validation_eurusd_pattern_candidate_pack.py \
  cajas/tests/test_eurusd_trend_segment_candidates.py \
  cajas/tests/test_validation_eurusd_pattern_review_batch.py \
  cajas/tests/test_eurusd_pattern_review_gui.py \
  cajas/tests/test_validation_eurusd_pattern_review_gui.py
```

Run py_compile for changed Python:

```bash
./.venv-qlib313/bin/python -m py_compile \
  cajas/research/eurusd_pattern_candidates.py \
  cajas/reports/validation_eurusd_pattern_review_batch.py \
  cajas/reports/validation_eurusd_candidate_audit.py \
  cajas/reports/validation_eurusd_candidate_selection_standards.py \
  cajas/scripts/build_eurusd_candidate_selection_standards_report.py \
  cajas/tests/test_validation_eurusd_candidate_selection_standards.py \
  cajas/tests/test_eurusd_trend_segment_candidates.py \
  cajas/tests/test_validation_eurusd_pattern_review_batch.py \
  cajas/tests/test_validation_eurusd_candidate_audit.py
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

### 5. Commit

If validation passes, commit all Task 041 files.

Suggested commit:

```bash
git add \
  cajas/research/eurusd_pattern_candidates.py \
  cajas/reports/validation_eurusd_pattern_review_batch.py \
  cajas/reports/validation_eurusd_candidate_audit.py \
  cajas/reports/validation_eurusd_candidate_selection_standards.py \
  cajas/scripts/build_eurusd_candidate_selection_standards_report.py \
  cajas/tests/test_validation_eurusd_candidate_selection_standards.py \
  cajas/tests/test_eurusd_trend_segment_candidates.py \
  cajas/tests/test_validation_eurusd_pattern_review_batch.py \
  cajas/tests/test_validation_eurusd_candidate_audit.py \
  cajas/docs/eurusd_pattern_research_kickoff.md \
  tasks/eurusd_15m_research_end_to_end_roadmap.md \
  cajas/README.md \
  tasks/041_audit_selection_standards_and_reduce_trend_tail_bias.md

git commit -m "fix: reduce EURUSD trend tail candidate bias"
```

If additional task markdown files are present and relevant, include them.

### 6. Final git check

Run:

```bash
git status --short
git log --oneline -5
```

Expected:
- `git status --short` clean, unless only intentionally ignored/generated files remain.
- New commit exists on `main`.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files committed
- Selection standards report status
- Tail-bias audit status
- Candidate audit final status
- Remaining warning inventory summary
- Completed progress status
- Validation command results
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
