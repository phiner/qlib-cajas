# Phase 236–275 Amendment: Include Non-Smoke Slow Tests in Fast Validation Optimization

You are continuing Phase 236–275 on branch:

- `phase-next-mega-logic`

## New observation

The fast pytest subset is still too slow:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full"
```

was still running after 7+ minutes and was around:

```text
[38%] cajas/tests/test_future_training_skeleton.py
```

This means the runtime problem is not limited to `test_run_*_smoke.py`.

Some non-smoke tests are also expensive and currently unmarked, possibly because they:

- run training skeletons
- execute model/experiment paths
- generate datasets repeatedly
- run subprocess CLIs
- run large fixture workflows
- perform repeated compile/import/discovery work
- invoke future training or placeholder pipeline logic

## Objective

Expand the runtime optimization from “smoke tests only” to **all slow tests**.

The fast subset must exclude any runtime-heavy tests, whether or not they are named smoke.

## Required actions

### 1. Stop treating naming as the only signal

Do not only mark `test_run_*_smoke.py`.

Audit all tests for runtime cost, especially:

- `cajas/tests/test_future_training_skeleton.py`
- any `training`
- any `baseline`
- any `model`
- any `experiment`
- any `dataset export`
- any `registry`
- any CLI subprocess tests
- any tests that build full artifacts under temp dirs
- any tests that call runners directly

### 2. Add dynamic duration audit for fast subset

Run:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full" --durations=50
```

If it runs too long, run targeted:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_future_training_skeleton.py --durations=30
```

Then classify expensive tests.

### 3. Mark runtime-heavy non-smoke tests

If `test_future_training_skeleton.py` is heavy, mark it:

```python
import pytest

pytestmark = [pytest.mark.slow, pytest.mark.integration]
```

or mark only heavy functions.

Use `slow` for runtime-heavy tests.

Use `integration` for medium-cost tests that exercise cross-module workflows.

Use `smoke` only for end-to-end smoke runners.

Do not mark pure unit tests as slow.

### 4. Convert heavy tests to lightweight unit tests where practical

For `test_future_training_skeleton.py` and similar files:

Prefer:

- tiny static fixtures
- monkeypatched training calls
- direct validation of schema/config/command construction
- no real training loop
- no full dataset generation
- no repeated CLI subprocess if direct function testing is enough

Keep at least one explicit heavy/integration test available, but mark it `slow` or `integration`.

### 5. Tighten fast validation marker expression

Update `run_fast_validation.py` to exclude integration too, unless integration remains proven fast:

```bash
python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration"
```

If some integration tests are fast and should be included, define a separate marker policy. The default daily command should be fast.

### 6. Add runtime budget guard

Add an optional budget flag to `run_fast_validation.py`:

```bash
--max-seconds 120
```

Behavior:

- Print warning if exceeded.
- Do not necessarily fail by default unless `--fail-on-budget` is passed.
- This keeps runtime regressions visible.

### 7. Update runtime audit

`audit_validation_runtime.py` should report:

- unmarked tests with suspicious names:
  - train
  - training
  - model
  - baseline
  - experiment
  - dataset
  - export
  - smoke
  - runner
  - subprocess
- unmarked tests that import subprocess
- unmarked tests that call `main(...)` for CLI scripts
- unmarked tests that call smoke/training runners
- recommended marker

### 8. Update marker policy tests

`test_validation_marker_policy.py` should include checks for suspicious unmarked slow candidates.

At minimum, ensure `test_future_training_skeleton.py` is no longer included in fast default if it is expensive.

### 9. Update docs

Update:

- `cajas/docs/test_runtime_optimization_notes.md`
- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`

Document that daily fast validation excludes:

- smoke
- slow
- closure
- full
- integration, unless explicitly included

Recommended daily command:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py
```

Explicit integration command:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests -m "integration and not slow and not smoke"
```

Explicit slow command:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests -m "slow"
```

## Validation commands

Run:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration"
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/audit_validation_runtime.py --tests-root cajas/tests --out-json tmp/validation-runtime-audit/validation_runtime_audit.json --out-md tmp/validation-runtime-audit/validation_runtime_audit.md
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
```

Optional targeted checks:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_future_training_skeleton.py --durations=30
./.venv-qlib313/bin/python -m pytest cajas/tests -m "integration and not slow and not smoke" --durations=30
```

## Commit guidance

This amendment can be included in the existing Phase 236–275 commits, or use an additional commit:

```bash
git commit -m "test: exclude non-smoke slow tests from fast validation"
```

## Final response expected from Codex

Report:

- Which non-smoke tests were slow.
- Which were marked `slow` / `integration`.
- Fast validation command used.
- Fast validation runtime.
- Whether `test_future_training_skeleton.py` is excluded from daily fast validation.
- Remaining slow candidates.
