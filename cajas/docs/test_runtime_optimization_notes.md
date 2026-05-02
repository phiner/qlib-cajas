# Test Runtime Optimization Notes

## Slowest Test Class

- End-to-end smoke orchestration tests are the dominant runtime cost.
- Typical examples:
  - `cajas/tests/test_run_full_research_stack_smoke.py`
  - `cajas/tests/test_run_research_quality_loop_smoke.py`
  - `cajas/tests/test_run_research_remediation_smoke.py`
  - `cajas/tests/test_run_final_reproducibility_closure_smoke.py`
  - `cajas/tests/test_run_governance_review_closure_smoke.py`

Measured with:

- `./.venv-qlib313/bin/python -m pytest cajas/tests/test_run_full_research_stack_smoke.py cajas/tests/test_run_research_quality_loop_smoke.py cajas/tests/test_run_research_remediation_smoke.py cajas/tests/test_run_final_reproducibility_closure_smoke.py cajas/tests/test_run_governance_review_closure_smoke.py --durations=20`

Observed slowest durations:

- `208.65s` `test_run_governance_review_closure_smoke.py::test_smoke_outputs`
- `192.28s` `test_run_final_reproducibility_closure_smoke.py::test_smoke_outputs`
- `168.77s` `test_run_research_remediation_smoke.py::test_smoke_outputs`
- `156.32s` `test_run_research_quality_loop_smoke.py::test_smoke_outputs`
- `142.36s` `test_run_full_research_stack_smoke.py::test_smoke_outputs`

## Likely Reason

- These tests spawn multi-stage subprocess workflows and generate large temporary artifact trees.
- Many of them execute nested smoke runners that invoke other smoke scripts.

## Classification

- `smoke` + `slow`: full end-to-end workflow tests.
- default unit/integration tests: lightweight tests without full pipeline orchestration.

## Optimization Actions

- Added pytest markers:
  - `smoke`
  - `slow`
  - `integration`
- Marked heavy smoke test files with `pytestmark = [pytest.mark.smoke, pytest.mark.slow]`.
- Added fast validation command:
  - `./.venv-qlib313/bin/python -m pytest cajas/tests -m "not slow and not smoke"`
- Added validation runners:
  - `cajas/scripts/run_fast_validation.py`
  - `cajas/scripts/run_smoke_validation.py`
- Updated CI validation plan tiers to separate hygiene, fast unit, full pytest, and explicit smoke workflows.

## Marker Policy (Phase 236-275)

- `unit`: fast unit-level tests.
- `integration`: medium-cost integration tests.
- `smoke`: end-to-end smoke workflows.
- `slow`: runtime-heavy tests.
- `closure`: latest closure/review smoke flows.
- `full`: historical full-stack mega smoke flows.

Heavy smoke files are marked `smoke + slow` and additionally:

- closure flows: `test_run_governance_review_closure_smoke.py`, `test_run_final_reproducibility_closure_smoke.py`
- full historical flows: `test_run_full_research_stack_smoke.py`, `test_run_research_quality_loop_smoke.py`, `test_run_research_remediation_smoke.py`

## Recommended Commands

Daily development:

- `./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py`

Quick smoke sanity:

- `./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro`

Before merge:

- `./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full"`
- `./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier minimal --out-root tmp/smoke-validation-minimal`

Release or closure checks only (expensive):

- `./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier closure --out-root tmp/smoke-validation-closure`
- `./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier full --out-root tmp/smoke-validation-full`

## Runtime Audit

Static audit command:

- `./.venv-qlib313/bin/python cajas/scripts/audit_validation_runtime.py --tests-root cajas/tests --out-json tmp/validation-runtime-audit/validation_runtime_audit.json --out-md tmp/validation-runtime-audit/validation_runtime_audit.md`

Optional dynamic duration probe:

- add `--run-durations --durations 30`

## Boundaries

Validation remains offline research-only and does not enable broker/live/paper execution, order generation/routing, position sizing, portfolio optimization, or PnL optimization.

## Fast Validation Profiling Amendment

Default fast pytest expression now excludes integration tests:

- `not smoke and not slow and not closure and not full and not integration`

`run_fast_validation.py` now supports:

- tiers: `quick`, `fast`, `full-pytest`
- profiling output with per-step timing table
- JSON timing output: `--timing-json <path>`
- budget flags: `--max-seconds`, `--fail-on-budget`
- mode flags: `--skip-compileall`, `--skip-pytest`, `--only-pytest`, `--only-hygiene`

Recommended commands:

- Tight edit loop:
  - `./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier quick`
- Before commit:
  - `./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast`
- Tiny smoke:
  - `./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro`
- Integration-only explicit run:
  - `./.venv-qlib313/bin/python -m pytest cajas/tests -m "integration and not slow and not smoke"`
- Slow-only explicit run:
  - `./.venv-qlib313/bin/python -m pytest cajas/tests -m "slow"`

## Data IO Guardrail Addendum

To avoid I/O wait during development:

- use static audits and fixture-driven checks by default
- avoid reading `/home/phiner/projects/research/data` in fast validation paths
- only enable real-data checks with explicit `--include-real-data`
- for large data roots, require `--allow-large-data` acknowledgement

New helper modules:

- `cajas/reports/runtime_io_summary.py`
- `cajas/reports/io_runtime_audit.py`
- `cajas/reports/data_source_audit.py`
- `cajas/data_io/*`

## Phase 316-345 Runtime Update

- Fast subset runtime before: `136.15s`.
- Latest fast subset run: `129.34s`.
- `run_fast_validation --tier fast` total: `133.69s` (failed due unrelated `test_multi_model_baseline` runtime environment issue).
- Recommendation: isolate/mark expensive baseline tests that depend on local prepared dataset/model environment as integration.

## Phase 346-365 Baseline Runtime Closure

- Root cause of fast-tier failure:
  - `cajas/tests/test_multi_model_baseline.py::test_runs_sklearn_models` used the large local prepared dataset path (`tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv`).
  - CSV loading policy correctly blocked unbounded full reads, so model runs failed with:
    - `large CSV full read blocked; set allow_large_data or use row_limit/chunk_size`
- Fix applied:
  - converted `test_multi_model_baseline` to a deterministic tiny temporary fixture dataset + config.
  - marked `test_multi_model_baseline` as `integration` so default fast tier excludes training-heavy baseline execution.
- Validation:
  - targeted test: `1 passed`.
  - integration marker run: `1 passed`.
  - fast subset (`not smoke and not slow and not closure and not full and not integration`): `300 passed, 14 deselected`.
  - `run_fast_validation.py --tier fast`: pass.
- Updated recommendation:
  - keep schema/logic checks in fast tier.
  - run baseline model execution via explicit integration command:
    - `./.venv-qlib313/bin/python -m pytest cajas/tests/test_multi_model_baseline.py -m "integration"`
