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
