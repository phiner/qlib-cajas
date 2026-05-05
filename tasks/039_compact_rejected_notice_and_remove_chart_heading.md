# 039 — Move Rejected-Sample Warning to Toast/Compact Status and Remove Chart Heading

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current GUI state after recent compacting:
- Top Streamlit chrome is hidden/compacted.
- Main sample metadata was moved into `Sample Details`.
- Header is compact.
- Chart section still shows a `Chart` heading.
- Rejected samples currently show a full-width banner:
  ```text
  This sample is rejected/excluded.
  ```

User feedback:
- The rejected-sample warning should not occupy page layout space.
- It should behave like save feedback: toast/popup or compact non-layout notification.
- The `Chart` heading line is unnecessary and should be removed.
- Main page should prioritize the candlestick chart and review controls.

Hard boundaries:
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only; no SQLite.
- Do not reset/rebuild active batch.
- Do not delete completed/rejected CSV/JSONL.
- No model training.
- No trading signals/orders.
- No Qlib core changes.

## Objective

Remove remaining layout clutter above the chart:

1. Replace the full-width rejected-sample banner with a toast or compact non-layout notice.
2. Remove the `Chart` heading line entirely.
3. Keep rejected status discoverable in sidebar/debug/sample details.
4. Preserve all save/navigation/reject/chart behavior.

## Required Behavior

### 1. Rejected-sample notice should not take layout space

Current behavior:
```python
st.warning("This sample is rejected/excluded.")
```
or equivalent full-width page notice.

Replace with one of these:

Preferred:
- show a one-shot toast when the current sample is rejected:
  ```text
  This sample is rejected/excluded.
  ```
- use the existing one-shot toast mechanism if available.

Alternative:
- show compact status in sidebar only:
  ```text
  Rejected/excluded
  ```
- no full-width banner in main content area.

Do **not** render the warning as a full-width `st.warning` / `st.info` block above the chart.

### 2. Avoid toast spam on reruns

The rejected toast should not replay on every field change.

Use one-shot behavior similar to save toast:
- show when navigating to a rejected sample,
- show after `Go to Sample` lands on rejected sample,
- show after reject action succeeds if already implemented,
- do not show repeatedly on dropdown/slider/notes changes.

If one-shot rejected toast is too complex, prefer sidebar compact status over repeated toast.

### 3. Preserve rejected status visibility

Even if main banner is removed, rejected state must still be visible somewhere:

Recommended:
- sidebar caption:
  ```text
  Status: rejected/excluded
  ```
- `Sample Details` expander:
  ```text
  rejected=true
  rejection_reason=...
  rejection_notes=...
  ```

If current sample is rejected, `Reject Sample` button should either:
- be disabled,
- or show `Already rejected`,
- and `Unreject` only if already implemented.

### 4. Remove Chart heading line

Remove:

```text
Chart
```

or any equivalent `st.markdown("##### Chart")`.

The candlestick plot is self-evident. Do not replace it with another heading.

The chart should start immediately after compact header / optional sample details expander.

### 5. Preserve chart internals

Do not change:
- Plotly candlestick rendering
- sample marker
- compressed axis
- hover data
- Chart Debug Info expander
- diagnostics line

### 6. Preserve workflows

Do not change logic for:
- Save
- Save and Next
- Previous / Next
- Go to Sample
- Reject Sample
- rejected registry CSV/JSONL
- review labels
- sample details/debug

This is a layout/notification cleanup.

## Tests Required

Update `cajas/tests/test_eurusd_pattern_review_gui.py`.

Suggested tests:
1. App source does not render full-width rejected warning in main content:
   - no direct `st.warning("This sample is rejected/excluded")` in main flow
   - or if warning function exists, it is not used for rejected main banner.
2. Rejected status is still present in sidebar or sample details/debug.
3. Rejected notification uses one-shot toast or compact sidebar status.
4. App no longer renders `st.markdown("##### Chart")` or equivalent chart heading.
5. Existing chart diagnostics/debug still present.
6. Existing Save / Save and Next / Previous / Next / Go to Sample / Reject tests still pass.

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
1. Open a rejected sample.
2. Confirm no full-width rejected banner occupies top page space.
3. Confirm rejected status appears as toast once or compact sidebar/sample-details status.
4. Change dropdown/slider/notes and confirm rejected toast does not replay repeatedly.
5. Confirm `Chart` heading line is gone.
6. Confirm chart starts higher.
7. Confirm Save / Save and Next / Previous / Next work.
8. Confirm Reject Sample workflow still works.
9. Confirm Go to Sample can still open rejected sample and status is visible.

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas/apps/eurusd_pattern_review_app.py cajas/tests/test_eurusd_pattern_review_gui.py tasks/039_compact_rejected_notice_and_remove_chart_heading.md
git commit -m "style: compact EURUSD rejected notice and chart header"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Rejected notice behavior
- Rejected toast/sidebar status behavior
- Chart heading removal
- Regression status for save/navigation/reject/chart
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
