# 038 — Remove Redundant EURUSD Review Header Text and Keep Details in Debug

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current GUI state:
- Top Streamlit chrome has been hidden/compacted.
- Review Labels / Bad Sample Workflow have been compacted.
- Action buttons moved to right-side action column.
- User now sees redundant large text blocks above the chart:
  - `EURUSD 15m Review · Sample 1/100 · Reviewed 2`
  - `Sample eurusd15m_000028`
  - `sample_id=... | timestamp=... | type=... | confidence=... | priority=... | reasons=...`
  - `Candlestick Chart`
  - chart internal title also repeats sample metadata.

User feedback:
- These text blocks are not very useful in the main view.
- They consume vertical space and visually clutter the review workflow.
- The details can be kept in debug/expander/sidebar rather than shown prominently.

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

Reduce redundant text clutter above the candlestick chart by hiding or compacting repeated sample metadata in the main page.

The main review view should prioritize:
1. chart
2. review controls
3. action buttons
4. only minimal sample/progress status

Detailed sample metadata should remain accessible in:
- sidebar
- chart hover
- Chart Debug Info expander
- Last Save Details / debug area

## Required Behavior

### 1. Compact top page title

Current compact title:

```text
EURUSD 15m Review · Sample X/Y · Reviewed N
```

This can remain, but it should be the only prominent header.

Optional improvement:
- make it smaller if still too large:
  ```text
  #### EURUSD 15m Review · Sample X/Y · Reviewed N
  ```
- or keep as `###` if visually okay.

### 2. Remove or collapse redundant sample heading

Remove from main page:

```text
Sample eurusd15m_000028
```

or replace with a tiny one-line muted caption only if needed.

Preferred:
- remove it from main view.
- keep sample id in sidebar/debug.

### 3. Remove or collapse long sample metadata line

Remove from main page:

```text
sample_id=... | timestamp=... | type=... | confidence=... | priority=... | reasons=...
```

Move this to a compact expander:

```text
Sample Details
```

or merge into existing `Chart Debug Info`.

Preferred:
- keep this metadata in `Chart Debug Info (click to expand)` or a new compact `Sample Details` expander.
- do not show it by default.

### 4. Compact or remove `Candlestick Chart` heading

The chart section does not need a large heading if the chart is obvious.

Options:
- remove the `Candlestick Chart` heading entirely,
- or make it a small muted label,
- or keep only if helpful in debug mode.

Preferred:
- remove or use `##### Candlestick Chart` with minimal margin.

### 5. Reduce chart internal title duplication

If the Plotly chart title repeats:

```text
sample_id=... | timestamp=... | candidate_type=...
```

make it optional or compact.

Preferred:
- remove long chart title from plot area.
- keep timestamp/sample metadata in hover/debug.
- optionally show tiny annotation only near sample marker.

The chart should not have both:
- external sample metadata line,
- internal long chart title,
- sample marker label.

### 6. Preserve useful information access

Detailed metadata must still be available somewhere:
- sample_id
- timestamp
- candidate_type
- confidence
- priority
- reason_codes
- current global sample number
- rejected status if applicable

Recommended placement:
- sidebar small caption:
  ```text
  sample_id=... | global_index=...
  ```
- existing debug expander:
  ```text
  Sample Details / Chart Debug Info
  ```

### 7. Rejected banner behavior

The rejected banner:

```text
This sample is rejected/excluded.
```

is useful but currently large. Keep it, but optionally compact it:
- use warning/info box only when current sample is rejected.
- avoid occupying too much vertical space.

Do not remove rejected warning entirely.

### 8. Preserve all workflows

Do not change:
- chart data
- sample marker
- Save / Save and Next
- Previous / Next
- Go to Sample
- Reject Sample
- CSV/JSONL persistence
- review labels
- candidate audit/report logic

This is mostly a display/layout cleanup.

## Tests Required

Update `cajas/tests/test_eurusd_pattern_review_gui.py`.

Suggested tests:
1. Main app no longer renders large `Sample {sample_id}` heading.
2. Long metadata line is moved to debug/sample details expander or not rendered as prominent markdown.
3. `EURUSD 15m Review` compact title remains.
4. `Candlestick Chart` heading is removed or reduced.
5. App source still includes sample metadata in debug/sidebar.
6. Plotly chart title is not the long full sample metadata string by default.
7. Existing save/navigation/reject/chart tests still pass.

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
1. Main page no longer shows big `Sample eurusd...` heading.
2. Main page no longer shows long metadata line by default.
3. `Candlestick Chart` heading is gone or much smaller.
4. Chart starts higher.
5. Details are still available in sidebar/debug expander.
6. Rejected sample warning still appears when relevant.
7. Save / Save and Next works.
8. Reject Sample works.
9. Go to Sample works.
10. Toast still works.

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py cajas/tests/test_eurusd_pattern_review_gui.py tasks/038_remove_redundant_eurusd_review_header_text.md
git commit -m "style: remove redundant EURUSD review header text"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Removed/compacted header text
- Where sample details are now available
- Chart title behavior
- Rejected warning behavior
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
