# 008 — Fix EURUSD GUI Missing default_review_values Import Regression

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Recent commit:
- `4ee059de`
- Compact EURUSD GUI layout:
  - merged diagnostics into one line
  - moved Save / Save and Next / Previous Sample / Next Sample into one row
  - removed visible Reset Form

User now reports GUI startup/runtime error:

```text
NameError: name 'default_review_values' is not defined

Traceback:
File ".../cajas/apps/eurusd_pattern_review_app.py", line 482, in <module>
    main()
File ".../cajas/apps/eurusd_pattern_review_app.py", line 187, in main
    state_defaults = default_review_values()
                     ^^^^^^^^^^^^^^^^^^^^^
```

Interpretation:
- `cajas/apps/eurusd_pattern_review_app.py` calls `default_review_values()`.
- The function is not in the app module scope.
- Likely missing import from `cajas.research.eurusd_pattern_review_gui`.
- It may also indicate the helper was renamed, removed, or not exported consistently.

Hard boundaries:
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.
- No SQLite.
- No trading signals/orders.
- No model training.
- No Qlib core changes.

## Objective

Fix the GUI runtime `NameError` and add regression coverage so missing helper imports are caught before browser runtime.

## Required Work

### 1. Locate the helper

Search:

```bash
grep -R "def default_review_values" -n cajas
grep -R "default_review_values" -n cajas
```

Expected:
- The helper should live in `cajas/research/eurusd_pattern_review_gui.py`.

If it exists:
- Import it explicitly in `cajas/apps/eurusd_pattern_review_app.py`.

If it does not exist:
- Restore it in `cajas/research/eurusd_pattern_review_gui.py`.
- It should return the default visible review field values used by the GUI.

### 2. Fix app imports

In `cajas/apps/eurusd_pattern_review_app.py`, ensure all directly called helper functions are imported.

Check for other missing helper risks introduced by recent layout changes.

Run:

```bash
python - <<'PY'
import ast
from pathlib import Path

path = Path("cajas/apps/eurusd_pattern_review_app.py")
tree = ast.parse(path.read_text())
print("parsed ok")
PY
```

Also search likely app helper calls:
- `default_review_values`
- `format_compact_save_message`
- `format_compact_chart_diagnostics`
- navigation helpers
- gap helpers

### 3. Add import regression test

Update `cajas/tests/test_eurusd_pattern_review_gui.py` or app-specific test to catch this.

At minimum:

```python
def test_eurusd_review_app_imports_without_missing_helpers():
    import importlib
    module = importlib.import_module("cajas.apps.eurusd_pattern_review_app")
    assert hasattr(module, "main")
```

If importing the Streamlit app has side effects, use source/static check:

```python
source = Path("cajas/apps/eurusd_pattern_review_app.py").read_text()
assert "default_review_values" in source
# and ensure it is imported from the research module
```

Better:
- Add a test that compiles and imports helper module and checks `default_review_values` callable.
- Add a static test that verifies the app import list includes `default_review_values` when app source calls it.

### 4. Preserve current UI behavior

Do not revert:
- compact diagnostic line
- one-row action buttons
- hidden Reset Form
- compact save toast/details behavior
- compressed market-closed gap chart behavior
- CSV/JSONL persistence behavior

### 5. Optional manual smoke

After fix, run:

```bash
./scripts/run_eurusd_review_gui.sh
```

Confirm the app launches without the `default_review_values` NameError.

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

Manual check:
1. App launches without `NameError`.
2. Chart renders.
3. Compact diagnostics line renders.
4. Buttons render in one row:
   - Save
   - Save and Next
   - Previous Sample
   - Next Sample
5. Save works.
6. Save and Next works.
7. Previous/Next works.
8. Last Save Details remains available.
9. Gap compression remains available for market-closed gaps.

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py cajas/tests/test_eurusd_pattern_review_gui.py tasks/prompts/008_fix_eurusd_gui_default_review_values_import.md
git commit -m "fix: restore EURUSD GUI default review helper import"
```

Only add files that changed.

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Exact root cause
- Fix applied
- App launch status
- Compact diagnostics status
- Button row status
- Save behavior status
- Save and Next behavior status
- Previous/Next navigation status
- Chart gap compression status
- Validation command results
- Manual GUI smoke result if run
- `git status --short`
- Push status: not pushed
- Manual push command:

```bash
git push origin main
```
