# 037 — Compact Review Form Width and Move Action Buttons to the Right Side

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current GUI state:
- Top Streamlit chrome/header has already been compacted.
- Review page still uses too much horizontal/vertical space in the form section.
- Screenshot/user feedback shows:
  - `Review Labels` spans too wide.
  - `Bad Sample Workflow` spans too wide.
  - Action buttons (`Save`, `Save and Next`, `Previous Sample`, `Next Sample`, `Reject Sample`) still sit below and consume extra vertical space.
- User wants:
  - Review form blocks narrower and left-aligned.
  - Right-side free space used for buttons/action area.
  - Keep the UI compact and practical for repeated review work.

User rule:
- Directly produce the next prompt markdown file.
- Include a concise explanation of what it does.
- Do not ask for confirmation first.

Hard boundaries:
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only; no SQLite.
- Do not reset/rebuild batch.
- Do not delete completed/rejected CSV/JSONL.
- No model training.
- No trading signals/orders.
- No Qlib core changes.

## Objective

Refactor the EURUSD review form layout so:
1. `Review Labels` becomes narrower and left-aligned.
2. `Bad Sample Workflow` becomes narrower and left-aligned.
3. Action buttons move into the right-side free area instead of occupying a full-width row below.
4. Vertical space usage improves without harming usability.

## Desired Layout

Target a two-column content section below the chart/diagnostics:

### Left column (main form area)
Contains:
- `Review Labels`
- review dropdowns/sliders/notes
- `Bad Sample Workflow`
- reject reason / reject notes / confirm reject checkbox

This left column should be narrower than full page width, for example ~60–70% width.

### Right column (action/control area)
Contains:
- `Save`
- `Save and Next`
- `Previous Sample`
- `Next Sample`
- `Reject Sample`

Optional:
- `Go to Sample` / jump controls can remain in sidebar if already there.
- `Last Save Details` can stay where it is unless moving it is low-risk.

The button area should:
- be visually compact
- use vertical stacking or a compact grid if needed
- remain easy to click
- not push the main form wider again

## Required Implementation Guidance

### 1. Refactor layout in `eurusd_pattern_review_app.py`

Use Streamlit columns for the lower form area, e.g.:

```python
left_col, right_col = st.columns([3, 1.4])
```

or similar ratio.

Within `left_col`:
- render `Review Labels`
- render `Bad Sample Workflow`

Within `right_col`:
- render all action buttons
- optionally show a compact help/hint text such as:
  - "Save before navigating"
  - "Reject uses current reject settings"

### 2. Keep review controls compact

Within `Review Labels`:
- keep 4 dropdowns in one row if possible:
  - Pattern Label
  - Market Context
  - Direction Context
  - Review Status
- keep sliders compact and aligned
- keep notes text area, but avoid oversized width if not necessary

Within `Bad Sample Workflow`:
- reduce width and avoid full-page stretching
- reject reason selectbox should only use left-column width
- reject notes textarea should be compact
- confirm reject checkbox remains visible and obvious

### 3. Button area layout

Preferred order:
```text
Save
Save and Next
Previous Sample
Next Sample
Reject Sample
```

Recommended arrangement:
- vertical stack
or
- 2-column small grid inside right column

Examples:
```python
with right_col:
    st.markdown("#### Actions")
    if st.button("Save"): ...
    if st.button("Save and Next"): ...
    ...
```

or:

```python
with right_col:
    a1, a2 = st.columns(2)
    ...
```

Important:
- preserve current button semantics exactly
- preserve disabled/clamped behavior for Previous/Next
- preserve `Save and Next` flow
- preserve `Reject Sample` confirmation behavior
- preserve one-shot save toast behavior

### 4. Preserve logic and persistence

Do not change:
- CSV-first persistence
- JSONL append audit
- Go to Sample behavior
- Save toast semantics
- reject registry behavior
- review state reload
- chart rendering
- candidate/batch/report logic

This task is layout-only unless a tiny rendering helper refactor is needed.

### 5. Optional compact section labels

If useful, reduce heading size:
- `Review Labels` -> smaller markdown heading
- `Bad Sample Workflow` -> smaller markdown heading
- `Actions` heading in right column

Example:
```python
st.markdown("### Review Labels")
st.markdown("### Bad Sample Workflow")
st.markdown("### Actions")
```

If this still feels too large, use `####`.

### 6. CSS tuning allowed

If needed, extend the compact CSS helper to:
- reduce spacing between widgets in these sections
- reduce margins below headings
- keep right column action area aligned near the top
- avoid giant blank gaps between sections

Do not use brittle CSS that risks breaking core layout unless necessary.

## Tests Required

Update `cajas/tests/test_eurusd_pattern_review_gui.py`.

Suggested regression checks:
1. App source contains a two-column form/action layout.
2. `Review Labels` and `Bad Sample Workflow` render in main/left area.
3. Action buttons exist in source and are grouped in right-side action section.
4. Save / Save and Next / Previous / Next / Reject button logic remains present.
5. Reject controls remain present.
6. Sidebar-based sample navigation/jump logic remains untouched.
7. Existing compact CSS/title logic still exists.
8. Existing GUI behavior tests still pass.

## Validation Commands

Run focused GUI tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_eurusd_pattern_review_gui.py \
  cajas/tests/test_validation_eurusd_pattern_review_gui.py
```

Run py_compile:

```bash
./.venv-qlib313/bin/python -m py_compile \
  cajas/apps/eurusd_pattern_review_app.py \
  cajas/research/eurusd_pattern_review_gui.py \
  cajas/tests/test_eurusd_pattern_review_gui.py
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
1. `Review Labels` is visibly narrower and left-aligned.
2. `Bad Sample Workflow` is narrower and left-aligned.
3. Button area is on the right side, not occupying a full-width bottom row.
4. Layout feels more compact vertically.
5. Save works.
6. Save and Next works.
7. Previous / Next works.
8. Reject Sample works.
9. Toast still appears properly.
10. No clipping/overlap on smaller desktop windows.

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas/apps/eurusd_pattern_review_app.py cajas/tests/test_eurusd_pattern_review_gui.py tasks/037_compact_review_form_and_move_actions_right.md
git commit -m "style: compact EURUSD review form layout"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Left/right layout changes
- Review Labels compacting behavior
- Bad Sample Workflow compacting behavior
- Action button placement
- Regression status for save/navigation/reject
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
- reset/rebuild review data
- delete completed/rejected CSV/JSONL
- add SQLite
- create branches
- push automatically
- train models
- produce trading signals/orders
- modify Qlib core
