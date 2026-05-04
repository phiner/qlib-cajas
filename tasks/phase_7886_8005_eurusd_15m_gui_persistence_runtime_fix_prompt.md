# Phase 7886-8005 — Fix EURUSD 15m GUI Save-and-Next Runtime Regression

## Context

We are working directly on `main` for the Qlib Base / `qlib-cajas` project.

Recent completed work:
- CSV/JSONL-only durable persistence was hardened.
- CSV is authoritative latest-state storage by `sample_id`.
- JSONL is append-friendly audit history.
- SQLite is explicitly deferred.
- No trading signals/orders/model training/Qlib core changes are allowed.

Current user-reported runtime regression:

When clicking **Save and Next** in the Streamlit EURUSD review GUI, the UI reports:

```text
Save and Next failed for sample_id=eurusd15m_000027: name 'persist_review' is not defined
```

Terminal also shows Streamlit warnings like:

```text
The widget with key "review_market_context" was created with a default value but also had its value set via the Session State API.
```

Relevant stack location:

```text
cajas/apps/eurusd_pattern_review_app.py
main()
market_context = st.selectbox(...)
```

Likely cause:
- `cajas/apps/eurusd_pattern_review_app.py` still calls an old/nonexistent helper named `persist_review`.
- The new persistence helpers in `cajas/research/eurusd_pattern_review_gui.py` likely include functions such as:
  - `default_review_values`
  - `build_review_update_row`
  - `save_or_update_completed_review`
  - JSONL append helper or equivalent
- Save and Save-and-Next button paths are not consistently using the new persistence API.
- Widget initialization still mixes Streamlit `value` / `index` defaults with direct `st.session_state[...]` assignment for the same keys in the same run.

## Objective

Fix the runtime regression so the GUI save actions work reliably again.

Primary goals:
1. `Save` works without `NameError`.
2. `Save and Next` works without `NameError`.
3. `Save and Next` saves first, then advances exactly one sample only after successful persistence.
4. CSV update remains duplicate-safe by `sample_id`.
5. JSONL appends one audit event per successful save/save-and-next.
6. Reset Form resets visible fields only and does not delete CSV/JSONL.
7. Streamlit widget/session-state warning is eliminated or minimized by using a single ownership pattern for widget defaults.
8. No SQLite is introduced.

## Required Scope

Inspect and update:

- `cajas/apps/eurusd_pattern_review_app.py`
- `cajas/research/eurusd_pattern_review_gui.py`
- `cajas/tests/test_eurusd_pattern_review_gui.py`
- `cajas/tests/test_validation_eurusd_pattern_review_gui.py` if needed
- docs/tasks only if behavior wording needs correction

## Implementation Requirements

### 1. Remove all stale `persist_review` references

Search:

```bash
grep -R "persist_review" -n cajas tests tasks docs || true
```

Any runtime path in the app must not call `persist_review` unless the function is intentionally restored as a compatibility wrapper.

Preferred fix:
- Update app button handlers to call the current canonical persistence helper(s).

Acceptable compatibility fix:
- Add a thin `persist_review(...)` wrapper in `cajas/research/eurusd_pattern_review_gui.py` only if it reduces churn and delegates to the canonical CSV/JSONL save implementation.
- If adding wrapper, document that it is compatibility-only and test it.

Do not create duplicate persistence semantics.

### 2. Centralize save action behavior

Create or confirm a single helper path equivalent to:

```python
result = save_review_action(
    batch_row=current_row,
    review_values=current_review_values,
    completed_csv_path=completed_csv_path,
    audit_jsonl_path=audit_jsonl_path,
    action="save" or "save_and_next",
    schema_version=...
)
```

The helper/result should clearly indicate:
- `ok`
- `sample_id`
- `completed_csv_path`
- `audit_jsonl_path`
- `csv_saved`
- `jsonl_appended`
- warning/error message if JSONL append failed after CSV success

The GUI should use this result for visible feedback.

### 3. Fix Save and Save-and-Next consistency

Button behavior:

#### Save
- Build review payload from current widget/session values.
- Persist CSV latest state by `sample_id`.
- Append JSONL audit event.
- Show success/warning/error status.
- Do not change current sample index.

#### Save and Next
- Build review payload from current widget/session values.
- Persist exactly like Save.
- Only if persistence result is acceptable:
  - advance current sample index by 1
  - clamp to last sample if at end
  - reload next sample form values
- If persistence fails before CSV save:
  - do not advance
- If CSV saved but JSONL append warns:
  - acceptable to advance, but visible warning must mention JSONL audit issue.

#### Reset Form
- Reset only current visible review widget values to defaults.
- Do not delete completed CSV.
- Do not delete JSONL.
- Do not advance index.

### 4. Fix Streamlit widget/session_state default warning

Use one consistent pattern.

Recommended pattern:
- Before rendering widgets, initialize missing session_state keys only when absent:

```python
if key not in st.session_state:
    st.session_state[key] = default_value
```

- When creating widgets with `key=...`, avoid also passing a conflicting `value=` or `index=` derived from a different default if Streamlit already owns that key.

For selectbox/radio widgets:
- Either:
  - compute `index` only before the key is initialized and do not mutate afterward in same run, or
  - initialize `st.session_state[key]` first and omit conflicting default when safe.
- Avoid assigning `st.session_state["review_market_context"] = ...` after creating the widget in the same run.

For reset/reload:
- Use a helper to set session keys before the next rerun.
- Call `st.rerun()` after reset or sample change if needed to ensure clean widget reconstruction.

### 5. Ensure completed row reload still works

When revisiting a sample:
- If completed CSV has a row for `sample_id`, the form should be populated from completed values.
- Otherwise default review values should be used.
- This should not trigger Streamlit default/session warning.

### 6. Preserve forbidden-column filtering

Do not allow trading/execution/action columns to be persisted, including but not limited to:
- signal
- order
- broker
- trade
- position
- execution
- action columns that imply trading execution

Preserve existing forbidden-column tests.

## Tests Required

Add/update tests to cover:

1. No stale persistence symbol:
   - Assert `persist_review` is either absent from app runtime code or is a real callable compatibility wrapper.
   - Prefer a test that imports app/helper code enough to catch NameError risk.

2. Save action helper:
   - Given one sample and review payload, CSV is created/updated by `sample_id`.
   - JSONL has exactly one appended event.

3. Save-and-next helper/app logic:
   - Persistence success permits advance.
   - Persistence hard failure prevents advance.
   - CSV success + JSONL warning reports warning status.

4. Duplicate-safe update:
   - Saving same `sample_id` twice produces one CSV row with latest values.
   - JSONL has two audit events.

5. Completed reload:
   - Completed CSV values override defaults for revisited sample.

6. Reset defaults:
   - Reset values equal `default_review_values()`.
   - Existing completed CSV is untouched.

7. Widget-state helper:
   - Unit test pure helper functions where possible.
   - Do not rely on browser/UI automation.

## Validation Commands

Run:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_eurusd_pattern_review_gui.py cajas/tests/test_validation_eurusd_pattern_review_gui.py
```

Run:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py cajas/tests/test_eurusd_pattern_review_gui.py
```

Run:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/fast_validation_latest.json
```

Run hygiene:

```bash
git diff --check
find cajas -path "*/init.py" -print
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Optional manual smoke:

```bash
./scripts/run_eurusd_review_gui.sh
```

Then manually test:
1. Open GUI.
2. Change review fields.
3. Click Save.
4. Confirm success status and completed CSV row.
5. Click Save and Next.
6. Confirm sample advances only after save.
7. Revisit previous sample.
8. Confirm completed values reload.
9. Click Reset Form.
10. Confirm visible fields reset, completed CSV/JSONL are not deleted.
11. Watch terminal for no `persist_review` NameError and no repeated Streamlit widget default/session_state warning.

## Commit Requirements

Work directly on `main`.

Create one commit with a message like:

```bash
git add cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py cajas/tests/test_eurusd_pattern_review_gui.py cajas/tests/test_validation_eurusd_pattern_review_gui.py cajas/docs/eurusd_pattern_research_kickoff.md cajas/README.md tasks/eurusd_15m_research_end_to_end_roadmap.md
git commit -m "fix: repair EURUSD GUI persistence runtime path"
```

If docs/tasks are unchanged, do not force-add them.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Exact root cause
- What was fixed
- Save behavior confirmation
- Save-and-next behavior confirmation
- Reset behavior confirmation
- CSV behavior confirmation
- JSONL behavior confirmation
- Streamlit warning status
- Validation command results
- `git status --short`
- Push status: not pushed
- Manual push command:

```bash
git push origin main
```

## Hard Boundaries

Do not:
- add SQLite
- introduce trading signals
- introduce broker/order execution
- train models
- modify Qlib core
- create/merge branches
- push automatically
- delete completed review data during reset
