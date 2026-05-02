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
