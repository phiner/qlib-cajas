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

## Phase 456-485 Fast Validation Subprocess Hotspot Closure

Baseline fast subset timing:

- Command:
  - `./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration" --durations=30 -q`
- Runtime before this phase: `111.43s`
- Slowest tests before this phase:
  - `8.24s` `cajas/tests/test_validation_runners.py::ValidationRunnersTests::test_fail_on_budget_returns_nonzero`
  - `8.24s` `cajas/tests/test_validation_runners.py::ValidationRunnersTests::test_fast_validation_writes_timing_json`
  - `4.01s` `cajas/tests/test_validate_qlib_handler_input_cli.py::ValidateQlibHandlerInputCliTests::test_cli_outputs_validation_report`
  - `2.93s` `cajas/tests/test_baseline_runner.py::BaselineRunnerTests::test_artifact_writing`

Changes:

- `run_fast_validation.py` now exposes an injected execution surface:
  - validation plan objects
  - validation step results
  - fake-runner support
  - deterministic timer support
  - timing JSON writer
  - budget evaluation
- `test_validation_runners.py` now verifies command planning, timing JSON, and budget failure semantics without spawning a real nested validation subprocess.
- `test_baseline_runner.py::test_artifact_writing` now tests the artifact writer directly with a tiny payload.
- Runtime audit and marker-policy tests guard against reintroducing unmarked validation-runner subprocess tests in the fast tier.

Targeted timing after refactor:

- `./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_runners.py cajas/tests/test_baseline_runner.py -q --durations=10`
- Runtime: `4.80s`
- Former validation-runner subprocess tests no longer appear in targeted slow durations.

Final fast validation timing after refactor:

- Fast pytest subset: `306 passed, 15 deselected in 100.43s`.
- `run_fast_validation.py --tier fast`: `306 passed, 15 deselected`; timing JSON total `100.57s`.
- The under-90s target was not reached in this phase.
- Remaining top slow tests are now CLI artifact/report tests rather than validation-runner subprocess tests:
  - `3.94s` `test_validate_qlib_handler_input_cli.py::ValidateQlibHandlerInputCliTests::test_cli_outputs_validation_report`
  - `3.49s` `test_baseline_runner.py::BaselineRunnerTests::test_training_and_model_actions_are_disabled`
  - `3.37s` `test_build_final_readiness_summary_cli.py::BuildFinalReadinessSummaryCliTests::test_cli_writes_output`
  - `3.27s` `test_build_final_research_bundle_cli.py::BuildFinalResearchBundleCliTests::test_cli`
  - `3.19s` `test_build_final_readiness_packet_cli.py::BuildFinalReadinessPacketCliTests::test_cli_writes_output`

Data-source audit stability:

- `reads_full_csv_likely_count`: `2`
- real-data-risk records: `3`
- no new production CSV reader was introduced by this phase.

Policy:

- Subprocess-heavy validation runner tests should use injected runner/timer hooks.
- If a real CLI subprocess smoke remains necessary, mark it `integration` and run it explicitly:
  - `./.venv-qlib313/bin/python -m pytest cajas/tests -m "integration and not slow and not smoke"`

## Phase 486-515 Commit Recovery + Under-90 Push

Commit recovery status:

- Local commit creation is currently blocked by approval service error `503 Service Unavailable` in this session.
- Working tree still preserves the intended split:
  - staged: fast validation runner/test/audit group
  - unstaged: baseline/docs + new fast-tier CLI optimization

Fast-tier profiling and optimization:

- First profiling run:
  - `306 passed, 15 deselected in 85.83s`
- Known hotspot converted:
  - `cajas/tests/test_validate_qlib_handler_input_cli.py` no longer spawns real subprocesses.
  - now uses direct `build_qlib_handler_input(...)` and in-process CLI `main()` invocation with patched `sys.argv`.
- Post-change profiling run:
  - `306 passed, 15 deselected in 89.67s`
- Final fast runner:
  - `run_fast_validation.py --tier fast` completed with `pytest_fast` step around `91.00s`, total around `94.06s`.

Observed top remaining slow fast-tier tests are mostly CLI artifact/report tests around ~2.1-2.5s each:

- `test_data_source_audit.py::test_cli_writes_outputs`
- `test_io_runtime_audit.py::test_cli_writes_outputs`
- `test_validation_runtime_audit.py::test_audit_cli_writes_json_and_markdown`
- `test_train_qlib_model_bridge_baseline_cli.py::test_cli`
- many `test_build_*_cli.py` report/packet builders

Data-source audit after Phase 486 changes:

- `reads_full_csv_likely_count = 2` (stable, no regression observed)
- no new high-risk data-source pattern was introduced by this phase work.

Recommended operational commands:

- Daily fast tier:
  - `./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast`
- Tight loop:
  - `./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier quick`
- Explicit integration:
  - `./.venv-qlib313/bin/python -m pytest cajas/tests -m "integration and not slow and not smoke"`
- Micro smoke:
  - `./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro`

## Phase 516-545 Consistent Under-90s Hardening

Commit recovery:

- Local commit creation remains blocked in this session by approval-service error `503 Service Unavailable`.
- No push was attempted.
- Pending commit groups remain preserved in working tree.

Additional fast-tier CLI hotspot conversions (subprocess removed, in-process `main()` used):

- `cajas/tests/test_build_offline_review_packet_cli.py`
- `cajas/tests/test_build_qlib_adapter_contract_cli.py`
- `cajas/tests/test_build_ci_validation_plan_cli.py`

Each now patches `sys.argv`, calls the script module `main()`, and keeps file-output assertions.

Runtime impact:

- Fast subset before this phase (recent baseline): `87.81s` (and earlier near-boundary runs: `89.67s`, `89.81s`)
- Fast subset after conversions:
  - `306 passed, 15 deselected in 80.06s`
- `run_fast_validation.py --tier fast` after conversions:
  - `pytest_fast`: `80.88s`
  - total: `83.77s`
- Micro smoke:
  - `10.33s`

Remaining top slow tests (fast tier) are mostly small CLI/report artifact writers around ~2.0-2.5s:

- `test_build_research_pipeline_manifest_cli.py::test_cli_writes_output`
- `test_io_runtime_audit.py::test_cli_writes_outputs`
- `test_data_source_audit.py::test_cli_writes_outputs`
- `test_validation_runtime_audit.py::test_audit_cli_writes_json_and_markdown`
- several `test_build_*_cli.py` report/packet tests

Data-source audit (Phase 516):

- `reads_full_csv_likely_count = 2` (stable, no regression)
- no new high-risk data-source regression introduced

## Phase 566-585 Final Delivery Baseline

- final fast subset runtime: `306 passed, 15 deselected in 80.06s`
- final `run_fast_validation.py --tier fast`:
  - `pytest_fast`: `80.88s`
  - total: `83.77s`
- final micro smoke runtime: `10.33s`
- data-source audit remains stable:
  - `reads_full_csv_likely_count = 2`

Delivery artifacts:

- packet builder: `cajas/scripts/build_validation_delivery_packet.py`
- packet module: `cajas/reports/validation_delivery_packet.py`
- delivery outputs:
  - `tmp/validation-delivery/validation_delivery_packet.json`
  - `tmp/validation-delivery/validation_delivery_packet.md`
- final workflow docs:
  - `cajas/docs/final_research_stack_index.md`
  - `cajas/docs/future_work_checklist.md`


## Phase 806-835 Dataset Quality Runtime Tightening

Regression identified:

- Fast subset runtime before this phase: `~106.18s` (pytest_fast: `~103.13s`)
- Regression cause: Phase 776-805 added dataset-quality modular CLI tests that used subprocess execution for 6 CLI scripts.
- Slowest test: `test_dataset_quality_modular_clis.py::test_modular_clis_write_outputs` took `11.47s`.

Optimization applied:

- Updated 6 dataset-quality CLI scripts to accept optional `argv` parameter:
  - `build_dataset_quality_report.py`
  - `build_label_coverage_diagnostics.py`
  - `build_time_coverage_diagnostics.py`
  - `run_chunked_feature_dry_run.py`
  - `build_feature_schema_manifest.py`
  - `build_offline_research_queue_summary.py`
- Converted `test_dataset_quality_modular_clis.py` from subprocess calls to in-process `main(argv)` calls.
- Test runtime improvement: `11.47s` → `0.05s` (~230x speedup).

Runtime after optimization:

- Fast subset: `310 passed, 16 deselected in 81.94s` (pytest_fast)
- `run_fast_validation.py --tier fast`: total `85.19s`
- Improvement: `~21s` faster (~20% improvement)
- Micro smoke: `11.47s` (stable)
- Dataset quality smoke: passes (stable)

Data-source audit:

- `read_csv_count = 29` (stable, no regression)

Remaining top slow tests (fast tier):

- `3.06s` `test_baseline_runner.py::test_training_and_model_actions_are_disabled`
- `2.42s` `test_io_runtime_audit.py::test_cli_writes_outputs`
- `2.31s` `test_validation_runtime_audit.py::test_audit_cli_writes_json_and_markdown`
- `2.26s` `test_data_source_audit.py::test_cli_writes_outputs`
- `2.12s` `test_train_qlib_model_bridge_baseline_cli.py::test_cli`

Policy:

- Dataset-quality CLI tests now use in-process calls for fast validation.
- Explicit dataset-quality smoke workflow remains available:
  - `./.venv-qlib313/bin/python cajas/scripts/run_dataset_quality_smoke.py --out-root tmp/dataset-quality-smoke`
- Modular CLI scripts support both command-line and programmatic invocation.
