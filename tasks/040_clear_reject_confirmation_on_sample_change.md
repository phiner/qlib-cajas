# 040 — Clear EURUSD Reject Confirmation Checkbox After Reject/Navigate

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current GUI state:
- Rejected-sample workflow exists.
- The UI has a checkbox:
  ```text
  Confirm reject current sample
  ```
- User reports that once this checkbox is selected, it does not automatically clear.
- This is unsafe/annoying because the next sample may still have reject confirmation checked.

User request:
- After reject action or navigation, the confirm checkbox should reset/clear automatically.

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

Make `Confirm reject current sample` a per-sample, one-action confirmation that automatically clears after:
1. successful Reject Sample action,
2. navigation to another sample,
3. Go to Sample jump,
4. Save and Next navigation,
5. Previous / Next navigation.

It should not remain checked across samples.

## Required Behavior

### 1. Clear after successful reject

When user:
- selects reject reason,
- checks `Confirm reject current sample`,
- clicks `Reject Sample`,
- reject writes CSV/JSONL successfully,

then:
- clear `Confirm reject current sample`
- clear or reset `Reject Notes` if appropriate
- optionally keep `Reject Reason` default
- navigate to next non-rejected sample as current behavior dictates

### 2. Clear when sample changes

Whenever current sample changes, clear reject confirmation.

Sample changes include:
- Previous Sample
- Next Sample
- Save and Next
- Go to Sample
- pending global index navigation
- rejected skip navigation

Implementation should track last rendered sample id:

```python
if st.session_state.get("reject_form_sample_id") != current_sample_id:
    st.session_state["confirm_reject_current_sample"] = False
    st.session_state["reject_form_sample_id"] = current_sample_id
```

Use actual current key names from app.

### 3. Avoid Streamlit post-instantiation mutation errors

Do not mutate widget-bound checkbox key after widget creation in the same run.

Apply sample-change reset before rendering the checkbox.

Use safe key pattern:
- canonical/sample tracking key
- widget key for checkbox
- apply reset before checkbox is instantiated

Avoid errors like:
```text
st.session_state.<key> cannot be modified after widget with key <key> is instantiated
```

### 4. Clear after action without breaking rerun

If successful reject calls rerun or stages navigation:
- set a pending reset flag before rerun,
- apply it before widget creation on next run.

Example:
```python
st.session_state["pending_clear_reject_confirm"] = True
```

Then early in render:
```python
if st.session_state.pop("pending_clear_reject_confirm", False):
    st.session_state["confirm_reject_current_sample"] = False
```

### 5. Keep rejection safety

`Reject Sample` button should remain disabled unless confirmation is checked.

After clearing:
- next sample should not have reject enabled accidentally.
- user must intentionally check again.

### 6. Preserve other workflows

Do not change:
- rejected CSV/JSONL schema
- rejection reason options
- rejected toast/status behavior
- save/save-and-next
- previous/next
- go-to-sample
- chart
- review labels
- completed progress reports
- candidate audits

## Tests Required

Update `cajas/tests/test_eurusd_pattern_review_gui.py`.

Suggested tests:
1. Source contains sample-id tracking for reject form reset.
2. Source clears reject confirmation on sample change before widget creation.
3. Source has pending clear flag or equivalent for post-reject reset.
4. Reject confirmation key is not reused unsafely after widget creation.
5. Existing reject workflow tests still pass.
6. Save/navigation tests still pass.

If pure helpers exist or can be added:
```python
def should_clear_reject_confirmation(previous_sample_id, current_sample_id) -> bool:
    ...
```

Test:
- same sample -> false
- different sample -> true
- missing previous -> true/initialize

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
1. Check `Confirm reject current sample`.
2. Click Next Sample.
3. Confirm checkbox is cleared.
4. Check it again and reject a sample.
5. Confirm next sample has checkbox cleared.
6. Use Go to Sample.
7. Confirm checkbox is cleared after jump.
8. Use Save and Next.
9. Confirm checkbox is cleared on next sample.
10. Confirm no Streamlit session-state mutation warning appears.
11. Confirm Reject Sample still requires explicit confirmation.

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas/apps/eurusd_pattern_review_app.py cajas/tests/test_eurusd_pattern_review_gui.py tasks/040_clear_reject_confirmation_on_sample_change.md
git commit -m "fix: clear EURUSD reject confirmation on sample change"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Reject confirmation reset behavior
- Sample-change reset behavior
- Post-reject reset behavior
- Streamlit state safety
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
