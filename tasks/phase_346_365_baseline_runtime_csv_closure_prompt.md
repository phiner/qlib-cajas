# Phase 346–365 Prompt: Baseline Runtime Failure Fix + Remaining Full-Read CSV Closure

You are working on branch:

- `phase-next-mega-logic`

## Current state

Phase 316–345 completed.

Latest results:

- Added reusable CSV loading policy.
- Refactored high-risk CSV entrypoints to support guarded/sampled/chunked reads.
- Improved data-source audit with risk categories, remediation hints, and line/snippet evidence.
- Added full-read refactor docs and before/after metrics.

Latest data-source audit:

```text
Before:
  read_csv_count: 27
  reads_full_csv_likely_count: 25
  chunking_support_count: 7

After:
  read_csv_count: 27
  reads_full_csv_likely_count: 20
  chunking_support_count: 13

Net:
  likely full-read sites reduced by 5
  chunking/policy-capable sites increased by 6
```

Latest runtime:

```text
Fast pytest baseline before: 136.15s
Latest fast subset run: 129.34s, but ended with one failing test
run_fast_validation --tier fast:
  compileall: 0.068s
  path_hygiene: 3.090s
  init_py_find: 0.005s
  git_init_py_check: 0.015s
  total before pytest failure: 133.685s
```

Known current failure:

```text
FAIL:
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration"

1 failure:
cajas/tests/test_multi_model_baseline.py::test_runs_sklearn_models
```

`run_fast_validation.py --tier fast` fails for the same underlying test.

Known remaining risks:

- Remaining full-read candidates are mostly under:
  - `cajas/baseline/*` analysis/trainer modules
  - `cajas/audits/leakage_drift_audit.py`
  - some dataset/report utility paths
- Fast subset still includes expensive baseline tests.
- Repository may still contain unrelated pre-existing uncommitted changes from earlier phases; do not mix unrelated changes.

## Phase objective

Implement **Baseline Runtime Failure Fix + Remaining Full-Read CSV Closure**.

Primary goals:

1. Fix `test_multi_model_baseline.py::test_runs_sklearn_models`.
2. Determine whether the failure is environment, dependency, path, data fixture, or refactor regression.
3. Reduce fast subset runtime by moving expensive baseline/model tests out of the default fast tier or converting them to lightweight fixtures.
4. Continue refactoring remaining baseline/audit full-read CSV candidates toward:
   - `csv_loading_policy`
   - chunked reads
   - row limits
   - sample mode
   - cache/manifest usage
5. Get `run_fast_validation.py --tier fast` passing again.
6. Keep all research safety boundaries unchanged.

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

# Part A — Diagnose failing baseline test

Start with targeted diagnostics only. Do not run the whole suite repeatedly.

Run:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_multi_model_baseline.py::test_runs_sklearn_models -vv --tb=short
```

Then inspect:

- `cajas/tests/test_multi_model_baseline.py`
- related baseline module(s)
- fixture data used by the test
- dependency availability, especially sklearn-like dependencies
- whether the failure came from CSV loading policy changes
- whether the test is doing real model training and should be marked integration/slow
- whether the test can be converted to a deterministic tiny fixture test

Expected fix options:

- If it is a real regression, fix the baseline code.
- If it is environment-dependent, make the test skip only when dependency is genuinely unavailable.
- If it is too expensive for fast validation, split:
  - a lightweight fast unit test
  - a marked `integration` or `slow` model execution test
- If it depends on full CSV reads, move it to tiny fixture / row-limit / sample mode.

Do not hide the failure by deleting the test.

---

# Part B — Refactor baseline full-read CSV candidates

Run or inspect the latest audit:

```bash
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py \
  --project-root cajas \
  --data-root /home/phiner/projects/research/data \
  --out-json tmp/data-io-audit/data_source_audit_phase346_before.json \
  --out-md tmp/data-io-audit/data_source_audit_phase346_before.md
```

Prioritize remaining high/medium candidates under:

- `cajas/baseline/*`
- `cajas/audits/leakage_drift_audit.py`
- generated-artifact report utilities

For each candidate, classify:

- fixture-only
- generated artifact, bounded
- generated artifact, potentially large
- real user data path
- docs/test-only

Refactor high-value sites to use:

- `cajas.data_io.csv_loading_policy`
- `cajas.data_io.chunked_csv_reader`
- row limits
- selected columns
- sample-only modes
- manifest/cache input where appropriate

Add CLI flags where relevant:

```bash
--row-limit N
--chunk-size N
--sample-only
--allow-large-data
--use-cache
--cache-root PATH
--manifest PATH
```

Do not break existing CLI compatibility.

---

# Part C — Fast validation test tier cleanup

Fast validation currently spends most time in pytest, not compile/hygiene.

Actions:

1. Run duration report for fast subset:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration" --durations=50
```

If too expensive, run targeted baseline tests:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_multi_model_baseline.py --durations=30
```

2. For expensive baseline/model tests:
   - convert to tiny deterministic unit tests where possible
   - mark true cross-module model execution as `integration` or `slow`
   - ensure fast subset still covers schema/config/logic without training-heavy runtime

3. Update marker policy tests if needed.

4. Update `cajas/docs/test_runtime_optimization_notes.md` with:
   - failing test diagnosis
   - slow baseline tests found
   - what was moved to integration/slow
   - new recommended commands

---

# Part D — Improve audit_data_sources after baseline refactor

Update:

- `cajas/reports/data_source_audit.py`
- `cajas/docs/full_read_csv_refactor_plan.md`

Make the after-refactor report clearer:

- baseline modules migrated
- remaining candidates by category
- exact reasons for candidates left unchanged
- whether a full-read is bounded by row limit / fixture / generated tiny artifact
- high-priority next targets

Goal:

- Reduce `reads_full_csv_likely_count` again if feasible.
- If count does not reduce due to static pattern detection, make classification more precise so that actionable high-risk count decreases.

---

# Part E — Tests

Add or update tests for:

## Baseline failure

- targeted test now passes or is split correctly
- dependency skip is explicit and justified if needed
- fast unit coverage remains

## Baseline CSV policy

- baseline module uses row-limit/sample mode when provided
- baseline module rejects large full-read without `--allow-large-data` where applicable
- tiny fixture path still works
- generated artifact path behavior remains backward compatible

## Fast validation

- `test_multi_model_baseline.py::test_runs_sklearn_models` is no longer a fast-tier blocker
- expensive model execution tests are marked integration/slow when appropriate
- fast validation excludes integration/slow/smoke/closure/full

## Audit

- baseline read_csv candidates have improved classification
- full-read refactor plan includes baseline/audit remaining items

Keep tests deterministic and lightweight.

---

# Part F — Documentation updates

Update:

- `cajas/README.md`
- `cajas/docs/test_runtime_optimization_notes.md`
- `cajas/docs/data_io_optimization_notes.md`
- `cajas/docs/full_read_csv_refactor_plan.md`
- `tasks/phase_346_365_baseline_runtime_csv_closure_prompt.md`

Document:

- cause and fix for `test_multi_model_baseline.py` failure
- baseline CSV loading policy
- remaining full-read candidates
- updated fast validation runtime
- how to run integration/slow baseline tests explicitly

Recommended daily command remains:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast
```

Targeted integration command:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests -m "integration and not slow and not smoke"
```

Slow tests:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests -m "slow"
```

---

# Part G — Validation commands

Use targeted checks first:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_multi_model_baseline.py::test_runs_sklearn_models -vv --tb=short
```

Then run bounded validation:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_phase346_after.json --out-md tmp/data-io-audit/data_source_audit_phase346_after.md
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration"
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/validation-runtime-audit/fast_validation_phase346.json
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
```

Optional duration report:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration" --durations=50
```

If commands exceed a few minutes, stop and report bottleneck rather than burning time.

---

# Commit guidance

Suggested split:

1. `fix: repair multi-model baseline fast test`
2. `refactor: apply csv loading policy to baseline readers`
3. `test: reduce baseline runtime in fast validation`
4. `docs: document baseline csv and runtime closure`

Report:

- changed files
- failure root cause
- validation results
- data source audit before/after
- fast pytest runtime before/after
- fast validation runtime
- remaining full-read candidates
- remaining slow tests
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
- Failure root cause
- Validation
- Data source audit before/after
- Runtime before/after
- Remaining risks
- Git commits
- Final status

Do not push from Codex unless explicitly instructed.
