# Phase 486–515 Prompt: Commit Recovery + Fast Validation Under-90s Final Push

You are working on branch:

- `phase-next-mega-logic`

## Current state

Phase 456–485 completed implementation and validation, but local commits were not created because the approval service returned `503 Service Unavailable`.

Latest Phase 456–485 summary:

- `run_fast_validation.py` was refactored to expose injectable validation plan/result execution, deterministic timing, budget evaluation, and timing JSON writing.
- Slow validation runner tests were converted away from nested real subprocess execution.
- Baseline disabled artifact writing was split into `write_baseline_disabled_artifacts()`.
- Runtime-audit and marker-policy guards were added to prevent unmarked validation-runner subprocess tests from returning to fast tier.
- Docs and prompt were updated.

Latest validation:

```text
PASS: pytest cajas/tests/test_validation_runners.py -q -> 8 passed in 0.07s
PASS: pytest cajas/tests/test_baseline_runner.py -q -> 2 passed in 5.12s
PASS: runtime audit + marker policy tests -> 10 passed in 5.12s
PASS: compileall cajas
PASS: check_path_hygiene.py
PASS: find cajas -path "*/init.py" -print -> no output
PASS: git diff --check
PASS: data-source audit, reads_full_csv_likely_count=2
PASS: fast pytest subset -> 306 passed, 15 deselected in 100.43s
PASS: run_fast_validation.py --tier fast -> total 100.57s
PASS: micro smoke -> 11.03s
```

Runtime before/after:

```text
Fast pytest subset: 111.43s -> 100.43s
run_fast_validation.py --tier fast: 120.65s -> 100.57s
Target under 90s: not reached
```

Remaining slow tests:

- mostly CLI artifact/report tests around 2–4s each
- leading known slow test:
  - `test_validate_qlib_handler_input_cli` around `3.94s`

Current git state from Phase 456 report:

- local commits were not created
- staged group: fast validation runner/test/audit changes
- unstaged group: baseline/docs changes
- untracked: phase prompt
- push not run

## Phase objective

Implement **Commit Recovery + Fast Validation Under-90s Final Push**.

Primary goals:

1. Recover and commit Phase 456–485 changes in clean groups.
2. Preserve all validated behavior.
3. Identify the remaining slow fast-tier CLI/report tests.
4. Convert or mark expensive CLI artifact/report tests so fast validation drops below 90s if feasible.
5. Keep fast validation and micro smoke passing.
6. Keep data-source audit stable or improved.
7. Preserve all research-only/no-execution boundaries.

## Non-negotiable boundaries

Do not:

- Modify Qlib core.
- Add broker adapters.
- Add live trading.
- Add paper trading execution.
- Add order generation.
- Add order routing.
- Add position sizing.
- Add portfolio optimization.
- Add PnL optimization.
- Add execution simulation.
- Add network calls.
- Add GPU/CUDA requirements.
- Add files named `init.py`; continue using `__init__.py`.

All validation remains:

- CPU-only
- local
- deterministic where feasible
- no network
- no broker/live/paper execution

---

# Part A — Commit recovery first

Start with:

```bash
git status --short
git diff --cached --name-only
git diff --name-only
```

Do not revert valid work from Phase 456.

Commit in the intended groups.

## A1. Fast validation runner/test/audit changes

Likely files:

- `cajas/scripts/run_fast_validation.py`
- `cajas/tests/test_validation_runners.py`
- `cajas/reports/validation_runtime_audit.py`
- `cajas/tests/test_validation_runtime_audit.py`
- `cajas/tests/test_validation_marker_policy.py`

Run targeted tests if needed:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_runners.py cajas/tests/test_validation_runtime_audit.py cajas/tests/test_validation_marker_policy.py -q
```

Then commit:

```bash
git add cajas/scripts/run_fast_validation.py \
        cajas/tests/test_validation_runners.py \
        cajas/reports/validation_runtime_audit.py \
        cajas/tests/test_validation_runtime_audit.py \
        cajas/tests/test_validation_marker_policy.py

git commit -m "test: refactor fast validation runner tests to injected execution"
```

## A2. Baseline artifact writing changes

Likely files:

- `cajas/scripts/run_baseline_disabled.py`
- `cajas/tests/test_baseline_runner.py`

Run:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_baseline_runner.py -q
```

Then commit:

```bash
git add cajas/scripts/run_baseline_disabled.py cajas/tests/test_baseline_runner.py
git commit -m "test: optimize baseline artifact writing test"
```

## A3. Docs and task prompt

Likely files:

- `cajas/docs/test_runtime_optimization_notes.md`
- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`
- `tasks/phase_456_485_fast_validation_subprocess_hotspot_prompt.md`

Commit:

```bash
git add cajas/docs/test_runtime_optimization_notes.md \
        cajas/README.md \
        cajas/docs/qlib_integration_notes.md \
        tasks/phase_456_485_fast_validation_subprocess_hotspot_prompt.md

git commit -m "docs: document fast validation subprocess hotspot closure"
```

If the exact staged/unstaged files differ, adjust using `git status --short`. Only commit files you understand.

End Part A with:

```bash
git status --short
```

If unrelated files remain, report them and do not mix them into Phase 486 work.

---

# Part B — Profile remaining fast-tier slow tests

Run one duration report:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests \
  -m "not smoke and not slow and not closure and not full and not integration" \
  --durations=50 -q
```

Capture top slow tests in:

- `cajas/docs/test_runtime_optimization_notes.md`

Known candidate:

- `test_validate_qlib_handler_input_cli`

Also look for tests around:

- CLI artifact writers
- report builders
- validation scripts
- handler input validation
- dataset contract/handler smoke validators
- subprocess-based script tests
- repeated temp artifact tree construction

Do not repeatedly run the full subset while coding. Use targeted files after the first duration report.

---

# Part C — Optimize or reclassify CLI artifact/report tests

For each top slow fast-tier test, choose the safest option.

## Option 1 — Convert subprocess CLI test to direct function test

Preferred when test only verifies output schema or command logic.

Use:

- direct builder function
- tiny fixture data
- monkeypatched file writes
- temporary minimal artifacts

Keep a separate integration test only if necessary.

## Option 2 — Monkeypatch subprocess / command runner

Preferred for script-runner tests.

Test:

- command construction
- exit-code handling
- output paths
- timing JSON writing
- error handling

Do not spawn real process in fast tier.

## Option 3 — Mark as integration

Use when test is truly end-to-end CLI behavior and remains expensive.

Add:

```python
import pytest

pytestmark = [pytest.mark.integration]
```

or function-level marker.

Make sure marker policy tests accept this.

## Option 4 — Split fast/integration

Create:

- fast unit test for core logic
- integration test for end-to-end CLI

Do not remove coverage.

---

# Part D — Prioritize known slow test: validate qlib handler input CLI

Inspect:

- `cajas/tests/test_validate_qlib_handler_input_cli.py`
- related script:
  - `cajas/scripts/validate_qlib_handler_input.py`
- related report/module:
  - `cajas/reports/qlib_handler_smoke_validator.py`

If the test spawns subprocess or builds too much fixture data:

- replace with direct function test for validator logic
- use tiny static fixture
- monkeypatch CLI wrapper
- mark true CLI subprocess test as integration

Add or update tests to preserve coverage:

- valid tiny handler input passes
- missing required column fails
- large file guard behavior remains tested
- CLI argument parsing is tested without full subprocess if possible

---

# Part E — Keep data-source audit stable

Run after changes:

```bash
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py \
  --project-root cajas \
  --data-root /home/phiner/projects/research/data \
  --out-json tmp/data-io-audit/data_source_audit_phase486_after.json \
  --out-md tmp/data-io-audit/data_source_audit_phase486_after.md
```

Expected:

- no high-risk candidates
- `reads_full_csv_likely_count` should remain around 2 or improve
- no regression in policy guard detection

---

# Part F — Add regression guard for fast-tier subprocess usage

Update if needed:

- `cajas/reports/validation_runtime_audit.py`
- `cajas/tests/test_validation_runtime_audit.py`
- `cajas/tests/test_validation_marker_policy.py`

The audit/marker policy should flag:

- unmarked fast-tier tests that call `subprocess.run`
- unmarked fast-tier tests that invoke `python cajas/scripts/...`
- unmarked tests that run validation/smoke runners
- unmarked tests that build large temp artifact trees

Classification should recommend:

- monkeypatch
- direct function test
- mark integration
- mark slow

---

# Part G — Validation commands

Use targeted checks first:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_runners.py -q
./.venv-qlib313/bin/python -m pytest cajas/tests/test_baseline_runner.py -q
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validate_qlib_handler_input_cli.py -q
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_runtime_audit.py cajas/tests/test_validation_marker_policy.py -q
```

Then bounded final validation:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_phase486_after.json --out-md tmp/data-io-audit/data_source_audit_phase486_after.md
./.venv-qlib313/bin/python cajas/scripts/audit_validation_runtime.py --tests-root cajas/tests --out-json tmp/validation-runtime-audit/validation_runtime_phase486.json --out-md tmp/validation-runtime-audit/validation_runtime_phase486.md
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration" --durations=30 -q
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/validation-runtime-audit/fast_validation_phase486.json
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
```

If any command exceeds a few minutes, stop and report exact bottleneck.

---

# Part H — Documentation

Update:

- `cajas/docs/test_runtime_optimization_notes.md`
- `cajas/docs/data_io_optimization_notes.md` only if audit numbers change
- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`
- `tasks/phase_486_515_fast_validation_under90_prompt.md`

Document:

- commit recovery result
- old/new runtime
- slow tests optimized or reclassified
- remaining slow tests
- recommended fast/integration commands

Recommended commands:

```bash
# Daily
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast

# Tight loop
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier quick

# Explicit integration tests
./.venv-qlib313/bin/python -m pytest cajas/tests -m "integration and not slow and not smoke"

# Micro smoke
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
```

---

# Commit guidance

Use multiple commits.

Suggested:

```bash
git commit -m "chore: recover phase 456 validation runtime commits"
git commit -m "test: optimize qlib handler input cli fast test"
git commit -m "test: reduce remaining fast-tier cli hotspots"
git commit -m "docs: document fast validation under-90 push"
```

Final report should include:

- commit recovery result
- changed files
- validation results
- fast pytest runtime before/after
- run_fast_validation runtime before/after
- data-source audit result
- remaining top slow tests
- commit hashes
- final `git status --short`
- manual push command:

```bash
git push origin phase-next-mega-logic
```

---

# Final response expected from Codex

Return compact summary:

- Summary
- Commit recovery result
- Files changed
- Validation
- Runtime before/after
- Data-source audit
- Remaining risks
- Git commits
- Final status

Do not push from Codex unless explicitly instructed.
