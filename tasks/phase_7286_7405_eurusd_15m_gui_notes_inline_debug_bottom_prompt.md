# Phase 7286–7405 — EURUSD 15m GUI Review Notes Inline and Debug Section Reposition

## Context

You are working in the Qlib Base / qlib-cajas repository.

Current workflow preference:

- Work directly on `main`.
- Do not create a new feature branch unless explicitly requested.
- Start from local `main`.
- If needed, sync with:
  - `git checkout main`
  - `git pull origin main`
- Do not perform automated merge operations.

Current GUI state:

- EURUSD 15m GUI review app is functional.
- K-line chart renders correctly.
- Compact mode is enabled by default.
- Chart diagnostics summary is visible.
- Detailed `Chart Debug Info (click to expand)` exists.
- Review form is more compact than before.
- `Review Notes` is sanitized and no longer displays `nan`.

Current user requests:

1. `Review Notes` should be on the same row as the label/control area, and the input should be one-line height only.
2. The hint text:
   - `Open "Chart Debug Info (click to expand)" for timestamp/window details.`
   and the expandable `Chart Debug Info` section are not user-input fields and should not sit in the main review area.
   They should be moved to the bottom, below the Save / Save and Next / Reset row.

Important clarification:

- `Chart Debug Info` is not something the human user needs to fill.
- It is diagnostic/read-only developer/debug information.
- It should stay available but should not interrupt the main review workflow.

Project constraints:

- EURUSD 15m Bid only.
- No 1H/4H aggregation.
- No live trading.
- No paper trading.
- No broker routing.
- No order generation.
- No production model training.
- No Qlib core modifications.
- No labels invented by automation.
- GUI remains review interface.
- CSV/JSONL remain durable storage/interchange.

## Goal

Polish the compact GUI layout so the main review workflow fits better on screen.

This phase should:

1. Convert `Review Notes` from a tall text area to a one-line input in compact mode.
2. Place `Review Notes` in the same row as the review controls if practical.
3. Keep optional notes behavior and blank/default sanitization.
4. Move the debug hint and detailed debug expander below the Save button row.
5. Keep the always-visible compact chart diagnostics near the chart.
6. Preserve all save/update/data behavior.

## Required Work

### 1. Update Review Notes layout

Inspect:

```text
cajas/apps/eurusd_pattern_review_app.py
```

Current notes field likely uses a text area.

In compact mode, replace or conditionally render notes as a one-line input:

```python
st.text_input("Review Notes", value=..., placeholder="Optional notes...")
```

or use an equivalent compact one-line input.

Requirements:

- Notes field must remain optional.
- Missing/NaN notes still sanitize to empty string.
- Do not display literal `nan`.
- User-entered notes must still be saved to completed CSV.
- In non-compact mode, it is acceptable to keep the taller text area, but compact mode should use one-line input.

Preferred compact layout:

- Row 1:
  - Pattern Label
  - Market Context
  - Direction Context
  - Review Status
- Row 2:
  - Structure Quality
  - Follow-through Quality
  - Review Confidence
  - Review Notes one-line input

Alternative acceptable layout:

- Put `Review Notes` on the same row as Review Status / buttons if that fits better.
- The key requirement is: notes should be one-line height and not consume a large vertical block.

### 2. Keep Save buttons close to review controls

Keep the main action buttons visible directly below the compact form:

```text
Save | Save and Next | Reset Form
```

Do not place debug text between the form fields and the buttons.

### 3. Move debug hint and expander to bottom

The following hint should move below the Save button row:

```text
Open "Chart Debug Info (click to expand)" for timestamp/window details.
```

The expandable debug section should also move below the Save button row:

```text
Chart Debug Info (click to expand)
```

Requirements:

- Keep the detailed debug info available.
- Keep it collapsed by default.
- It should not appear between the chart and review form.
- It should not appear between form fields and save buttons.
- It should appear after the main review action row.

### 4. Preserve compact chart diagnostics

The compact diagnostics summary near the chart should remain visible, for example:

```text
Window 91 bars | traces 1 | exact match ✓ | fallback ✗ | target index 60
```

This is useful and should stay near the chart.

Only the detailed debug hint/expander should move lower.

### 5. Tests

Update tests if helper behavior is touched:

```text
cajas/tests/test_eurusd_pattern_review_gui.py
```

Required checks:

1. NaN notes still sanitize to empty string.
2. Completed CSV save/update still preserves entered notes.
3. Completed CSV save/update still does not duplicate `sample_id`.
4. Forbidden trading/action columns are still removed.
5. Compact diagnostic summary formatting still works.

If a new helper is added for compact notes handling, test it.

Do not require launching Streamlit in tests.

### 6. Documentation

Update minimally:

```text
cajas/docs/eurusd_pattern_research_kickoff.md
cajas/README.md
tasks/eurusd_15m_research_end_to_end_roadmap.md
```

Document:

- compact mode now uses one-line Review Notes.
- Detailed Chart Debug Info is read-only diagnostics and appears below the action buttons.
- Users do not need to fill Chart Debug Info.
- GUI remains review-only.

### 7. Validation

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest   cajas/tests/test_eurusd_pattern_review_gui.py   cajas/tests/test_validation_eurusd_pattern_review_gui.py
```

Run py_compile:

```bash
./.venv-qlib313/bin/python -m py_compile   cajas/apps/eurusd_pattern_review_app.py   cajas/research/eurusd_pattern_review_gui.py   cajas/tests/test_eurusd_pattern_review_gui.py
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

### 8. Commit Guidance

Work directly on `main`.

Before editing:

```bash
git checkout main
git pull origin main
git status --short --branch
```

If clean, modify files directly on `main`.

Suggested commit:

```bash
git add   cajas/apps/eurusd_pattern_review_app.py   cajas/research/eurusd_pattern_review_gui.py   cajas/tests/test_eurusd_pattern_review_gui.py   cajas/docs/eurusd_pattern_research_kickoff.md   cajas/README.md   tasks/eurusd_15m_research_end_to_end_roadmap.md   tasks/phase_7286_7405_eurusd_15m_gui_notes_inline_debug_bottom_prompt.md

git commit -m "fix: streamline EURUSD GUI notes and debug layout"
```

Push directly to main only after validation:

```bash
git push origin main
```

Do not create a new branch unless explicitly requested.

Do not perform automated merge operations.

## Final Response Required

Report:

- active branch
- confirmation work was done on `main`
- commit created
- files changed
- whether Review Notes is one-line in compact mode
- where Review Notes is placed
- whether debug hint/expander moved below Save buttons
- whether compact chart diagnostics remain near chart
- whether save/update behavior is unchanged
- validation results
- fast validation runtime
- push status
- confirmation that GUI remains review interface and CSV/JSONL remain durable storage
- confirmation that no labels were invented
- confirmation that no trading signals/orders/model training were produced
- confirmation that no automated merge was performed
