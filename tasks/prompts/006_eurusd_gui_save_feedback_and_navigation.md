# 006 — Polish EURUSD GUI Save Feedback and Review Navigation

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current EURUSD 15m review GUI status:
- CSV/JSONL persistence works.
- `Save` works.
- `Save and Next` works.
- `Reset Form` works.
- Compressed market-closed/weekend gap chart behavior works.
- Streamlit app starts successfully.
- User manually checked the UI and says most things look okay.

User feedback:
1. The green save status block remains visible in the main chart/review area for too long and takes too much space.
2. Save success feedback should be a smaller notification, preferably in the top-right/toast style.
3. The GUI should provide an obvious way to go back to the previous sample.
4. Add clear navigation controls/settings for moving between samples.

Current screenshot shows a large persistent green message:

```text
save_and_next: sample_id=eurusd15m_000030 (update) |
csv=tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv |
jsonl=tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed_events.jsonl [written] |
sample_index=8
```

This should not permanently occupy central review space.

User preference:
- Work directly on `main`.
- Use simple sequential prompt numbering under `tasks/prompts/`.
- CSV/JSONL only.
- No SQLite.
- Do not create branches.
- Do not push automatically.

## Objective

Polish the GUI review workflow:

1. Replace large persistent save success blocks with compact transient feedback.
2. Keep detailed save diagnostics available in debug/sidebar, not as a large central banner.
3. Add explicit Previous / Next sample navigation controls.
4. Preserve all persistence and chart behavior.

## Required Behavior

### 1. Compact save feedback

For successful `Save` and `Save and Next`:
- Prefer `st.toast(...)` if available in the installed Streamlit version.
- If `st.toast` is unavailable, use a compact `st.success(...)` in a small sidebar/status area, not a large central block under the chart.

Suggested success text:

```text
Saved eurusd15m_000030
```

For Save and Next:

```text
Saved eurusd15m_000030 → moved to sample 31/500
```

Do not show full CSV/JSONL paths in the main success message.

### 2. Keep detailed persistence status in debug/status expander

Move detailed text such as:
- completed CSV path
- JSONL path
- action type
- sample_id
- sample_index
- JSONL warning
into one of:
- sidebar compact status area
- expander: `Last Save Details`
- existing debug section

This should be available for troubleshooting but not visually dominate the page.

### 3. Error/warning handling

For hard errors:
- still show visible error with `st.error`
- do not hide errors in toast only

For CSV success + JSONL warning:
- show compact warning
- preserve detailed warning in `Last Save Details`

Suggested behavior:
- success: toast + optional compact status
- warning: `st.warning` compact
- error: `st.error` visible

### 4. Add Previous / Next sample navigation

Add explicit navigation controls near the review action buttons or in sidebar:

```text
Previous Sample
Next Sample
```

Behavior:
- `Previous Sample`: move to previous sample without saving current form.
- `Next Sample`: move to next sample without saving current form.
- `Save and Next`: save current sample first, then move next.
- Navigation should be clamped:
  - first sample cannot go below 0
  - last sample cannot exceed row_count - 1
- Buttons should be disabled when not applicable if possible:
  - Previous disabled at first sample
  - Next disabled at last sample

Important:
- Navigating away without saving may discard visible unsaved form edits. Add a small hint:

```text
Use Save or Save and Next to persist edits before navigating.
```

No modal confirmation is required in this phase.

### 5. Use existing staged navigation pattern

Do not reintroduce Streamlit session-state mutation errors.

Continue using:
- `current_sample_idx`
- `sample_idx_widget`
- `pending_sample_idx`

or equivalent staged/rerun-safe pattern.

Do not mutate a widget-bound key after widget instantiation.

### 6. Keep sample index display clear

Show current position:

```text
Sample 31 / 500
sample_id=eurusd15m_000030
```

If there is a numeric sample selector, keep it stable and synchronized with canonical state.

### 7. Preserve chart behavior

Do not change:
- compressed market-closed/weekend gap axis
- vertical gap markers
- raw timestamp hover/debug
- sample anchor marker

### 8. Preserve persistence behavior

Do not change:
- completed CSV schema
- JSONL event schema
- duplicate-safe update by `sample_id`
- reset behavior
- review labels/scores

## Suggested Implementation Notes

In `cajas/apps/eurusd_pattern_review_app.py`:

- Replace central persistent save success display with helper:

```python
def show_action_feedback(result):
    if result.ok and not result.warning:
        if hasattr(st, "toast"):
            st.toast(f"Saved {result.sample_id}", icon="✅")
        else:
            st.sidebar.success(f"Saved {result.sample_id}")
    elif result.warning:
        st.warning(...)
    else:
        st.error(...)
```

- Store detailed status in:

```python
st.session_state["last_save_details"] = {...}
```

- Render details under expander:

```python
with st.expander("Last Save Details", expanded=False):
    st.json(st.session_state.get("last_save_details", {}))
```

For navigation:
- Add helper functions in `cajas/research/eurusd_pattern_review_gui.py` if not already present:
  - `previous_sample_index(current_idx, row_count)`
  - `next_sample_index(current_idx, row_count)`
  - `clamp_sample_index(value, row_count)`

- Use pending navigation:

```python
if previous_clicked:
    st.session_state["pending_sample_idx"] = previous_sample_index(current_idx, row_count)
    st.rerun()
```

## Tests Required

Add/update tests in `cajas/tests/test_eurusd_pattern_review_gui.py`.

Required test coverage:
1. Previous index:
   - from 5 -> 4
   - from 0 -> 0

2. Next index:
   - from 5 -> 6
   - from last -> last

3. Clamp:
   - negative -> 0
   - too large -> last
   - empty row_count handled safely

4. Save details formatting:
   - compact user message does not include full CSV/JSONL paths
   - detailed payload does include paths

5. Static regression:
   - app source no longer renders full save details as a large central success block if practical to assert.
   - app source contains `Last Save Details` or equivalent details expander.
   - app source contains `Previous Sample` and `Next Sample`.

6. Existing regression tests:
   - Save helper
   - Save and Next helper
   - Reset helper
   - CSV/JSONL persistence
   - gap compression
   - sample index staged navigation

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
1. Click `Save`.
2. Confirm compact success notification appears.
3. Confirm no large persistent green block dominates central area.
4. Confirm details are available in `Last Save Details` or sidebar/debug.
5. Click `Save and Next`.
6. Confirm compact notification and sample advances.
7. Click `Previous Sample`.
8. Confirm sample moves back.
9. Click `Next Sample`.
10. Confirm sample moves forward.
11. At first sample, Previous is disabled or clamped.
12. At last sample, Next is disabled or clamped.
13. Confirm Reset still resets visible form only.
14. Confirm compressed chart gap marker still renders.
15. Confirm CSV/JSONL still update as before.

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py cajas/tests/test_eurusd_pattern_review_gui.py tasks/prompts/006_eurusd_gui_save_feedback_and_navigation.md
git commit -m "feat: polish EURUSD GUI save feedback and navigation"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Save feedback behavior
- Last Save Details/debug behavior
- Previous Sample behavior
- Next Sample behavior
- Save and Next behavior
- Reset behavior
- CSV/JSONL persistence status
- Chart gap compression regression status
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
- delete completed review CSV/JSONL data
- revert compressed chart gap behavior
