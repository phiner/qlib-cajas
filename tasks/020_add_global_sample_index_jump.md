# 020 — Add Global Sample Index Jump in EURUSD Review GUI

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current EURUSD 15m review GUI:
- Sidebar has `Sample Index` number input with +/- controls.
- Save / Save and Next / Previous / Next work.
- CSV/JSONL persistence works.
- Completed progress validation works.
- Filters exist for Candidate Type / Review Status.
- User wants the sample index to be a fixed locator, not dependent on filters.

User clarification:
- Every sample/review should have a fixed index number.
- Direct index jump should use the original global batch order.
- The index should be independent of current filters.
- Do not define Sample Index as “position in current filtered list.”

Hard boundaries:
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- CSV/JSONL only.
- No SQLite.
- Do not reset or regenerate review batch.
- Do not delete completed review data.
- Do not train models or create trading signals/orders.
- Do not modify Qlib core.

## Objective

Implement a direct global sample index jump in the EURUSD review GUI.

The user should be able to type a sample number/index and jump directly to that sample in the original batch order, regardless of current filters.

## Required Index Semantics

### 1. Global batch index

Define:

```text
global_sample_index = fixed index in the original review batch CSV order
```

This index is independent of:
- Candidate Type filter
- Review Status filter
- current filtered view
- whether the sample has been reviewed

### 2. User-facing display should be 1-based

Preferred UI label:

```text
Sample Number
```

Meaning:

```text
Sample Number 1 = batch row index 0
Sample Number 34 = batch row index 33
Sample Number 100 = batch row index 99
```

Display helper text:

```text
Global position in full review batch; ignores filters.
```

Internal conversion:

```python
global_index = sample_number - 1
```

### 3. Keep global identity visible

Sidebar should show something like:

```text
Sample 34 / 100
sample_id=eurusd15m_000026
```

If filters are active, also show:

```text
Filters are active; direct Sample Number jump uses full batch order.
```

## Required Behavior

### 1. Direct jump

When the user types a sample number:
- clamp to `[1, batch_count]`
- convert to zero-based global index
- locate that exact row in the full batch dataframe
- update current selected sample to that row
- reload completed values if available
- update chart
- do not save automatically
- do not show save toast

### 2. Filters must not redefine the index

Filters may still control list browsing or visibility if currently implemented, but direct Sample Number jump must not be relative to filtered result.

If the selected global sample does not match the current filters, choose one of these designs:

Preferred:
- Direct jump overrides/ignores filters for the selected sample display.
- Show a compact info/warning:

```text
Showing global sample 34; it may not match current filters.
```

Alternative:
- Clear filters automatically after direct jump.
- This is acceptable only if clearly documented and tested.

Do **not** silently fail to jump because of filters.

### 3. Previous / Next behavior

Define Previous / Next as global batch navigation too:

```text
Previous Sample = global index - 1
Next Sample = global index + 1
Save and Next = save current global sample, then global index + 1
```

This keeps navigation simple and consistent.

If existing filters previously changed Previous/Next behavior, update docs/UI to say filters are for browsing/status only, while sample navigation is global.

### 4. Candidate Type / Review Status filters

Clarify behavior in UI:
- Filters can still be used to inspect counts or optionally jump to matching samples if existing behavior supports it.
- But the main Sample Number input and Prev/Next use global order.

If implementing filtered browsing is too complex, keep filters as display/status controls only or leave their existing behavior but ensure global direct jump works predictably.

### 5. Optional Sample ID jump

If easy and low risk, add:

```text
Jump to Sample ID
```

Behavior:
- user enters `eurusd15m_000151`
- click `Go`
- locate by `sample_id` in full batch
- ignore filters or show warning if filters active
- no save occurs

This is optional. Prioritize global Sample Number.

### 6. Preserve one-shot toast behavior

If prompt `019` has not been implemented yet, fix it here too or ensure no regression:
- save toast appears only after Save / Save and Next
- typing Sample Number must not replay old save toast
- changing filters must not replay old save toast

### 7. Preserve persistence and chart behavior

Do not change:
- completed CSV schema
- JSONL event schema
- review batch contents
- chart framing
- gap compression
- sample marker
- validation reports

## Implementation Notes

Likely files:
- `cajas/apps/eurusd_pattern_review_app.py`
- `cajas/research/eurusd_pattern_review_gui.py`
- `cajas/tests/test_eurusd_pattern_review_gui.py`

Potential helpers:

```python
def sample_number_to_global_index(sample_number: int, batch_count: int) -> int:
    ...

def global_index_to_sample_number(global_index: int) -> int:
    ...

def clamp_global_sample_index(index: int, batch_count: int) -> int:
    ...

def resolve_global_sample_by_number(batch_df, sample_number: int):
    ...
```

Streamlit state guidance:
- Use canonical state key for global index, e.g. `current_global_sample_idx`.
- Use widget key distinct from canonical state, e.g. `sample_number_widget`.
- Use staged rerun key, e.g. `pending_global_sample_idx`.
- Do not mutate widget-bound keys after widget instantiation.

Important:
- Ensure existing `current_sample_idx` is either renamed or clearly treated as global batch index.
- Avoid “filtered index” ambiguity.

## Tests Required

Update `cajas/tests/test_eurusd_pattern_review_gui.py`.

Required tests:

### 1. Global index conversion
- Sample Number 1 -> global index 0
- Sample Number 34 -> global index 33
- Sample Number 100 -> global index 99
- below range clamps to 0
- above range clamps to last index

### 2. Direct jump ignores filters
Use a small fake batch:
- sample 3 has candidate_type not matching current filter
- direct jump to Sample Number 3 still resolves sample 3
- no failure due to filter

### 3. Previous / Next global navigation
- from global index 33, Previous -> 32
- Next -> 34
- boundaries clamp correctly

### 4. Save and Next global navigation
- save success permits global index + 1
- hard save failure does not advance
- JSONL warning after CSV success follows current semantics

### 5. No save/no toast on jump
- direct sample number jump does not call persistence helper
- direct sample number jump does not enqueue save toast

### 6. Static app regression
- app UI label says `Sample Number` or equivalent
- app helper/help text says global/full batch order and ignores filters
- app does not use old `key="sample_idx"` post-mutation pattern
- pending global sample navigation pattern exists

### 7. Existing tests still pass
- Save / Save and Next
- Previous / Next
- one-shot toast if implemented
- CSV/JSONL persistence
- chart marker/framing/gap compression

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
1. Enter Sample Number `34`.
2. Confirm GUI jumps to global batch row 34.
3. Confirm sample_id/chart/review values update.
4. Turn on Candidate Type filter.
5. Enter Sample Number `34` again or another number not matching the filter.
6. Confirm it still jumps by full batch order, or clearly shows that global sample is being displayed despite filters.
7. Click Previous Sample and Next Sample.
8. Confirm they move global order, not filtered order.
9. Click Save and Next.
10. Confirm it saves then moves to next global sample.
11. Confirm no old save toast appears from typing sample number or changing filters.
12. Confirm CSV/JSONL persistence still works.

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py cajas/tests/test_eurusd_pattern_review_gui.py tasks/prompts/020_add_global_sample_index_jump.md
git commit -m "feat: add EURUSD global sample index jump"
```

Only add changed files.

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Global Sample Number semantics
- Direct jump behavior
- Filter interaction behavior
- Previous/Next global behavior
- Save and Next global behavior
- Optional Sample ID jump behavior if added
- Toast regression status
- CSV/JSONL persistence status
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
- delete or reset completed review CSV/JSONL
- regenerate review batch
