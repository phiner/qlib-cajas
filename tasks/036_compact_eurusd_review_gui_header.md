# 036 — Compact EURUSD Review GUI Header and Hide Unneeded Streamlit Chrome

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current EURUSD 15m GUI:
- Streamlit app title/header area is visually large.
- Screenshot shows a large top band with:
  - Streamlit top chrome
  - `Deploy`
  - menu dots
  - large empty vertical space above `EURUSD 15m Review`
- User asks whether this area is useful and whether it can be removed to free space.

User preference:
- Compact review UI.
- Maximize vertical space for candlestick chart and review controls.
- Keep useful review information visible.
- Do not break save/navigation/reject/chart behavior.

Hard boundaries:
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only; no SQLite.
- Do not reset/rebuild active batch.
- Do not delete completed/rejected CSV/JSONL.
- No model training, no trading signals/orders, no Qlib core changes.

## Objective

Reduce wasted vertical space at the top of the Streamlit EURUSD review app by hiding unnecessary Streamlit chrome and compacting the app header/title area.

## Required Behavior

### 1. Hide Streamlit default top chrome where safe

Hide or reduce:
- Streamlit top header
- Deploy button area
- top toolbar chrome
- default menu/header spacing

Common Streamlit CSS targets may include:

```css
[data-testid="stHeader"] { display: none; }
[data-testid="stToolbar"] { display: none; }
[data-testid="stDecoration"] { display: none; }
#MainMenu { visibility: hidden; }
header { visibility: hidden; height: 0rem; }
```

Use the least invasive selectors that work for current Streamlit version.

Important:
- Do not hide sidebar.
- Do not hide toast notifications if possible.
- Do not hide useful app content.
- Do not break debug expanders.

### 2. Compact app title section

Current title:

```text
EURUSD 15m Review
```

Keep the title, but reduce wasted top margin.

Suggested layout:
- compact title row
- maybe smaller font
- maybe include progress on same row if convenient:
  ```text
  EURUSD 15m Review · Sample 1/100 · Reviewed 0
  ```
- Avoid large empty blank area above chart.

If title is currently rendered with `st.title`, consider replacing with compact markdown:

```python
st.markdown("### EURUSD 15m Review")
```

or a custom small header.

### 3. Add an explicit app-level compact CSS helper

In `cajas/apps/eurusd_pattern_review_app.py`, add a helper such as:

```python
def inject_compact_review_css() -> None:
    st.markdown(
        '''
        <style>
        ...
        </style>
        ''',
        unsafe_allow_html=True,
    )
```

Call it once near app startup after `st.set_page_config`.

Keep the CSS localized and documented.

### 4. Preserve core behavior

Do not change:
- chart rendering
- sample marker
- compressed axis
- Save / Save and Next
- Previous / Next
- Go to Sample
- Reject Sample workflow
- CSV/JSONL persistence
- review schema/dropdowns
- reports

### 5. Add optional config toggle if simple

If low-risk, allow disabling compact chrome hiding for debugging:

```python
HIDE_STREAMLIT_CHROME = True
```

or sidebar checkbox hidden under debug.

Not required if it adds complexity.

## Tests Required

Update `cajas/tests/test_eurusd_pattern_review_gui.py`.

Suggested tests:
1. App source contains compact CSS injection helper.
2. CSS includes Streamlit header/toolbar hiding selectors.
3. App still renders/keeps `EURUSD 15m Review` title text.
4. Static regression:
   - app does not hide sidebar selectors.
   - app does not remove toast helper.
5. Existing GUI tests still pass:
   - Save / Save and Next
   - Previous / Next
   - Go to Sample
   - Reject Sample
   - chart marker/framing/gap compression

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
1. Top Streamlit Deploy/header area is hidden or greatly reduced.
2. `EURUSD 15m Review` title remains visible but compact.
3. Chart starts higher on the page.
4. Sidebar still works.
5. Toast still appears after Save.
6. Save / Save and Next works.
7. Go to Sample works.
8. Reject Sample controls still work.
9. Debug expanders still work.

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas/apps/eurusd_pattern_review_app.py cajas/tests/test_eurusd_pattern_review_gui.py tasks/036_compact_eurusd_review_gui_header.md
git commit -m "style: compact EURUSD review GUI header"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- What Streamlit chrome was hidden
- Header/title compact behavior
- Vertical-space improvement
- Regression status for chart/save/navigation/reject
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
