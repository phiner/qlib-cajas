# Phase 366–395 Prompt: Remaining Full-Read Closure + Fast Runtime Subprocess Optimization

You are working on branch:

- `phase-next-mega-logic`

## Current state

Phase 346–365 partially closed the baseline/runtime blocker.

Latest completed changes:

- Fixed the fast-tier blocker:
  - `cajas/tests/test_multi_model_baseline.py::test_runs_sklearn_models`
- Refactored `test_multi_model_baseline` to use deterministic tiny fixture dataset/config instead of large local CSV.
- Moved that test to `integration`, so default fast validation excludes training-heavy baseline execution.
- Added CSV policy checks to baseline analysis modules:
  - `cajas/baseline/calibration_analysis.py`
  - `cajas/baseline/confidence_analysis.py`
  - `cajas/baseline/error_slice_analysis.py`
- Updated runtime/full-read docs.

Latest validation:

```text
PASS: pytest cajas/tests/test_multi_model_baseline.py -vv --tb=short
PASS: pytest cajas/tests/test_multi_model_baseline.py -m "integration" -q
PASS: pytest test_calibration_analysis.py test_confidence_analysis.py test_error_slice_analysis.py -q
PASS: pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration" --durations=20 -q
      300 passed, 14 deselected
PASS: run_fast_validation.py --tier fast
      total: 136.67s
PASS: find cajas -path "*/init.py" -print
PASS: audit_data_sources.py
      reads_full_csv_likely_count: 20 -> 17
```

Known remaining risks:

- Fast validation is green, but still slow: ~136.67s.
- Runtime is dominated by non-smoke tests around validation/subprocess orchestration.
- Remaining high-risk or medium-risk full-read candidates include:
  - `cajas/audits/leakage_drift_audit.py`
  - `prediction_review.py`
  - `qlib_model_bridge_trainer.py`
  - other remaining entries in `tmp/data-io-audit/data_source_audit_phase346_after2.md`
- Working tree may contain unrelated modified/untracked files from earlier phases. Do not revert or mix unrelated changes.

## Phase objective

Implement **Remaining Full-Read Closure + Fast Runtime Subprocess Optimization**.

Primary goals:

1. Reduce remaining actionable full-read CSV candidates from 17.
2. Refactor priority remaining readers:
   - leakage/drift audit
   - prediction review
   - qlib model bridge trainer
   - any other high-risk real-data or generated-large artifact readers
3. Add consistent CSV policy flags/API options:
   - `row_limit`
   - `chunk_size`
   - `sample_only`
   - `allow_large_data`
   - `selected_columns`
   - `use_cache`
   - `manifest`
4. Reduce fast validation runtime by optimizing or marking expensive subprocess/orchestration tests.
5. Keep fast validation green.
6. Preserve research-only and no-execution boundaries.

Target outcomes:

- `run_fast_validation.py --tier fast` passes.
- Fast runtime should improve materially from ~136s if feasible.
- If not feasible, produce exact top slow tests and a plan.
- `reads_full_csv_likely_count` should drop again, or actionable high-risk count should drop with better classification.
- Micro smoke remains fixture-first and does not read real data by default.

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

# Part A — Start from exact audit evidence

First check worktree:

```bash
git status --short
```

Do not revert unrelated files. Keep this phase changes focused.

Run or inspect:

```bash
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py \
  --project-root cajas \
  --data-root /home/phiner/projects/research/data \
  --out-json tmp/data-io-audit/data_source_audit_phase366_before.json \
  --out-md tmp/data-io-audit/data_source_audit_phase366_before.md
```

Use the report to rank remaining candidates:

- high: can read real user CSV or potentially multi-GB CSV
- medium: generated artifacts that may grow large
- low: test fixture / tiny generated data / docs-only
- false positive: static audit pattern but policy already guards it

Update:

- `cajas/docs/full_read_csv_refactor_plan.md`

with a phase 366 section listing exact remaining targets and planned action.

---

# Part B — Refactor remaining high-priority CSV readers

Prioritize these modules if they appear in the audit:

## B1. Leakage/drift audit

Likely file:

- `cajas/audits/leakage_drift_audit.py`

Add support for:

- row limit
- selected columns
- sample-only mode
- large data guard via `csv_loading_policy`
- chunked streaming where practical

If the audit compares train/valid/test CSVs, avoid full loading when only metadata/schema/null-rate/sample stats are needed.

Suggested behavior:

- default: safe for generated/tiny artifacts
- large file without explicit allow: warn/block full read
- row_limit/sample mode: allowed
- chunked mode: allowed for aggregate stats

## B2. Prediction review

Likely files may include:

- `prediction_review.py`
- report/review modules reading predictions CSV

Add:

- row_limit
- selected columns
- sample-only
- chunked summary for large prediction files
- policy checks before full read

## B3. Qlib model bridge trainer

Likely file:

- `cajas/baseline/qlib_model_bridge_trainer.py`

Be careful: training may require full training data in some modes.

Implement safe behavior:

- smoke/default tests use tiny fixture or row_limit
- real/full training requires explicit `allow_large_data` or equivalent
- selected feature/target columns only
- chunking if only metadata/validation is needed
- do not silently truncate real training unless user requested row_limit/sample mode
- preserve existing bounded smoke behavior

## B4. Remaining generated-artifact readers

For remaining medium-risk report utilities:

- add row_limit where reports only need preview
- use chunked stats for counts/distributions when feasible
- classify as generated-artifact risk if not real data
- keep backward compatibility

---

# Part C — Fast runtime subprocess/orchestration optimization

Fast validation still takes ~136s.

Run duration report, but avoid repeating many long runs:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests \
  -m "not smoke and not slow and not closure and not full and not integration" \
  --durations=50 -q
```

Identify top slow files.

Likely candidates:

- tests that spawn subprocess for scripts
- validation runner tests
- audit CLI tests
- report builder CLI tests
- full artifact construction tests not marked integration/slow

For each slow fast-tier test:

Choose one:

1. Convert subprocess tests to direct function tests.
2. Monkeypatch subprocess execution.
3. Use static tiny fixtures.
4. Mark as `integration` if it tests end-to-end CLI behavior and is slow.
5. Keep one cheap CLI smoke per subsystem only if fast.

Do not remove coverage. Split if necessary:

- fast unit test for logic
- integration test for real subprocess

Update marker policy tests if needed.

---

# Part D — Add subprocess runtime audit

Create or update:

- `cajas/reports/validation_runtime_audit.py`
- `cajas/scripts/audit_validation_runtime.py`

Add static detection for:

- `subprocess.run`
- `subprocess.check_call`
- `subprocess.check_output`
- `os.system`
- tests invoking `python cajas/scripts/...`
- tests invoking validation/smoke scripts
- tests that write large temp directories

Output should include:

- test file
- line number
- snippet
- suspected cost
- suggested action:
  - monkeypatch
  - direct function test
  - mark integration
  - keep fast

---

# Part E — Tests

Add/update tests for:

## CSV policy refactors

- leakage drift audit respects row_limit/sample mode
- leakage drift audit blocks/warns large full reads without allow flag
- prediction review respects row_limit/sample mode
- qlib model bridge trainer uses selected columns/row_limit in smoke
- full training path remains explicit
- backward compatibility for tiny fixtures

## Runtime optimization

- subprocess-heavy tests are classified by runtime audit
- marker policy catches unmarked subprocess-heavy fast tests
- run_fast_validation excludes integration/slow/smoke/closure/full
- micro smoke remains real-data-free

## Audit quality

- data source audit classifies policy-guarded read_csv differently from unguarded full read
- docs/full_read_csv_refactor_plan includes remaining high-risk list

Keep tests deterministic and lightweight.

---

# Part F — Documentation

Update:

- `cajas/docs/full_read_csv_refactor_plan.md`
- `cajas/docs/data_io_optimization_notes.md`
- `cajas/docs/test_runtime_optimization_notes.md`
- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`
- `tasks/phase_366_395_remaining_full_read_runtime_prompt.md`

Document:

- which remaining full-read sites were refactored
- which remain and why
- updated audit numbers
- top slow fast-tier tests before/after
- what was moved to integration/slow
- recommended daily validation command

Recommended daily command remains:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast
```

For tight loop:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier quick
```

---

# Part G — Validation commands

Use targeted checks first:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_leakage_drift_audit.py -q
./.venv-qlib313/bin/python -m pytest cajas/tests/test_prediction_review.py -q
./.venv-qlib313/bin/python -m pytest cajas/tests/test_qlib_model_bridge_trainer.py -q
```

If some files do not exist, skip and report.

Then run bounded validation:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_phase366_after.json --out-md tmp/data-io-audit/data_source_audit_phase366_after.md
./.venv-qlib313/bin/python cajas/scripts/audit_validation_runtime.py --tests-root cajas/tests --out-json tmp/validation-runtime-audit/validation_runtime_phase366.json --out-md tmp/validation-runtime-audit/validation_runtime_phase366.md
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration" --durations=30 -q
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/validation-runtime-audit/fast_validation_phase366.json
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
```

If any command exceeds a few minutes, stop and report the bottleneck instead of burning time.

---

# Commit guidance

Suggested split:

1. `refactor: close remaining baseline csv full-read risks`
2. `test: reduce subprocess-heavy fast validation runtime`
3. `feat: improve validation runtime audit for subprocess tests`
4. `docs: document remaining csv and runtime closure`

Report:

- changed files
- validation results
- data source audit before/after
- fast pytest runtime before/after
- run_fast_validation timing
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
- Validation
- Data source audit before/after
- Runtime before/after
- Remaining risks
- Git commits
- Final status

Do not push from Codex unless explicitly instructed.
