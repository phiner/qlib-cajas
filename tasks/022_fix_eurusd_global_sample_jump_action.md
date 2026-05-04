# 022 — Fix EURUSD Global Sample Number Jump Action

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current GUI state:
- Sidebar has `Sample Number`.
- It is defined as global full-batch 1-based sample number.
- It should ignore filters.
- Previous / Next / Save and Next should use global order.
- However, the user reports that typing/changing `Sample Number` still does not actually locate/jump to that sample/review.

Screenshot:
- Sidebar shows:
  - `Sample Number`
  - number input value `1`
  - help text: `Global position in full review batch; ignores filters.`
- But changing it does not navigate to the requested sample.

Likely issue:
- `number_input` value is not being converted into `pending_global_sample_idx`, or
- widget state is overwritten by canonical state on rerun, or
- callback/order is wrong, or
- app still renders current sample from old filtered/current index instead of global index.
- There may be no explicit `Go` action, so typed values are not reliably committed.

Hard boundaries:
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only.
- No SQLite.
- Do not reset/regenerate review batch.
- Do not delete completed review CSV/JSONL.
- Do not train models or create trading signals/orders.
- Do not modify Qlib core.

## Objective

Make global Sample Number jump actually work.

The user should be able to:
1. Type a sample number.
2. Click `Go` / `Jump` or press enter if supported.
3. GUI displays that global batch sample.
4. Chart and review fields reload for that sample.
5. No save occurs.
6. No old save toast appears.

## Required Behavior

### 1. Add explicit `Go to Sample` button

Do not rely only on `number_input` auto-rerun.

Sidebar should show:

```text
Sample Number [ input ]
Go to Sample
```

or compact row:

```text
Sample Number: [ 34 ] [Go]
```

Behavior:
- User types 34.
- User clicks `Go`.
- App converts 34 -> global index 33.
- App sets `pending_global_sample_idx = 33`.
- App reruns.
- App displays global batch row 33.

### 2. Keep Previous/Next as global navigation

- Previous Sample: global index - 1
- Next Sample: global index + 1
- Save and Next: save current global sample then global index + 1

### 3. Input should not be overwritten before Go

The input widget should allow typed value to remain until `Go`.

Avoid this bad pattern:
```python
st.session_state["sample_number_widget"] = current_global_idx + 1
```
after the widget has been created or on every rerun.

Use separate keys:
```python
current_global_sample_idx
sample_number_input
pending_global_sample_idx
```

Initialization:
- initialize `sample_number_input` only if absent.
- when current sample changes due to Prev/Next/Save and Next/Go, sync `sample_number_input` before widget creation on next rerun.

### 4. Apply pending navigation before rendering

At top of `main()`, before sample-dependent widgets:
```python
if "pending_global_sample_idx" in st.session_state:
    idx = clamp(...)
    st.session_state["current_global_sample_idx"] = idx
    st.session_state["sample_number_input"] = idx + 1
    clear/reload review field state for the new sample
```

Then render the selected sample from the full batch row at `current_global_sample_idx`.

### 5. Jump ignores filters

Even if filters are active:
- `Go to Sample` must find the full batch row.
- If selected sample does not match filters, still display it.
- Show info:
```text
Showing global sample 34; current filters may not match this sample.
```

Do not silently fail due to filters.

### 6. Optional enter-to-jump

If Streamlit supports `on_change` safely:
- optional callback may stage jump when input changes.
- But the explicit `Go to Sample` button must exist and work.

### 7. No save/no toast on jump

`Go to Sample`:
- does not call save/persistence helper.
- does not enqueue save toast.
- does not modify completed CSV/JSONL.

### 8. Add debug/status display

Sidebar should show:
```text
Sample 34 / 100
sample_id=...
global_index=33
```

This helps verify the jump worked.

## Required Investigation

Search:
```bash
grep -R "Sample Number" -n cajas/apps cajas/research
grep -R "sample_number" -n cajas/apps cajas/research cajas/tests
grep -R "current_global_sample_idx" -n cajas/apps cajas/research cajas/tests
grep -R "pending_global_sample_idx" -n cajas/apps cajas/research cajas/tests
```

Find:
- whether the app renders selected row from full batch or filtered dataframe.
- whether the widget value is overwritten every rerun.
- whether pending navigation is applied before chart/review widgets are rendered.

## Tests Required

Update `cajas/tests/test_eurusd_pattern_review_gui.py`.

Required tests:

### 1. Go-to-sample conversion
- input sample number 1 -> global index 0
- input sample number 34 -> global index 33
- out-of-range clamps safely

### 2. Pending navigation application
Create pure helper if needed:
```python
apply_pending_global_sample_index(state, batch_count)
```
Test:
- pending index updates current index
- sample_number_input syncs to current index + 1
- pending key is cleared

### 3. Jump ignores filters
With fake full batch and filtered subset:
- direct global index 3 resolves row 3 from full batch
- not row 3 from filtered subset
- if row 3 doesn't match filter, still selected

### 4. No persistence on jump
Test helper/static path:
- `Go to Sample` does not call save helper
- no pending toast is set

### 5. Static app regression
Assert app source includes:
- `Go to Sample` or equivalent button label
- `pending_global_sample_idx`
- `sample_number_input`
- help text explaining global/full batch order
- does not use `key="sample_idx"` mutation pattern

### 6. Existing tests still pass
- Save / Save and Next
- Previous / Next global navigation
- one-shot toast
- CSV/JSONL persistence
- chart framing/marker/gap compression

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

Manual GUI smoke:
```bash
./scripts/run_eurusd_review_gui.sh
```

Manual checks:
1. Type Sample Number `34`.
2. Click `Go to Sample`.
3. Confirm sidebar shows `Sample 34 / 100`.
4. Confirm chart/header changes to the corresponding sample.
5. Confirm completed values reload if reviewed.
6. Change Candidate Type filter.
7. Type another Sample Number and click Go.
8. Confirm jump still uses full batch order, not filtered list.
9. Confirm no old save toast appears.
10. Confirm Save, Save and Next, Previous, Next still work.

## Commit Requirements

Work directly on `main`.

Suggested commit:
```bash
git add cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py cajas/tests/test_eurusd_pattern_review_gui.py tasks/022_fix_eurusd_global_sample_jump_action.md
git commit -m "fix: make EURUSD sample number jump actionable"
```

Since user allows committing all `tasks/**/*.md`, commit this prompt wherever it is placed.

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Exact root cause
- Go to Sample behavior
- Filter interaction behavior
- Previous/Next regression status
- Save/Save and Next regression status
- Toast regression status
- CSV/JSONL persistence status
- Validation command results
- Manual GUI smoke result if run
- `git status --short`
- Push status: not pushed
- Manual push command:

```bash
git push origin main
```
