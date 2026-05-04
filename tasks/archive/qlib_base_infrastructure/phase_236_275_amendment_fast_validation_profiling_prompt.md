# Phase 236–275 Amendment: Fast Validation Profiling + Sub-60s Daily Path

You are continuing Phase 236–275 on branch:

- `phase-next-mega-logic`

## Current observed problem

Even after splitting slow/smoke/integration markers, fast validation remains slow:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py
```

Observed runtime:

```text
elapsed: 151.73s
total_runtime: 154.97s
```

This means the next step must be profiling-first.

Do not keep blindly marking tests without knowing which step is slow.

## Objective

Make daily validation practical by identifying and optimizing the expensive step(s).

Target:

- Create clear per-step runtime reporting.
- Identify whether time is spent in:
  - compileall
  - path hygiene
  - init.py checks
  - git ls-files check
  - fast pytest subset
  - test collection
  - import overhead
  - slow unmarked tests
- Add a quicker daily mode if full compileall + pytest is inherently too slow.

## Required behavior

`run_fast_validation.py` should print a concise timing table like:

```text
step                                      status   seconds
compileall                               pass     12.3
path_hygiene                             pass     0.4
init_py_find                             pass     0.1
git_init_py_check                        pass     0.1
pytest_fast                              pass     95.8
total                                    pass     108.7
```

It should also write JSON if requested:

```bash
--timing-json tmp/validation-runtime-audit/fast_validation_timing.json
```

## Part A — Add profiling modes to run_fast_validation.py

Update:

- `cajas/scripts/run_fast_validation.py`

Add flags:

```bash
--skip-compileall
--skip-pytest
--only-pytest
--only-hygiene
--durations 30
--max-seconds 120
--fail-on-budget
--timing-json PATH
--pytest-expression 'not smoke and not slow and not closure and not full and not integration'
```

Default pytest expression should remain:

```text
not smoke and not slow and not closure and not full and not integration
```

The script must:

- print per-step elapsed time
- print total runtime
- warn if exceeding budget
- fail only if `--fail-on-budget` is set
- never run smoke/closure/full by default

## Part B — Run diagnostic commands

Run these and record results in docs/report:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --skip-pytest --timing-json tmp/validation-runtime-audit/fast_no_pytest_timing.json

./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --only-pytest --durations 50 --timing-json tmp/validation-runtime-audit/fast_pytest_only_timing.json

./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration" --collect-only -q

./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration" --durations=50
```

If the full fast pytest subset is still too slow, run targeted chunks:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration" --durations=50 -x
```

and identify the exact slow files.

## Part C — Add ultra-fast validation tier

If daily fast validation remains around 2–3 minutes even after reasonable fixes, add a lower tier:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier quick
```

Suggested tiers:

## quick

- path hygiene
- no `init.py`
- git init.py check
- import/compile selected changed-light modules if available
- marker policy tests
- runtime audit static tests
- no full pytest sweep

## fast

- compileall
- path hygiene
- no init.py
- fast pytest subset excluding smoke/slow/closure/full/integration

## full-pytest

- all pytest, including marked tests

Default should remain `fast`, unless runtime remains impractical. In docs, recommend:

- `quick` for tight edit loops
- `fast` before commit
- `micro smoke` before handoff
- `closure/full` only explicit

## Part D — Optimize compileall if it is expensive

If compileall is a major cost:

- Add `--skip-compileall` option, already required above.
- Consider compiling only `cajas` changed modules is optional and only if easy.
- Do not remove compileall from `fast` default unless docs clearly move it to a different tier.
- `quick` may skip compileall or use targeted compile checks.

## Part E — Optimize fast pytest if it is expensive

If fast pytest is the bottleneck:

- Use duration report to identify slow files.
- Mark additional non-smoke expensive tests as `slow` or `integration`.
- Convert expensive tests to fixture/unit tests where feasible.
- Avoid subprocess CLI tests in fast subset unless they are very cheap.
- Use monkeypatch for CLI subprocess tests.
- Ensure tests that do training, data export, model bridge, or artifact bundle construction are not in the daily fast subset unless proven cheap.

## Part F — Update runtime audit

Update:

- `cajas/reports/validation_runtime_audit.py`
- `cajas/scripts/audit_validation_runtime.py`

Add:

- fast subset test count
- excluded marker count
- suspicious unmarked file list
- optional timing JSON ingestion from `run_fast_validation.py`
- recommendation field:
  - keep_fast
  - mark_integration
  - mark_slow
  - convert_to_unit
  - move_to_smoke_tier

## Part G — Documentation

Update:

- `cajas/docs/test_runtime_optimization_notes.md`
- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`
- `tasks/phase_236_275_validation_runtime_audit_optimization_prompt.md`

Document:

- current measured runtime
- per-step timing
- recommended daily commands

Recommended commands should become:

```bash
# Tight edit loop
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier quick

# Before commit
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast

# Tiny smoke
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
```

## Part H — Tests

Add or update tests:

- `run_fast_validation.py` supports timing JSON
- `run_fast_validation.py --only-pytest` only runs pytest step
- `run_fast_validation.py --skip-pytest` does not run pytest
- `run_fast_validation.py --tier quick` excludes full pytest
- budget warning works
- `--fail-on-budget` fails when budget exceeded
- runtime audit can ingest timing JSON
- docs mention quick/fast/micro smoke tiers

Use monkeypatch/subprocess mocking. Do not run expensive validation inside tests.

## Validation commands

Run:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration"
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier quick --timing-json tmp/validation-runtime-audit/quick_validation_timing.json
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/validation-runtime-audit/fast_validation_timing.json
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
```

If `--tier` has not existed before this task, implement it.

Optional diagnostics:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --skip-pytest --timing-json tmp/validation-runtime-audit/fast_no_pytest_timing.json
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --only-pytest --durations 50 --timing-json tmp/validation-runtime-audit/fast_pytest_only_timing.json
```

## Commit guidance

Suggested commit:

```bash
git commit -m "test: profile and tier fast validation runtime"
```

or split if large:

1. `test: add fast validation profiling options`
2. `test: add quick validation tier`
3. `docs: document validation timing workflow`

## Final response expected from Codex

Report:

- per-step runtime table
- fast pytest duration summary
- quick tier runtime
- fast tier runtime
- remaining slow files
- changed files
- validation results
- commit hashes
- final `git status --short`
