# 023 — Fix EURUSD GUI Startup UnboundLocalError for sample Sidebar Caption

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Recent commit:
- `1efcdb66`
- Added explicit `Go to Sample` global sample jump behavior.

User now reports GUI startup failure:

```text
UnboundLocalError: cannot access local variable 'sample' where it is not associated with a value

Traceback:
File ".../cajas/apps/eurusd_pattern_review_app.py", line 570, in <module>
    main()
File ".../cajas/apps/eurusd_pattern_review_app.py", line 249, in main
    st.sidebar.caption(f"sample_id={sample['sample_id']} | global_index={sample_idx}")
                                    ^^^^^^
```

Interpretation:
- Sidebar caption references `sample` before `sample` is assigned.
- This is a variable ordering/scope regression introduced around global sample jump debug/sidebar display.
- App fails on startup before user can review.

Hard boundaries:
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only.
- No SQLite.
- Do not reset/regenerate review batch.
- Do not delete completed review data.
- Do not train models or create trading signals/orders.

## Objective

Fix the GUI startup error by ensuring `sample` is defined before it is referenced in sidebar/debug text.

## Required Fix

### 1. Inspect app variable ordering

Open:

```text
cajas/apps/eurusd_pattern_review_app.py
```

Around line ~249, inspect:
- when `sample_idx` / `current_global_sample_idx` is computed
- when full batch/current sample dataframe is available
- where `sample = ...` is assigned
- where `st.sidebar.caption(f"sample_id={sample...`) is rendered

### 2. Define sample before sidebar caption

Ensure the currently selected sample row is resolved before any UI element references it.

Preferred pattern:

```python
sample_idx = clamp_global_sample_index(...)
sample = full_batch.iloc[sample_idx].to_dict()
st.sidebar.caption(f"sample_id={sample['sample_id']} | global_index={sample_idx}")
```

If sample resolution depends on loaded batch:
- only render caption after batch is loaded and non-empty.
- if batch is empty, show a clear warning and stop gracefully.

### 3. Avoid duplicate/late sample assignment

If `sample` is currently assigned later in the app:
- move assignment earlier,
- or rename early assignment to avoid confusion,
- but ensure chart/review code uses the same selected sample.

Do not compute sidebar caption from a stale filtered sample.

### 4. Preserve global semantics

`sample` must come from the full batch by global index, not filtered subset.

### 5. Add regression test

Add/update tests in `cajas/tests/test_eurusd_pattern_review_gui.py`.

Suggested tests:

1. Static source ordering / import sanity:
   - app source should not reference `sample['sample_id']` before sample assignment if practical.
   - or add a source-level test ensuring sidebar caption is after a `sample =` assignment.

2. Better pure helper test:
   - if a helper exists to resolve selected sample, test it returns sample dict before rendering metadata.

3. App import/compile:
   - py_compile already catches syntax, but not this runtime scope issue.
   - add a small test around new helper rather than trying to run Streamlit.

4. Existing tests still pass:
   - global jump
   - one-shot toast
   - Save / Save and Next
   - Previous / Next
   - CSV/JSONL persistence
   - chart marker/framing/gap compression

### 6. Manual GUI smoke

After fix:

```bash
./scripts/run_eurusd_review_gui.sh
```

Confirm:
- app starts without `UnboundLocalError`
- sidebar shows sample_id/global_index
- Sample Number + Go to Sample works
- Save / Save and Next works
- Previous / Next works

## Validation Commands

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_eurusd_pattern_review_gui.py cajas/tests/test_validation_eurusd_pattern_review_gui.py
```

Run py_compile:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py cajas/tests/test_eurusd_pattern_review_gui.py
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

Manual startup smoke:

```bash
./scripts/run_eurusd_review_gui.sh
```

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas/apps/eurusd_pattern_review_app.py cajas/tests/test_eurusd_pattern_review_gui.py tasks/023_fix_eurusd_gui_sample_scope_startup.md
git commit -m "fix: resolve EURUSD GUI sample sidebar scope"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Exact root cause
- Fix applied
- GUI startup status
- Sample Number / Go to Sample status
- Save/navigation regression status
- Validation command results
- Manual GUI smoke result if run
- `git status --short`
- Push status: not pushed
- Manual push command:

```bash
git push origin main
```
