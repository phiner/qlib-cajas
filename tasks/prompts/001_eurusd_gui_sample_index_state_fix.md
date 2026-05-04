# Phase 8126-8245 — Fix EURUSD GUI Save-and-Next Sample Index Session-State Regression

## Context

We are working directly on `main` for the Qlib Base / `qlib-cajas` project.

Recent state:
- CSV/JSONL persistence is working.
- `Save` now shows green success status.
- `Save and Next` writes CSV/JSONL successfully, but then fails while advancing to the next sample.

User-reported UI error:

```text
Save and Next failed for sample_id=eurusd15m_000027:
st.session_state.sample_idx cannot be modified after the widget with key sample_idx is instantiated.
```

The screenshot also shows the green persistence status beneath the red error:

```text
save: sample_id=eurusd15m_000027 (update) |
csv=tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv |
jsonl=tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed_events.jsonl [written] |
sample_index=0
```

Interpretation:
- CSV save succeeded.
- JSONL append succeeded.
- The remaining failure is purely Streamlit session-state ordering for sample navigation.
- The app is modifying `st.session_state["sample_idx"]` after a widget using `key="sample_idx"` has already been instantiated in the same script run.

Hard boundaries:
- Do not add SQLite.
- Do not introduce trading signals/orders.
- Do not train models.
- Do not modify Qlib core.
- Do not create branches.
- Work directly on `main`.
- Do not push automatically.

## Objective

Fix `Save and Next` so it saves successfully and advances to the next sample without Streamlit session-state mutation errors.

The fix must preserve:
- CSV authoritative latest-state persistence by `sample_id`
- JSONL append-friendly audit events
- duplicate-safe completed CSV updates
- completed row reload on revisit
- reset behavior that does not delete saved data

## Root Cause to Fix

Search current app code for sample index handling:

```bash
grep -R "sample_idx" -n cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py cajas/tests
```

Likely problematic pattern:

```python
sample_idx = st.number_input(..., key="sample_idx", ...)
...
if save_and_next:
    st.session_state["sample_idx"] = next_idx
```

Streamlit does not allow changing a session state key after the widget bound to the same key has been created in that same run.

## Required Implementation

### 1. Decouple widget key from canonical state key

Do not bind the navigation widget directly to the same key that the app mutates after save.

Preferred pattern:

```python
CANONICAL_INDEX_KEY = "current_sample_idx"
WIDGET_INDEX_KEY = "sample_idx_widget"
PENDING_INDEX_KEY = "pending_sample_idx"
```

At the very top of `main()`, before any widgets are instantiated:

```python
if PENDING_INDEX_KEY in st.session_state:
    st.session_state[CANONICAL_INDEX_KEY] = clamp_index(
        st.session_state.pop(PENDING_INDEX_KEY),
        row_count,
    )

if CANONICAL_INDEX_KEY not in st.session_state:
    st.session_state[CANONICAL_INDEX_KEY] = 0
```

The widget may use `key=WIDGET_INDEX_KEY`, not `key=CANONICAL_INDEX_KEY`.

When the widget changes:
- update canonical index before dependent widgets render, or
- use an `on_change` callback that copies widget value to canonical index safely, or
- avoid index widget callback entirely and use explicit Previous/Next buttons.

### 2. Save-and-Next must stage navigation, then rerun

After successful save:

```python
next_idx = clamp_index(current_idx + 1, row_count)
st.session_state[PENDING_INDEX_KEY] = next_idx
st.session_state["last_action_msg"] = ...
st.rerun()
```

Do not directly assign to the widget-bound key after the widget exists.

### 3. Preserve Save behavior

`Save`:
- persists CSV
- appends JSONL audit event
- updates status
- does not advance index
- does not mutate widget-bound sample index after instantiation

### 4. Preserve Reset Form behavior

`Reset Form`:
- resets only visible review field session keys
- does not delete CSV
- does not delete JSONL
- does not advance index
- if rerun is needed, stage reset state before rerun

### 5. Completed-row reload after navigation

When changing samples:
- load completed values if `sample_id` exists in completed CSV
- otherwise defaults
- update review field session keys before those widgets are instantiated
- avoid changing field keys after widgets are instantiated in the same run

### 6. Avoid old `sample_idx` key conflicts

If existing saved Streamlit session has `sample_idx`, migrate safely at top of `main()` before any widget with that key is created:

```python
if "sample_idx" in st.session_state and CANONICAL_INDEX_KEY not in st.session_state:
    st.session_state[CANONICAL_INDEX_KEY] = st.session_state["sample_idx"]
```

Then stop creating widgets with `key="sample_idx"` if the app later mutates that key.

### 7. Add pure helper tests

Add small pure helpers in `cajas/research/eurusd_pattern_review_gui.py`, for example:

```python
def clamp_sample_index(value: int, row_count: int) -> int: ...
def next_sample_index(value: int, row_count: int) -> int: ...
def should_advance_after_save(result) -> bool: ...
```

Tests should cover:
- next index from 0 to 1
- next index at last row remains last row
- negative/out-of-range clamp
- hard persistence failure does not advance
- CSV success with JSONL warning can advance if current semantics allow it

### 8. Regression test for no direct post-widget mutation pattern

Since Streamlit UI is hard to unit test, add static or structural test to prevent recurrence:
- app source should not include `st.session_state["sample_idx"] =` after creating a widget with `key="sample_idx"`, or
- app should no longer use `key="sample_idx"` at all.
- Prefer asserting `key="sample_idx"` is absent from app source, replaced by e.g. `sample_idx_widget`.

Example:

```python
source = Path("cajas/apps/eurusd_pattern_review_app.py").read_text()
assert 'key="sample_idx"' not in source
assert "current_sample_idx" in source
assert "pending_sample_idx" in source
```

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
1. Open the GUI.
2. Pick a sample.
3. Modify one review field.
4. Click `Save`.
5. Confirm green save status and no red error.
6. Modify one review field again.
7. Click `Save and Next`.
8. Confirm green save status and sample advances to the next sample.
9. Confirm no red `st.session_state.sample_idx cannot be modified` error.
10. Click Previous or select the prior sample.
11. Confirm completed values reload.
12. Click Reset Form.
13. Confirm visible values reset only; CSV/JSONL remain intact.
14. Watch terminal for no repeated widget default/session-state warnings related to `sample_idx`.

## Commit Requirements

Work directly on `main`.

Commit message suggestion:

```bash
git add cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py cajas/tests/test_eurusd_pattern_review_gui.py
git commit -m "fix: stage EURUSD GUI sample navigation state"
```

If docs/tasks are updated, include them only if needed.

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Exact root cause
- What changed in sample index state handling
- Save behavior confirmation
- Save-and-next behavior confirmation
- Reset behavior confirmation
- CSV behavior confirmation
- JSONL behavior confirmation
- Streamlit warning/error status
- Validation command results
- Manual GUI smoke result if run
- `git status --short`
- Push status: not pushed
- Manual push command:

```bash
git push origin main
```
