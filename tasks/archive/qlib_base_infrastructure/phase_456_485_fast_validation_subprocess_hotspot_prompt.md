# Phase 456–485 Prompt: Fast Validation Subprocess Hotspot Elimination

You are working on branch:

- `phase-next-mega-logic`

## Current state

Phase 426–455 completed successfully.

Important outcomes:

- Prior mixed work was separated and committed.
- Working tree was clean at the end of Phase 426.
- Data-source audit false positives were improved.
- All remaining real-data-risk CSV readers were guarded.
- `reads_full_csv_likely_count` improved from `9` to `3`.
- Zero high-risk data-source audit candidates remain.
- Fast validation is green but still too slow.

Latest metrics:

```text
run_fast_validation.py --tier fast:
  before Phase 426: 117.30s
  after Phase 426: 120.65s

reads_full_csv_likely_count:
  before Phase 426: 9
  after Phase 426: 3

high-risk candidates:
  0
```

Known top slow fast-tier tests:

```text
test_validation_runners.py::test_fail_on_budget_returns_nonzero       ~7.95s
test_validation_runners.py::test_fast_validation_writes_timing_json    ~7.78s
test_baseline_runner.py::test_artifact_writing                         ~4.28s
```

Interpretation:

- CSV high-risk I/O is mostly closed.
- Fast validation bottleneck is now test architecture, especially subprocess-heavy validation runner tests.
- Phase 456–485 should focus narrowly on eliminating subprocess-heavy tests from the fast tier or converting them to pure/injected tests.

## Phase objective

Implement **Fast Validation Subprocess Hotspot Elimination**.

Primary goals:

1. Refactor `run_fast_validation.py` and related tests so budget/timing behavior can be tested without spawning real subprocess commands.
2. Convert top slow tests into pure function / injected runner tests.
3. Move any true end-to-end CLI subprocess test to `integration` if it remains expensive.
4. Reduce fast validation runtime materially from ~120s.
5. Keep `run_fast_validation.py --tier fast` green.
6. Preserve CSV/data guardrails and research-only boundaries.

Target outcome:

- `run_fast_validation.py --tier fast` ideally under 90s.
- If under 90s is not reached, produce exact remaining top slow tests and next actions.
- No smoke/slow/integration/closure/full tests should run in fast tier.

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

# Part A — Baseline timing evidence

Start with:

```bash
git status --short
```

Then run one targeted duration report:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests \
  -m "not smoke and not slow and not closure and not full and not integration" \
  --durations=30 -q
```

Do not repeatedly run the full suite while coding. Use targeted tests after this.

Update:

- `cajas/docs/test_runtime_optimization_notes.md`

with the current top slow tests and plan.

---

# Part B — Refactor run_fast_validation for injected execution

Update:

- `cajas/scripts/run_fast_validation.py`

Goal: make most behavior testable without invoking real subprocesses.

Introduce small pure/testable components if not already present:

```python
@dataclass
class ValidationStep:
    name: str
    command: list[str]
    enabled: bool = True

@dataclass
class ValidationStepResult:
    name: str
    command: list[str]
    returncode: int
    elapsed_seconds: float
    stdout: str = ""
    stderr: str = ""

def build_validation_plan(args) -> list[ValidationStep]:
    ...

def run_validation_step(step, runner=subprocess.run, timer=time.perf_counter) -> ValidationStepResult:
    ...

def evaluate_budget(results, max_seconds, fail_on_budget) -> tuple[bool, list[str]]:
    ...

def write_timing_json(path, results, total_seconds, budget_info) -> None:
    ...
```

The exact API can differ, but tests must be able to:

- inject a fake runner
- inject deterministic timing
- verify budget failure behavior
- verify timing JSON content
- verify command plan
- verify marker expression
- verify that smoke/slow/integration are excluded

CLI behavior must remain backward compatible.

---

# Part C — Optimize test_validation_runners.py

Update:

- `cajas/tests/test_validation_runners.py`

Known slow tests:

```text
test_fail_on_budget_returns_nonzero
test_fast_validation_writes_timing_json
```

Refactor them so they do not spawn a real `run_fast_validation.py` subprocess.

They should call pure functions or an injected fake runner.

Test coverage should still verify:

- `--fail-on-budget` returns nonzero semantics
- budget warning when exceeded
- timing JSON writing
- command plan contains expected steps
- fast tier excludes:
  - smoke
  - slow
  - closure
  - full
  - integration
- skip/only flags work if present:
  - `--skip-pytest`
  - `--only-pytest`
  - `--only-hygiene`
  - `--tier quick`
  - `--tier fast`

If one true subprocess CLI smoke test is still desired, mark it:

```python
pytestmark = [pytest.mark.integration]
```

or mark only that function as integration.

---

# Part D — Optimize test_baseline_runner.py::test_artifact_writing

Inspect:

- `cajas/tests/test_baseline_runner.py`
- specifically `test_artifact_writing`

If the test runs model/training logic or writes many artifacts:

Refactor to:

- tiny fixture
- monkeypatch expensive model/trainer call
- direct artifact writer test
- assert schema and file presence only
- avoid full baseline run in fast tier

If end-to-end baseline artifact writing is still needed:

- split into a fast unit artifact-writer test
- mark the full end-to-end test as `integration`

Do not remove coverage.

---

# Part E — Add runtime guard tests

Add or update tests to prevent regression:

- Fast-tier tests should not call real `subprocess.run` for validation runners.
- Marker policy catches unmarked heavy subprocess tests.
- Runtime audit identifies subprocess-heavy fast tests.
- `run_fast_validation.py --tier fast` command plan excludes integration/slow/smoke/closure/full.

Update:

- `cajas/reports/validation_runtime_audit.py`
- `cajas/tests/test_validation_runtime_audit.py`
- `cajas/tests/test_validation_marker_policy.py`

if needed.

---

# Part F — Keep data-source audit stable

Do not reopen broad CSV work unless necessary.

Run after changes:

```bash
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py \
  --project-root cajas \
  --data-root /home/phiner/projects/research/data \
  --out-json tmp/data-io-audit/data_source_audit_phase456_after.json \
  --out-md tmp/data-io-audit/data_source_audit_phase456_after.md
```

Expected:

- no new high-risk candidates
- `reads_full_csv_likely_count` should not regress materially from 3

---

# Part G — Validation commands

Use targeted checks first:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_runners.py -q
./.venv-qlib313/bin/python -m pytest cajas/tests/test_baseline_runner.py -q
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_runtime_audit.py cajas/tests/test_validation_marker_policy.py -q
```

Then run bounded final validation:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_phase456_after.json --out-md tmp/data-io-audit/data_source_audit_phase456_after.md
./.venv-qlib313/bin/python cajas/scripts/audit_validation_runtime.py --tests-root cajas/tests --out-json tmp/validation-runtime-audit/validation_runtime_phase456.json --out-md tmp/validation-runtime-audit/validation_runtime_phase456.md
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration" --durations=30 -q
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/validation-runtime-audit/fast_validation_phase456.json
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
```

If a command exceeds a few minutes, stop and report the bottleneck.

---

# Part H — Documentation

Update:

- `cajas/docs/test_runtime_optimization_notes.md`
- `cajas/docs/data_io_optimization_notes.md` only if data-source audit changes
- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`
- `tasks/phase_456_485_fast_validation_subprocess_hotspot_prompt.md`

Document:

- old slow tests and old runtime
- refactor strategy
- new fast validation runtime
- remaining top slow tests
- how to run integration tests explicitly
- why subprocess-heavy tests should not live in fast tier

---

# Commit guidance

Suggested commits:

```bash
git commit -m "test: refactor fast validation runner tests to injected execution"
git commit -m "test: optimize baseline artifact writing test"
git commit -m "docs: document fast validation subprocess hotspot closure"
```

Report:

- changed files
- validation results
- fast pytest runtime before/after
- run_fast_validation runtime before/after
- remaining top slow tests
- data-source audit stability
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
- Files changed
- Validation
- Runtime before/after
- Remaining risks
- Git commits
- Final status

Do not push from Codex unless explicitly instructed.

---

## Completion notes

Implemented in this phase:

- Refactored `cajas/scripts/run_fast_validation.py` for injected execution and deterministic timing tests.
- Converted the two known slow validation-runner tests away from real nested subprocess execution.
- Split baseline disabled artifact writing into a direct writer helper and narrowed the fast artifact-writing test.
- Added runtime audit / marker policy guard coverage for validation-runner subprocess regressions.

Baseline evidence:

- Fast pytest subset before changes: `302 passed, 15 deselected in 111.43s`.
- Top slow tests before changes:
  - `8.24s` `test_fail_on_budget_returns_nonzero`
  - `8.24s` `test_fast_validation_writes_timing_json`
  - `4.01s` `test_validate_qlib_handler_input_cli.py::test_cli_outputs_validation_report`
  - `2.93s` `test_baseline_runner.py::test_artifact_writing`

Policy:

- Keep subprocess-heavy CLI coverage out of the fast tier unless it is converted to injected execution.
- Mark any remaining true end-to-end CLI subprocess smoke as `integration` and run it explicitly.

Final validation evidence:

- Fast pytest subset after changes: `306 passed, 15 deselected in 100.43s`.
- `run_fast_validation.py --tier fast`: passed with timing JSON total `100.57s`.
- Micro smoke: passed in `11.03s`.
- Data-source audit: `reads_full_csv_likely_count=2`; no phase regression from the prior `3` baseline.

Remaining runtime risk:

- The under-90s target was not reached.
- Remaining slow tests are mostly CLI artifact/report tests around 2-4 seconds each.
