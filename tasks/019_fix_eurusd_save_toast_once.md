# 019 — Fix EURUSD GUI Save Toast Reappearing on Field Changes

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current GUI behavior:
- Save / Save and Next work.
- Compact toast feedback is shown, e.g.
  `Saved eurusd15m_000026 → moved to sample 34/100`
- However, the toast appears again when the user changes review fields/options.
- This is noisy and misleading.

User request:
- The top-right save toast should appear only when a real save action occurs.
- It should not appear on every selectbox/field/note/score change.
- Keep Last Save Details if useful, but do not re-toast old messages.

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

Make save toast feedback one-shot:
- show toast immediately after `Save`
- show toast immediately after `Save and Next`
- do not show toast again on normal Streamlit reruns caused by form field changes
- do not show toast again when navigating unless a save happened

## Likely Root Cause

Streamlit reruns the script on every widget change.

The app probably stores something like:
```python
st.session_state["last_action_msg"] = "Saved ..."
```

and then renders:
```python
st.toast(st.session_state["last_action_msg"])
```

on every rerun.

That causes the old save toast to reappear after unrelated widget changes.

## Required Behavior

### 1. Separate persistent status from one-shot toast

Use two concepts:

```python
st.session_state["last_save_details"] = {...}      # persistent, for expander/debug
st.session_state["pending_toast_message"] = "..."  # one-shot, consumed once
```

or equivalent.

Rules:
- `last_save_details` can remain available in `Last Save Details`.
- `pending_toast_message` should be set only inside successful save handlers.
- The toast should be displayed once and then cleared immediately.

Example pattern:

```python
def enqueue_toast(message: str, icon: str = "✅") -> None:
    st.session_state["pending_toast_message"] = message
    st.session_state["pending_toast_icon"] = icon

def consume_pending_toast() -> None:
    msg = st.session_state.pop("pending_toast_message", None)
    icon = st.session_state.pop("pending_toast_icon", None)
    if msg:
        if hasattr(st, "toast"):
            st.toast(msg, icon=icon)
        else:
            st.sidebar.success(msg)
```

Call `consume_pending_toast()` once per rerun, preferably near the top of layout after Streamlit is ready.

### 2. Save handler behavior

On `Save`:
- persist CSV/JSONL
- update `last_save_details`
- enqueue toast message
- do not advance sample

On `Save and Next`:
- persist CSV/JSONL
- update `last_save_details`
- enqueue toast message
- stage pending sample index
- rerun safely

Important:
- If `Save and Next` sets pending navigation and calls rerun, ensure toast survives exactly one rerun and is then consumed once.
- After it is consumed, changing any field must not show it again.

### 3. Warning/error behavior

For hard errors:
- show `st.error` visibly in the same action run.
- do not silently put hard errors only in toast.

For CSV success + JSONL warning:
- show a compact warning once.
- keep details in `Last Save Details`.

Optional:
- use a one-shot warning message key similar to one-shot success toast.

### 4. Do not clear Last Save Details

The user may still want to inspect:
- sample id
- CSV path
- JSONL path
- action type
- status/warning

So `Last Save Details` should remain persistent until next save.

Only toast should be one-shot.

### 5. Do not trigger toast from field changes

Changing any of these should not enqueue or show toast:
- candidate type selection
- review labels
- market context
- direction context
- score sliders
- notes text area
- Previous Sample
- Next Sample
- opening/closing expanders
- chart interactions

Only actual persistence actions should enqueue toast:
- Save
- Save and Next

## Suggested Tests

Update `cajas/tests/test_eurusd_pattern_review_gui.py`.

Add pure helper tests if possible:

1. Toast enqueue/consume:
   - enqueue message
   - consume returns/shows message once
   - second consume returns nothing

2. Save details vs toast:
   - setting last_save_details does not imply pending_toast_message
   - pending_toast_message can be cleared while last_save_details remains

3. Save and Next staged rerun behavior:
   - toast key survives until next run
   - pending sample index can coexist with pending toast
   - consuming toast does not clear pending navigation before applied

4. Static regression:
   - app source should not call `st.toast(st.session_state["last_action_msg"])` or equivalent persistent-key toast directly.
   - app source should contain a pop/consume pattern for pending toast.
   - field widgets should not set pending toast keys.

Existing tests must still pass:
- Save / Save and Next
- Previous / Next
- CSV/JSONL persistence
- chart framing
- gap compression
- sample marker

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
1. Change a dropdown/score/notes field.
2. Confirm no old save toast appears.
3. Click Save.
4. Confirm toast appears once.
5. Change another field.
6. Confirm the old save toast does not reappear.
7. Click Save and Next.
8. Confirm toast appears once after save/navigation.
9. Change a field on the next sample.
10. Confirm the old save-and-next toast does not reappear.
11. Confirm Last Save Details still shows the latest save details.
12. Confirm Save / Save and Next / Previous / Next still work.

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py cajas/tests/test_eurusd_pattern_review_gui.py tasks/prompts/019_fix_eurusd_save_toast_once.md
git commit -m "fix: show EURUSD save toast only once"
```

Only add files that changed.

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Exact root cause
- Toast one-shot behavior
- Last Save Details behavior
- Save behavior
- Save and Next behavior
- Field-change no-toast confirmation
- Validation command results
- Manual GUI smoke result if run
- `git status --short`
- Push status: not pushed
- Manual push command:

```bash
git push origin main
```
