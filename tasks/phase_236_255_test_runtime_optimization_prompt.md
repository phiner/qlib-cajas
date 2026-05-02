# Phase 236–255 Prompt: Test Runtime Optimization + Smoke Tier Split

You are working on branch:

- `phase-next-mega-logic`

## Current problem

The full test suite is getting too slow.

Observed example:

```bash
rtk ./.venv-qlib313/bin/python -m pytest cajas/tests
```

was still running after about 16+ minutes and was around:

```text
[85%] cajas/tests/test_run_full_research_stack_smoke.py
```

This strongly suggests that some pytest tests are running full smoke workflows repeatedly, including expensive end-to-end orchestration.

## Phase 236–255 objective

Implement **Test Runtime Optimization + Smoke Tier Split**.

The goal is to keep correctness coverage while making routine development validation fast.

Expected outcome:

1. Default pytest should be fast.
2. Heavy smoke tests should be explicitly marked and excluded from default local unit test runs.
3. Smoke flows should still be runnable via explicit commands.
4. CI validation plan should document test tiers clearly.
5. Existing safety boundaries must remain unchanged.

Target:

- Default focused/unit test command should run much faster than the current all-in heavy suite.
- Heavy smoke tests should be marked with `@pytest.mark.smoke` or equivalent.
- Runtime-heavy tests should be marked with `@pytest.mark.slow` where appropriate.
- Default `pytest cajas/tests` may still include all tests if the project prefers that, but add a clearly documented fast command such as:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not slow and not smoke"
```

and make sure it passes.

Prefer changing docs/validation commands to use tiers rather than deleting coverage.

## Non-negotiable boundaries

Do not:

- Remove important tests just to reduce runtime.
- Weaken semantic correctness tests.
- Hide failing smoke behavior.
- Modify Qlib core.
- Add broker/live/paper execution.
- Add GPU/CUDA requirements.
- Add network calls.
- Add files named `init.py`; continue using `__init__.py`.

All changes must remain:

- CPU-only.
- Bounded.
- Deterministic where feasible.
- Compatible with existing smoke CLIs.

---

# Part A — Measure and classify slow tests

Run a duration report:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests --durations=30
```

If this is too slow, use targeted duration checks for likely files:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_run_full_research_stack_smoke.py --durations=20
./.venv-qlib313/bin/python -m pytest cajas/tests/test_run_research_quality_loop_smoke.py --durations=20
./.venv-qlib313/bin/python -m pytest cajas/tests/test_run_research_remediation_smoke.py --durations=20
./.venv-qlib313/bin/python -m pytest cajas/tests/test_run_final_reproducibility_closure_smoke.py --durations=20
./.venv-qlib313/bin/python -m pytest cajas/tests/test_run_governance_review_closure_smoke.py --durations=20
```

Create a short report:

- `cajas/docs/test_runtime_optimization_notes.md`

Include:

- slowest tests
- likely reason
- whether each should be unit, integration, smoke, or slow
- optimization action taken

---

# Part B — Add pytest marker configuration

Add or update:

- `pytest.ini` or `pyproject.toml`, depending existing project style

Define markers:

```ini
markers =
    smoke: end-to-end smoke workflows that may run full pipelines
    slow: runtime-heavy tests excluded from fast local validation
    integration: medium-cost integration tests
```

If there is already a config, extend it without disrupting existing options.

---

# Part C — Mark heavy smoke tests

Mark end-to-end smoke runner tests as `smoke` and usually `slow`.

Likely candidates:

- `cajas/tests/test_run_full_research_stack_smoke.py`
- `cajas/tests/test_run_research_quality_loop_smoke.py`
- `cajas/tests/test_run_research_remediation_smoke.py`
- `cajas/tests/test_run_final_reproducibility_closure_smoke.py`
- `cajas/tests/test_run_governance_review_closure_smoke.py`
- older smoke runner tests if they run full pipeline:
  - `test_run_final_readiness_smoke.py`
  - `test_run_research_gate_smoke.py`
  - `test_run_qlib_model_bridge_smoke.py`
  - `test_run_qlib_dataset_handler_smoke.py`
  - `test_run_qlib_adapter_smoke.py`

Use:

```python
import pytest

pytestmark = [pytest.mark.smoke, pytest.mark.slow]
```

or function-level marks if only some tests are heavy.

Do not mark small pure unit tests as slow.

---

# Part D — Replace full-pipeline pytest execution with cheaper fixture-level tests where possible

For heavy smoke tests, prefer testing orchestration using:

- tiny temp directories
- monkeypatched subcommands
- fake generated artifacts
- existing builder functions directly
- minimal fixture artifacts

Where feasible:

- Do not execute the entire upstream pipeline inside a pytest test.
- Instead verify:
  - command construction
  - expected output paths
  - status parsing
  - error handling
  - generated summary structure

Keep at least one explicit smoke CLI command documented for actual full pipeline verification outside default pytest.

---

# Part E — Add fast validation script

Create:

- `cajas/scripts/run_fast_validation.py`

It should run a fast validation tier:

1. compileall
2. path hygiene
3. no `init.py`
4. pytest excluding slow/smoke tests

Suggested behavior:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py
```

Internally run:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\\.py$' || true
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not slow and not smoke"
```

The script should:

- print each command
- stop on failure
- summarize elapsed time per step
- print total runtime
- not require network/GPU

Add tests for the script using monkeypatch/subprocess mocking if the code structure allows, or keep it small and deterministic.

---

# Part F — Add explicit smoke validation script

Create:

- `cajas/scripts/run_smoke_validation.py`

It should run selected smoke commands explicitly, not through default pytest.

Default smoke command can be the latest full closure smoke:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_governance_review_closure_smoke.py --out-root tmp/governance-review-smoke
```

Support flags such as:

```bash
--tier minimal
--tier full
--out-root tmp/smoke-validation
```

Suggested tiers:

- `minimal`: latest closure smoke only
- `full`: selected historical smoke workflows if needed

Do not run all historical mega smokes by default.

---

# Part G — Update CI validation plan and docs

Update:

- `cajas/reports/ci_validation_plan.py`
- `cajas/scripts/build_ci_validation_plan.py`
- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`
- `cajas/docs/test_runtime_optimization_notes.md`
- `tasks/phase_236_255_test_runtime_optimization_prompt.md`

Document validation tiers:

## Tier 0 — Hygiene

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\\.py$' || true
```

## Tier 1 — Fast unit validation

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not slow and not smoke"
```

## Tier 2 — All pytest including slow/smoke markers

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests
```

## Tier 3 — Explicit smoke

```bash
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier minimal
```

## Tier 4 — Full historical smoke

Optional only.

---

# Part H — Tests

Add or update tests for:

- pytest marker config exists and defines `slow`/`smoke`
- heavy smoke test files are marked slow/smoke
- fast validation command excludes slow/smoke tests
- CI validation plan includes fast and smoke tiers
- smoke validation script defaults to minimal tier
- docs mention the fast command

Keep tests lightweight and deterministic.

---

# Validation commands

Run:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not slow and not smoke"
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier minimal --out-root tmp/smoke-validation-minimal
```

Optionally run, if time allows:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests --durations=30
```

Do not require full historical smoke for this phase unless explicitly necessary.

---

# Commit guidance

After validation passes, create local commits. Suggested split:

1. `test: split slow smoke tests from fast validation`
2. `feat: add fast and smoke validation runners`
3. `docs: document validation tiers and runtime optimization`

Report:

- changed files
- validation results
- fast validation runtime if available
- smoke output paths
- commit hashes
- final `git status --short`
- manual push command:

```bash
git push origin phase-next-mega-logic
```

---

# Final response expected from Codex

Return a compact summary with:

- Summary
- Files changed
- Validation
- Runtime notes
- Smoke output paths
- Git commits
- Notes / risks
- Final status

Do not push from Codex unless explicitly instructed.
