# Phase 7526–7645 — EURUSD 15m GUI Save Actions Regression Fix

## Context

You are working in the Qlib Base / qlib-cajas repository.

Current workflow preference:

- Work directly on `main`.
- Do not create a new feature branch unless explicitly requested.
- Do not perform automated merge operations.

Current GUI state:

- EURUSD 15m GUI review app launches.
- K-line chart renders.
- Compact mode is enabled by default.
- Required fields are visible in the current screenshot:
  - Pattern Label
  - Market Context
  - Direction Context
  - Review Status
  - Structure Quality
  - Follow-through Quality
  - Review Confidence
  - Review Notes
- However, the user reports:
  - `Save`
  - `Save and Next`
  - `Reset Form`
  do not work correctly.

This is a blocking regression.

Do not continue layout polishing until save/reset behavior is fixed and validated.

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

Fix the GUI action buttons so manual review can proceed safely.

Required behavior:

1. `Save` writes/updates the current sample row in:
   - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv`
2. `Save and Next` saves the current row, then advances to the next sample.
3. `Reset Form` resets only the current form fields to defaults and does not corrupt saved data.
4. Existing completed rows are loaded back into the form when revisiting a sample.
5. Saving must be duplicate-safe by `sample_id`.
6. Forbidden trading/action columns must never be written.
7. All required review fields must be persisted.

## Required Review Fields

The save payload must include and persist these review fields:

```text
human_pattern_label
market_context
direction_context
structure_quality
follow_through_quality
review_confidence
review_notes
review_status
```

User-facing labels:

```text
Pattern Label
Market Context
Direction Context
Structure Quality
Follow-through Quality
Review Confidence
Review Notes
Review Status
```

## Required Work

### 1. Reproduce action button behavior

Inspect and run locally if possible:

```bash
./scripts/run_eurusd_review_gui.sh
```

In the app:

1. Change a sample from pending to reviewed.
2. Change Pattern Label / Market Context / Direction Context.
3. Set score sliders.
4. Add Review Notes.
5. Click `Save`.
6. Verify completed CSV exists and contains the updated row.
7. Return to the same sample and verify fields reload.
8. Click `Save and Next`.
9. Verify current row is saved and sample index advances.
10. Click `Reset Form`.
11. Verify current form resets to default values but does not delete saved rows unless explicitly saved after reset.

If manual GUI launch is not possible in the run environment, reproduce via helper/unit tests and Streamlit code inspection.

### 2. Inspect likely root causes

Inspect:

```text
cajas/apps/eurusd_pattern_review_app.py
cajas/research/eurusd_pattern_review_gui.py
```

Likely causes to check:

- Streamlit widget keys changed during compact layout work.
- Buttons are placed in columns but callbacks use stale values.
- `st.session_state` sample index is not updated correctly.
- `Save and Next` advances index before saving current values.
- `Reset Form` clears state keys that are immediately overwritten.
- Form values are read from wrong keys.
- Review field names mismatch schema:
  - UI label vs persisted column name.
- Compact-mode notes changed from `text_area` to `text_input` but save payload still reads old key.
- `review_status` key/value not included in save payload.
- completed output path not passed into save helper.
- save helper sanitizes out needed columns accidentally.
- written CSV includes duplicates or does not flush to disk.
- errors are swallowed and not shown in UI.

### 3. Make save actions explicit and testable

Refactor if needed so there is a clear helper path:

In:

```text
cajas/research/eurusd_pattern_review_gui.py
```

Ensure there are pure helpers for:

```python
build_review_update_row(...)
save_or_update_completed_review(...)
merge_completed_review_rows(...)
default_review_values(...)
sanitize_review_notes(...)
forbidden_column_filter(...)
```

The app should call these helpers rather than embedding fragile save logic only in UI code.

### 4. Fix Streamlit widget keys

Ensure every review widget has a stable key that includes the current `sample_id` or is explicitly reset when the selected sample changes.

Recommended pattern:

- Keep current selected sample id in session state:
  - `current_sample_id`
- When selected sample changes:
  - load existing completed values for that sample if available
  - otherwise load default values
- Widget keys should be stable and explicit, for example:
  - `review_pattern_label`
  - `review_market_context`
  - `review_direction_context`
  - `review_structure_quality`
  - `review_follow_through_quality`
  - `review_confidence`
  - `review_notes`
  - `review_status`

Avoid accidental key collisions with previous layout versions.

### 5. Save button behavior

`Save` must:

1. Read current widget values.
2. Build one review row for current sample.
3. Validate/sanitize the row.
4. Save/update by `sample_id`.
5. Write completed CSV to configured output path.
6. Show visible success message:
   - `Saved sample_id=...`
7. Show visible error message if save fails.

It must not change sample index.

### 6. Save and Next behavior

`Save and Next` must:

1. Perform the exact same save as `Save`.
2. Only if save succeeds, advance to next sample.
3. Update session state so the next sample's form values load correctly.
4. Show a visible message:
   - `Saved sample_id=... and moved to next sample`

It must not skip saving due to stale state.

### 7. Reset Form behavior

`Reset Form` must:

1. Reset current form widget values to defaults:
   - `human_pattern_label`: `unclear`
   - `market_context`: `unclear`
   - `direction_context`: `unclear`
   - `structure_quality`: `3`
   - `follow_through_quality`: `3`
   - `review_confidence`: `3`
   - `review_notes`: `""`
   - `review_status`: `pending`
2. Not delete completed CSV.
3. Not remove existing saved row unless the user subsequently clicks Save.
4. Show visible message:
   - `Form reset for sample_id=...`

### 8. Required UI feedback

Add visible status messages near the buttons:

- last saved sample_id
- save output path
- save success/failure
- reset success
- current selected sample_id

This can be compact but must be visible enough for debugging.

### 9. Tests

Update:

```text
cajas/tests/test_eurusd_pattern_review_gui.py
```

Add tests for pure helper behavior:

1. saving a new review row creates completed CSV
2. saving the same `sample_id` updates row instead of duplicating
3. saved row includes:
   - `structure_quality`
   - `follow_through_quality`
   - `review_confidence`
   - `review_notes`
   - `review_status`
4. forbidden trading/action columns are removed
5. notes sanitize `NaN` to empty string
6. default review values match reset defaults
7. merging completed values back into batch state preserves saved fields
8. save-and-next helper, if factored, saves before advancing
9. reset defaults do not delete saved output

Do not require browser automation.

Do not require launching Streamlit in tests.

### 10. Optional manual smoke script

If useful, add a small internal helper/test fixture but do not overbuild.

Do not add trading logic.

### 11. Documentation

Update minimally:

```text
cajas/docs/eurusd_pattern_research_kickoff.md
cajas/README.md
tasks/eurusd_15m_research_end_to_end_roadmap.md
```

Document:

- Save writes/updates current sample by `sample_id`.
- Save and Next saves first, then advances.
- Reset Form resets visible form only and does not delete saved CSV.
- Completed output path:
  - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv`

### 12. Validation

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

### 13. Manual verification checklist

After code/tests pass, manually launch GUI:

```bash
./scripts/run_eurusd_review_gui.sh
```

Verify on one sample:

1. Change Pattern Label to `weak_pattern`.
2. Change Market Context.
3. Change Direction Context.
4. Change all three score sliders.
5. Add one-line Review Notes.
6. Change Review Status to `reviewed`.
7. Click Save.
8. Confirm visible save message.
9. Confirm completed CSV exists.
10. Confirm completed CSV has one row for sample_id.
11. Change a value and Save again.
12. Confirm still one row for sample_id, updated value.
13. Click Save and Next.
14. Confirm current row saved and sample index advances.
15. Click Reset Form on next sample.
16. Confirm form resets to defaults.

### 14. Commit Guidance

Work directly on `main`.

Before editing:

```bash
git checkout main
git pull origin main
git status --short --branch
```

Suggested commit:

```bash
git add   cajas/apps/eurusd_pattern_review_app.py   cajas/research/eurusd_pattern_review_gui.py   cajas/tests/test_eurusd_pattern_review_gui.py   cajas/docs/eurusd_pattern_research_kickoff.md   cajas/README.md   tasks/eurusd_15m_research_end_to_end_roadmap.md   tasks/phase_7526_7645_eurusd_15m_gui_save_actions_regression_fix_prompt.md

git commit -m "fix: repair EURUSD GUI review save actions"
```

Push directly to main only after validation:

```bash
git push origin main
```

## Final Response Required

Report:

- active branch
- confirmation work was done on `main`
- commit created
- files changed
- root cause of broken Save / Save and Next / Reset Form
- confirmation Save writes completed CSV
- confirmation Save updates existing `sample_id` without duplicates
- confirmation Save and Next saves before advancing
- confirmation Reset Form resets visible fields without deleting saved CSV
- confirmation all required review fields persist
- validation results
- fast validation runtime
- manual GUI smoke result if run
- push status
- confirmation no review schema fields were removed
- confirmation no labels were invented
- confirmation no trading signals/orders/model training were produced
- confirmation no automated merge was performed
