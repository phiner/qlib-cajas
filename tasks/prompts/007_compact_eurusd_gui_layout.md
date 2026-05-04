# 007 — Compact EURUSD GUI Diagnostics and Action Button Layout

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Recent status:
- EURUSD 15m GUI persistence works with CSV/JSONL.
- Save / Save and Next works.
- Previous Sample / Next Sample navigation exists.
- Large central save status was replaced by compact toast/sidebar feedback.
- Compressed market-closed/weekend gap chart behavior is implemented.
- User now wants a smaller, cleaner review layout.

User feedback:
1. These two chart diagnostic lines should be combined into one line:

```text
Window 91 bars | traces 1 | exact match ✓ | fallback ✗ | target index 60

display_axis=real_time_axis | time_gap_count=0
```

Desired:

```text
Window 91 bars | traces 1 | exact match ✓ | fallback ✗ | target index 60 | display_axis=real_time_axis | time_gap_count=0
```

2. Navigation buttons should be on the same row after the save buttons, not on a separate row.

Desired action row:

```text
Save | Save and Next | Previous Sample | Next Sample
```

3. `Reset Form` can be removed from the main GUI.

User preference:
- Work directly on `main`.
- Use simple sequential prompt numbering under `tasks/prompts/`.
- CSV/JSONL only.
- No SQLite.
- Do not create branches.
- Do not push automatically.

## Objective

Make the EURUSD 15m review GUI more compact by:
- merging chart diagnostic text into one line,
- placing navigation buttons on the same row as save buttons,
- removing the visible `Reset Form` button from the main review UI.

Do not change persistence or chart computation semantics.

## Required Changes

### 1. Merge chart diagnostics into one line

In `cajas/apps/eurusd_pattern_review_app.py`, find where chart diagnostics are rendered.

Currently there may be two separate `st.caption`, `st.markdown`, or text blocks similar to:

```python
st.caption("Window 91 bars | traces 1 | exact match ✓ | fallback ✗ | target index 60")
st.caption("display_axis=real_time_axis | time_gap_count=0")
```

Change to a single compact line:

```text
Window 91 bars | traces 1 | exact match ✓ | fallback ✗ | target index 60 | display_axis=... | time_gap_count=...
```

If gap compression metadata exists, include the most useful compact fields only:
- `display_axis`
- `time_gap_count`
- optionally `gap_markers`
- optionally `largest_gap_hours` only when there is a gap

Avoid wrapping into multiple visible lines where possible.

Full details can remain in `Chart Debug Info`.

### 2. Put action/navigation buttons on one row

Current layout likely uses separate columns/rows for:
- Save
- Save and Next
- Reset Form
- Previous Sample
- Next Sample

Change main action row to:

```text
Save | Save and Next | Previous Sample | Next Sample
```

Suggested Streamlit layout:

```python
save_col, save_next_col, prev_col, next_col = st.columns([1, 1.2, 1.2, 1])
```

or similar.

Behavior:
- Save: persist current review only.
- Save and Next: save then advance.
- Previous Sample: navigate previous without saving.
- Next Sample: navigate next without saving.

Buttons should stay clamp-safe:
- Previous disabled at first sample if supported.
- Next disabled at last sample if supported.

### 3. Remove Reset Form from main GUI

Remove the visible `Reset Form` button from the main layout.

Do not delete underlying helper functions/tests unless they are no longer useful:
- Keeping reset helpers is okay for future/debug/testing.
- But the main GUI should not show `Reset Form`.

If a reset capability is still desired for debugging, it may be placed inside an advanced/debug expander, but the user's request says it can be removed, so simplest is to remove it from visible UI.

Important:
- Removing visible reset must not affect CSV/JSONL save behavior.
- Do not delete completed CSV/JSONL data.
- Do not change review defaults.

### 4. Preserve compact save feedback

Do not reintroduce the large central green save status block.

Keep:
- toast/sidebar compact success
- `Last Save Details` expander for full CSV/JSONL paths

### 5. Preserve chart gap behavior

Do not revert:
- compressed sequential axis when gaps exist
- vertical gap markers
- original timestamp hover/debug
- sample anchor marker

## Tests Required

Update tests in `cajas/tests/test_eurusd_pattern_review_gui.py`.

Suggested tests:
1. Compact diagnostics formatting:
   - helper returns a single string containing window/traces/exact/fallback/target index/display_axis/time_gap_count.
   - no newline in compact diagnostics string.

2. Static app layout regression:
   - source contains `Previous Sample` and `Next Sample`.
   - source contains `Save and Next`.
   - source does not contain visible `Reset Form` button text, or if it remains only in tests/helper/docs, ensure app UI no longer renders it.
   - app source includes one-row column layout for save/navigation if practical.

3. Existing behavior tests still pass:
   - Save helper
   - Save and Next helper
   - navigation index helpers
   - CSV/JSONL persistence
   - gap compression
   - sample anchor mapping

If reset helper tests exist, they can remain, but no test should require the main UI to show `Reset Form`.

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
1. Chart diagnostics appear as one compact line.
2. `display_axis` and `time_gap_count` are on the same line as window/traces info.
3. Action buttons are on one row:
   - Save
   - Save and Next
   - Previous Sample
   - Next Sample
4. `Reset Form` is no longer visible in the main GUI.
5. Save still works.
6. Save and Next still works.
7. Previous Sample and Next Sample still work.
8. Last Save Details still contains full details.
9. Compressed gap markers still work.
10. No large central save success block returns.

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py cajas/tests/test_eurusd_pattern_review_gui.py tasks/prompts/007_compact_eurusd_gui_layout.md
git commit -m "style: compact EURUSD GUI review layout"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Diagnostic line layout confirmation
- Button row layout confirmation
- Reset Form visibility status
- Save behavior confirmation
- Save and Next behavior confirmation
- Previous/Next navigation confirmation
- Last Save Details status
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
- reintroduce large central save success block
