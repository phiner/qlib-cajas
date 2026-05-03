# cajas research layer for qlib-cajas

`cajas/` is the independent research layer in this `qlib-cajas` fork.

## Goal

Qlib-based Market Recognition Research for FX K-line data.

Current focus:
- EURUSD 15m K-line market recognition research

Current scope is research-only and is **not** a trading system.

## Out of Scope

This phase does not include:
- live trading
- automatic order placement
- broker integration
- profit prediction promises
- production investment advice

## Phase 0 Objectives

- establish an independent research directory under `cajas/`
- prepare a minimal FX dataset
- generate lightweight K-line features
- generate `future_direction_8` research labels
- provide a first draft Qlib/LightGBM experiment config

## Directory Structure

```text
cajas/
  scripts/       # data preparation and research utilities
  configs/       # draft experiment configs
  data_examples/ # expected input/output schema notes
```

## Dataset Quality Loop (Phase 776-805, Enhanced Phase 836-865, Contracts Phase 866-895)

**Phase 836-865 Enhancements:**

Dataset quality reports now include:
- Quality score (0-100) with grade (A-D or review_needed)
- Status levels: pass, warn, review_needed, blocked
- Label review buckets with priority ranking
- Ranked review items for offline research queue
- Feature readiness categories
- Enhanced time quality with session distribution

**Phase 866-895 Schema Contracts:**

- Explicit schema validation for all report types
- Golden shape snapshots for regression testing
- Contract validation CLI
- Additive vs breaking change detection

**Phase 896-925 Contract Adoption:**

- Integrated contract validation in smoke workflow
- Automatic schema validation after report generation
- CLI failure tests for missing fields and type mismatches
- Contract workflow documentation

**Phase 926-955 Contract Drift Detection:**

- Drift detection against golden shapes
- Reviewer-friendly drift summaries
- Breaking vs additive drift classification
- Drift items with specific change details

**Phase 956-985 Enhanced Drift Semantics and Trend Tracking:**

- Semantic validation for critical field constraints
  - `quality_score` must be in [0, 100]
  - Count fields must be non-negative
  - Grade/status fields validated against known values
- Trend snapshots generated after each smoke run
- Trend comparison CLI for detecting regressions
- Regression detection: contract failures, semantic errors, quality drops, status degradation
- Semantic errors fail contract validation separately from shape drift

**Phase 986-1015 Golden Fixture Scenario Expansion:**

- Multiple edge-case scenarios for robust regression testing
  - `tiny_balanced`, `missing_label_values`, `single_class_label`, `time_gap`, `minimal_columns`
- Scenario manifest describing each scenario
- Scenario builder CLI to regenerate golden shapes
- 6 scenario regression tests (~2s)
- 21 golden shape files committed across 5 scenarios

**Phase 1016-1045 Qlib Experiment Reproducibility Strengthening:**

- Experiment manifest for offline Qlib research reproducibility
- Links dataset quality reports, contract reports, trend snapshots, golden scenarios
- Captures git branch/commit, Python version, platform info
- Manifest builder CLI with validation
- Reviewer-friendly Markdown with artifact table and reproducibility status
- 9 manifest tests (~2s)
- Manifests clearly marked as offline research only, not trading execution

**Phase 1046-1075 Runtime Budget Enforcement and Test Optimization:**

- Runtime budget configuration for validation sustainability
- Budget checking CLI with pass/warn/fail classification
- Reviewer-friendly budget reports with component table
- 9 runtime budget tests (~2s)
- Fast validation: ~83.5s (Phase 986: ~100s, Phase 1016: ~85s)
- Budgets are engineering guardrails, not performance claims

**Phase 1076-1105 Reviewer Report Enhancements — Diffs and Trends:**

- Reviewer diff report generation comparing baseline vs current artifacts
- Compares dataset quality, contract, semantic, drift, runtime budget status
- Detects quality score deltas, status changes, error increases
- 7 reviewer diff tests (~2s)
- Reviewer-friendly Markdown with executive summary and artifact table
- Clearly marked as offline research infrastructure comparison only

**Phase 1106-1135 Validation Delivery Packet and Artifact Index:**

- Validation delivery packet bundling all validation artifacts
- Artifact index with presence/missing status and role classification
- Status aggregation: pass/warn/fail based on critical artifacts
- 6 delivery packet tests (~2s)
- Reviewer-friendly packet index with recommended actions
- Optional artifact copying into packet directory

Combined bundle builder:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_dataset_quality_research_bundle.py \
  --input-csv cajas/data_examples/validation_fixtures/eurusd_tiny.csv \
  --out-dir tmp/dataset-quality-bundle \
  --label-col future_direction_8 \
  --feature-col Open \
  --feature-col High \
  --feature-col Low \
  --feature-col Close \
  --feature-col Volume \
  --datetime-col "Time (UTC)"
```

Modular CLIs:

- `build_dataset_quality_report.py`
- `build_label_coverage_diagnostics.py`
- `build_time_coverage_diagnostics.py`
- `run_chunked_feature_dry_run.py`
- `build_feature_schema_manifest.py`
- `build_offline_research_queue_summary.py`

Smoke workflow:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_dataset_quality_smoke.py \
  --out-root tmp/dataset-quality-smoke
```

Notes:

- defaults use tiny local fixtures
- larger reads require explicit `--allow-large-data`
- outputs are offline research artifacts only
- quality scores are data quality indicators, not trading/model performance metrics

## Phase 1: Run Real EURUSD 15m Preparation

Run:

```bash
python cajas/scripts/prepare_fx_dataset.py \
  --input ~/projects/research/data/EURUSD_15\ Mins_Bid_2025.01.01_2025.12.31.csv \
  --output-dir tmp/cajas/eurusd_15m_phase1 \
  --symbol EURUSD \
  --timeframe 15m
```

Notes:
- raw input CSV is local-only and should not be committed
- generated outputs are written under `tmp/` and should not be committed
- `future_direction_8` is a market-recognition research label, not a trading signal
- current phase validates data preparation only (no model training)

## Phase 2: Qlib Integration Mapping

- Phase 1 prepared dataset output is used as the current research input for integration planning:
  - `tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv`
  - `tmp/cajas/eurusd_15m_phase1/dataset_manifest.json`
- Phase 2 focus is mapping how this dataset can connect to Qlib `DatasetH` / `DataHandler` workflows.
- Integration notes are documented in:
  - `cajas/docs/qlib_integration_notes.md`
- Qlib core remains unchanged.
- This phase does not run formal training or trading workflows.

## Phase 3: Tracked Tasks and Prepared Handler

- `tasks/` is tracked as project task history and should not be ignored.
- `taskDocs/` is not used in this repository workflow.
- Added minimal prepared dataset handler:
  - `cajas/handlers/prepared_csv_handler.py`
- Added validation CLI:
  - `python cajas/scripts/validate_prepared_dataset_handler.py --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv --label-col future_direction_8`
- This phase validates dataset access, schema checks, and train/valid/test segment slicing only.
- No model training, no qlib core changes, no trading logic.

## Phase 4: Package Cleanup and Dataset Adapter

- Confirmed package init path:
  - `cajas/handlers/__init__.py`
- Added dev test dependency file:
  - `requirements-dev.txt` (pytest)
- Added DatasetH-like external adapter:
  - `cajas/datasets/prepared_dataset.py`
- Added adapter validation CLI:
  - `./.venv-qlib313/bin/python cajas/scripts/validate_prepared_dataset_adapter.py --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv --label-col future_direction_8`
- Existing handler validation CLI remains:
  - `./.venv-qlib313/bin/python cajas/scripts/validate_prepared_dataset_handler.py --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv --label-col future_direction_8`
- Test command:
  - `./.venv-qlib313/bin/python -m pytest cajas/tests/test_prepared_csv_handler.py cajas/tests/test_prepared_dataset.py`

This phase still excludes:
- qlib core modifications
- model training
- trading strategy or execution logic

## Phase 11: Baseline Execution Contract and Preflight

- Added path hygiene checker:
  - `cajas/quality/path_hygiene.py`
  - `cajas/scripts/check_path_hygiene.py`
- Added baseline execution contract:
  - `cajas/baseline/execution_contract.py`
- Added baseline preflight gate:
  - `cajas/baseline/baseline_preflight.py`
  - `cajas/scripts/run_baseline_preflight.py`
- CLI commands:
  - `./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py`
  - `./.venv-qlib313/bin/python cajas/scripts/run_baseline_preflight.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml`

This phase still excludes:
- qlib core modifications
- model training
- trading strategy or execution logic

## Phase 12: Training-Disabled Baseline Command

- Added future baseline run contract (Phase 12 blocked mode):
  - `cajas/baseline/run_contract.py`
- Added training-disabled baseline runner:
  - `cajas/baseline/baseline_runner.py`
  - `cajas/scripts/run_baseline_disabled.py`
- Runner behavior:
  - runs preflight and run-contract checks
  - blocks before any model build/fit/predict/evaluate/serialize action
  - writes blocked-run artifacts only when requested
- CLI command:
  - `./.venv-qlib313/bin/python cajas/scripts/run_baseline_disabled.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml`
- Optional artifact output:
  - `--write-artifacts --output-dir tmp/cajas/baseline_disabled_runs --run-name phase12_baseline_disabled`
  - files:
    - `baseline_blocked_run_report.json`
    - `baseline_run_contract.json`
- Policy note:
  - Codex communication is English-only unless explicitly requested otherwise by the user.
  - Codex does not run `git push`; only local commits are produced.

This phase still excludes:
- qlib core modifications
- model training
- trading strategy or execution logic

## Phase 13: Future Training Skeleton with Explicit Gates

- Added explicit future training enable contract:
  - `cajas/baseline/training_enable_contract.py`
- Added future baseline training skeleton:
  - `cajas/baseline/future_training_skeleton.py`
  - `cajas/scripts/build_future_training_skeleton.py`
- Added small baseline artifact helper:
  - `cajas/baseline/baseline_artifacts.py`
- CLI command:
  - `./.venv-qlib313/bin/python cajas/scripts/build_future_training_skeleton.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml`
- Optional artifact output:
  - `--write-artifacts --output-dir tmp/cajas/future_training_skeletons --run-name phase13_future_training_skeleton`
  - files:
    - `future_training_skeleton_report.json`
    - `training_enable_contract.json`
- Policy remains unchanged:
  - training is still disabled
  - no model construction / fit / predict / evaluate / serialize is executed
  - no qlib core change and no trading scope
  - manual push workflow remains active (`git push` is not run by Codex)

## Phase 10: Training-Guarded Baseline Scaffold

- Added baseline training safety guard:
  - `cajas/baseline/training_guard.py`
- Added training-disabled baseline scaffold:
  - `cajas/baseline/baseline_scaffold.py`
- Added baseline scaffold CLI:
  - `./.venv-qlib313/bin/python cajas/scripts/build_baseline_scaffold.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml`
- JSON mode:
  - `./.venv-qlib313/bin/python cajas/scripts/build_baseline_scaffold.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml --json`
- Optional local artifact:
  - `--write-artifacts --output-dir tmp/cajas/baseline_scaffolds --run-name phase10_baseline_scaffold`
- Label encoding plan is included as a spec (`down:0`, `flat:1`, `up:2`) and is not executed on data.

This phase still excludes:
- qlib core modifications
- model training
- trading strategy or execution logic

## Phase 14: Training Input Materialization Preview (No Training)

- Added label encoding preview module:
  - `cajas/baseline/label_encoding.py`
- Added multiclass metric planning module:
  - `cajas/baseline/metric_plan.py`
- Added training input materialization preview module:
  - `cajas/baseline/training_input_materialization.py`
- Added CLI:
  - `./.venv-qlib313/bin/python cajas/scripts/materialize_training_inputs_preview.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml --output-dir tmp/cajas/training_input_previews --run-name phase14_training_inputs_preview`
- Optional modes:
  - `--no-csv` writes only JSON artifacts
  - `--json` prints report JSON
- Local preview artifacts under `tmp/`:
  - `training_input_materialization_report.json`
  - `label_encoding_preview.json`
  - `metric_plan.json`
  - `train|valid|test` feature/label/encoded-label CSVs when CSV output is enabled
- Policy remains unchanged:
  - training remains disabled
  - no model construction / fit / predict / evaluate / serialize
- no qlib core change and no trading scope

## Phase 18: Qlib Workflow Dry-Run Loader

- Added class path resolver:
  - `cajas/qlib_compat/class_resolver.py`
- Added workflow dry-run loader:
  - `cajas/qlib_compat/workflow_dry_run_loader.py`
- Added CLI:
  - `./.venv-qlib313/bin/python cajas/scripts/run_qlib_workflow_dry_run_loader.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml`
- Optional artifact output:
  - `--write-artifacts --output-dir tmp/cajas/qlib_workflow_dry_run_loader --run-name phase18_qlib_workflow_dry_run_loader`
  - files:
    - `qlib_workflow_dry_run_loader_report.json`
    - `class_resolution_report.json`
    - `qlib_workflow_config_draft.json`
- Phase 18 boundaries remain unchanged:
  - qlib is not initialized
  - qlib workflow is not executed
  - training remains disabled
  - model classes are resolved but not instantiated
  - no trading or signal generation behavior

## Phase 19-20: Run Registry and Controlled Local Baseline Training

- Added local run manifest registry:
  - `cajas/registry/run_registry.py`
- Added controlled local baseline training module:
  - `cajas/baseline/local_baseline_trainer.py`
- Added training CLI:
  - `./.venv-qlib313/bin/python cajas/scripts/train_local_baseline.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml --output-dir tmp/cajas/baseline_runs --run-name phase20_local_baseline`
- Local baseline artifacts are written under `tmp/` and include model metadata, predictions, and classification metrics.
- Scope remains market-recognition classification only:
  - no trading signal generation
  - no backtest/profit analysis
  - no qlib core changes
  - no qlib workflow execution

## Phase 21: Baseline Artifact Inspection and Prediction Review

- Added baseline artifact inspector:
  - `cajas/baseline/baseline_artifact_inspector.py`
- Added prediction review module:
  - `cajas/baseline/prediction_review.py`
- Added inspection CLI:
  - `./.venv-qlib313/bin/python cajas/scripts/inspect_baseline_run.py --run-dir tmp/cajas/baseline_runs/phase20_local_baseline`
- Review artifacts are written under `tmp/` and remain local-only.
- Review scope is classification-only artifact QA:
  - no trading signals
  - no backtest/profit analysis

## Phase 23-26: Reporting and Comparison Workflow

## Research Decision Packet Workflow

This workflow is for research readiness only. It does not trade, does not modify Qlib core, and does not imply production deployment.

Commands:

```bash
python cajas/scripts/build_research_decision_packet.py --reports-dir ... --out-dir ...
python cajas/scripts/build_candidate_promotion_manifest.py --decision-packet ... --out-dir ... --label-variant-id ... --feature-set-id ... --target-name ... --horizon 8 --model-family LightGBM
python cajas/scripts/build_research_report_index.py --root-dir ... --out-dir ...
python cajas/scripts/run_research_packet_smoke.py --out-root tmp/research-packet-smoke
```

Promotion manifest meaning:
- candidate for manual review only
- not a production deployment
- not a trading execution switch

## Qlib Adapter Handoff Workflow

The research decision packet, adapter contract, and dry-run integration packet serve different handoff layers:
- research decision packet: summarizes research quality and readiness findings
- adapter contract: defines strict, testable Qlib-facing candidate metadata and required artifacts
- dry-run integration packet: summarizes what would be needed for controlled Qlib integration without enabling workflows

This phase does not:
- modify Qlib core
- enable live trading or broker execution
- deploy online services

Example commands:

```bash
python cajas/scripts/build_qlib_adapter_contract.py \
  --promotion-manifest ... \
  --out ... \
  --candidate-id ... \
  --feature-set-id ... \
  --label-variant-id ... \
  --target-name ... \
  --frequency 15m

python cajas/scripts/build_qlib_integration_packet.py \
  --adapter-contract ... \
  --out-dir ...

python cajas/scripts/build_qlib_compatibility_report.py \
  --adapter-contract ... \
  --out-dir ...

python cajas/scripts/run_qlib_adapter_smoke.py --out-root tmp/qlib-adapter-smoke
```

Expected output files:
- `qlib_adapter_contract.json`
- `qlib_adapter_contract.validation.json`
- `qlib_integration_packet.json` / `.md`
- `qlib_compatibility_report.json` / `.md`

Issue reading guidance:
- `error`: blocking issue; handoff should not proceed
- `warning`: non-blocking issue; review manually before next phase

## Qlib Dataset/Handler Offline Ingestion Workflow

This phase validates offline dataset/handler readiness only. It does not train models.

Run:

```bash
python cajas/scripts/build_qlib_dataset_contract.py --input-csv ... --out ... --dataset-id ... --label-col future_direction_8
python cajas/scripts/build_qlib_handler_input.py --input-csv ... --out-dir ... --label-col future_direction_8
python cajas/scripts/validate_qlib_handler_input.py --handler-dir ... --out ...
python cajas/scripts/run_qlib_dataset_handler_smoke.py --out-root tmp/qlib-dataset-handler-smoke
```

Interpretation:
- warnings: acceptable for offline smoke, require manual review before model bridge
- blocking issues: must be fixed before Phase 86-95

## Qlib Model / Experiment Bridge Workflow

This phase introduces bounded CPU-only research training from offline handler input artifacts.

Run:

```bash
python cajas/scripts/build_qlib_model_training_contract.py --handler-input ... --handler-manifest ... --dataset-contract ... --handler-smoke-report ... --out ...
python cajas/scripts/train_qlib_model_bridge_baseline.py --training-contract ... --out-dir ... --seed 42 --max-rows 5000
python cajas/scripts/register_qlib_model_run.py --experiment-dir ... --registry ...
python cajas/scripts/compare_qlib_model_runs.py --registry ... --out ...
python cajas/scripts/run_qlib_model_bridge_smoke.py --out-root tmp/qlib-model-bridge-smoke
```

Boundaries:
- research-only metrics (accuracy, macro F1, distributions)
- no trading PnL metrics
- no broker/live execution logic

## Research Gate and No-Broker Dry Run Workflow

This phase adds a conservative gate packet over model bridge artifacts and a no-broker review packet.

Run:

```bash
python cajas/scripts/build_research_gate_packet.py --contract ... --experiment-dir ... --registry ... --comparison ... --out ...
python cajas/scripts/build_no_broker_dry_run_packet.py --gate-packet ... --out ...
python cajas/scripts/build_research_gate_summary.py --gate-packet ... --no-broker-packet ... --out ...
python cajas/scripts/run_research_gate_smoke.py --out-root tmp/research-gate-smoke
```

Notes:
- gate status is encoded in JSON data (`offline_review_ready`, `needs_manual_review`, `blocked`)
- blocked status does not mean CLI crash
- still research-only: no broker, no live data routing, no paper execution

## Final Readiness, Reproducibility, and CI Validation

This phase adds reproducibility checks and a final readiness packet for manual review readiness.

Run:

```bash
python cajas/scripts/run_final_readiness_smoke.py --out-root tmp/final-readiness-smoke
```

Key points:
- final readiness is not trading approval
- reproducibility warnings highlight drift between repeated runs
- blocked actions remain explicitly encoded
- no broker/live/paper execution is introduced

## Stable Reproducibility and Artifact Normalization

Raw run directories can differ due to timestamps, temp roots, and host-specific paths.
Normalization removes expected environment variability while preserving semantic fields such as decisions, metrics, row counts, and blocked actions.

## Research Governance Audit

Run conservative governance scanning to detect forbidden execution capabilities:

```bash
python cajas/scripts/audit_research_governance.py --root cajas --out tmp/full-hardening-smoke/governance/research_governance_audit.json
```

Findings are categorized as `pass` / `warn` / `fail`. Documentation phrases that explicitly forbid execution are allowlisted.

## Artifact Lineage and Offline Review Bundle

Use lineage, run catalog, offline review packet, and final research bundle to consolidate manual review inputs without introducing execution semantics.

## Full Research Stack Smoke

Run:

```bash
python cajas/scripts/run_full_research_stack_smoke.py --out-root tmp/full-hardening-smoke
```

This remains research-only. It does not enable broker, live, or paper execution.

- Added baseline report pack builder:
  - `cajas/scripts/build_baseline_report_pack.py`
- Added multi-model local baseline runner:
  - `cajas/scripts/train_multi_model_baselines.py`
- Added feature-importance summary across runs:
  - `cajas/scripts/summarize_feature_importance.py`
- Added run registry summary reports:
  - `cajas/scripts/summarize_run_registry.py`
- All generated outputs are local artifacts under `tmp/` and remain classification-only.
- No trading/backtest/profit analysis is included.

## Phase 27-30: Sanitation, Export, and Health Checks

- Added numeric feature-value audit and model-input sanitation in baseline training.
- Added hardened multi-model status artifacts (`completed/skipped/failed`) and summary CSV outputs.
- Added markdown export for baseline report JSON:
  - `cajas/scripts/export_baseline_reports.py`
- Added run registry health checks:
  - `cajas/scripts/check_run_health.py`
- Source prepared CSV remains unchanged; sanitation applies only to model input matrices.
- No trading/backtest/profit analysis is included.

## Phase 31-34: Registry, Dashboard, Confidence, Research Pack

- Added registry cleanup/classification:
  - `cajas/scripts/classify_run_registry.py`
- Added dashboard data export:
  - `cajas/scripts/export_dashboard_data.py`
- Added prediction confidence analysis:
  - `cajas/scripts/analyze_prediction_confidence.py`
- Added consolidated research report pack:
  - `cajas/scripts/build_research_report_pack.py`
- All outputs are local under `tmp/` and remain classification/research artifacts only.

## Phase 35: External Holdout Validation

- Added external holdout dataset support:
  - train on 2020-2024 prepared data
  - validate on 2025 prepared data
- Added CLI:
  - `./.venv-qlib313/bin/python cajas/scripts/train_external_holdout_baseline.py --train ... --holdout ... --output-dir tmp/cajas/external_holdout_runs --run-name phase35_train_2020_2024_validate_2025 --model-family LightGBM`
- This is out-of-sample classification validation only.
- No trading/backtest/profit analysis is included.

## Phase 9: Training-Disabled Baseline Plan

- Added dependency probe module:
  - `cajas/environment/dependency_probe.py`
- Enhanced feature audit details:
  - missing value ratios
  - top missing feature summary
- Added training-disabled baseline planning module:
  - `cajas/baseline/baseline_plan.py`
- Added baseline plan CLI:
  - `./.venv-qlib313/bin/python cajas/scripts/build_baseline_plan.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml`
- JSON mode:
  - `./.venv-qlib313/bin/python cajas/scripts/build_baseline_plan.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml --json`
- Optional local artifact:
  - `--write-artifacts --output-dir tmp/cajas/baseline_plans --run-name phase9_baseline_plan`

This phase still excludes:
- qlib core modifications
- model training
- trading strategy or execution logic

## Phase 8: Baseline Readiness Gate

- Added feature audit module:
  - `cajas/audits/feature_audit.py`
- Added label audit module:
  - `cajas/audits/label_audit.py`
- Added baseline readiness gate:
  - `cajas/readiness/baseline_readiness.py`
- Added readiness CLI:
  - `./.venv-qlib313/bin/python cajas/scripts/check_baseline_readiness.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml`
- JSON mode:
  - `./.venv-qlib313/bin/python cajas/scripts/check_baseline_readiness.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml --json`
- Optional artifact output:
  - `--write-artifacts --output-dir tmp/cajas/baseline_readiness --run-name phase8_baseline_readiness`

This phase still excludes:
- qlib core modifications
- model training
- trading strategy or execution logic

## Phase 7: Dry-Run Artifact Recorder

- Added local dry-run artifact recorder:
  - `cajas/recorders/dry_run_recorder.py`
- Extended experiment plan dry-run CLI with optional artifact writing:
  - `--write-artifacts`
  - `--output-dir`
  - `--run-name`
- Artifact file names:
  - `run_manifest.json`
  - `config_snapshot.json`
  - `workflow_summary.json`
  - `validation_report.json`
- Example:
  - `./.venv-qlib313/bin/python cajas/scripts/run_experiment_plan_dry_run.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml --write-artifacts --output-dir tmp/cajas/experiment_dry_runs --run-name phase7_eurusd_15m_dry_run`
- Artifact outputs under `tmp/` are local-only and should not be committed.
- Test command:
  - `./.venv-qlib313/bin/python -m pytest cajas/tests/test_prepared_csv_handler.py cajas/tests/test_prepared_dataset.py cajas/tests/test_prepared_workflow.py cajas/tests/test_experiment_config.py caixas/tests/test_experiment_plan_dry_run.py cajas/tests/test_dry_run_recorder.py caixas/tests/test_experiment_plan_artifacts.py`

This phase still excludes:
- qlib core modifications
- model training
- trading strategy or execution logic

## Phase 6: Experiment Config Plan Dry-Run

- Added training-disabled config loader:
  - `cajas/config/experiment_config.py`
- Added experiment plan dry-run CLI:
  - `./.venv-qlib313/bin/python cajas/scripts/run_experiment_plan_dry_run.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml`
- Safety gates:
  - config validation
  - `training.enabled` must remain `false`
  - workflow remains dry-run only
- Optional flags:
  - `--input-override`
  - `--json`
  - `--strict`
- Test command:
  - `./.venv-qlib313/bin/python -m pytest cajas/tests/test_prepared_csv_handler.py cajas/tests/test_prepared_dataset.py cajas/tests/test_prepared_workflow.py cajas/tests/test_experiment_config.py cajas/tests/test_experiment_plan_dry_run.py`

This phase still excludes:
- qlib core modifications
- model training
- trading strategy or execution logic

## Phase 5: Workflow Bridge Dry-Run

- Package init naming is standard and confirmed:
  - `cajas/handlers/__init__.py`
  - `cajas/datasets/__init__.py`
- Added Qlib-inspired workflow bridge:
  - `cajas/workflows/prepared_workflow.py`
- Added workflow dry-run CLI:
  - `./.venv-qlib313/bin/python cajas/scripts/run_prepared_workflow_dry_run.py --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv --label-col future_direction_8`
- JSON output mode:
  - `./.venv-qlib313/bin/python cajas/scripts/run_prepared_workflow_dry_run.py --input tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv --label-col future_direction_8 --json`
- Test command:
  - `./.venv-qlib313/bin/python -m pytest cajas/tests/test_prepared_csv_handler.py cajas/tests/test_prepared_dataset.py cajas/tests/test_prepared_workflow.py`

This phase still excludes:
- qlib core modifications
- model training
- trading strategy or execution logic

## Phase 15: Qlib Dataset Compatibility Probe (No Training)

- Added Qlib compatibility probe package:
  - `cajas/qlib_compat/qlib_probe.py`
  - `cajas/qlib_compat/dataset_shape_probe.py`
  - `cajas/qlib_compat/prepared_dataset_h_like.py`
- Added CLI:
  - `./.venv-qlib313/bin/python cajas/scripts/probe_qlib_dataset_compat.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml`
- Probe scope:
  - checks Qlib import availability and key Dataset API classes
  - checks whether current prepared segment outputs match DatasetH-like shape expectations
  - keeps training disabled and does not initialize Qlib
- Policy remains unchanged:
  - no model build / fit / predict / evaluate / serialize
  - no qlib core modifications
  - no trading scope

## Phase 16: Qlib DatasetH Adapter Probe (No Training)

- Added real Qlib DatasetH adapter probe module:
  - `cajas/qlib_compat/prepared_dataset_h_adapter.py`
- Added adapter comparison probe:
  - `cajas/qlib_compat/adapter_comparison_probe.py`
- Added CLI:
  - `./.venv-qlib313/bin/python cajas/scripts/probe_qlib_dataset_h_adapter.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml`
- Probe scope:
  - compares `PreparedDataset`, `PreparedDatasetHLike`, and Qlib adapter outputs
  - accepts Qlib-style `prepare(..., col_set=..., data_key=...)` signature
  - keeps adapter external to qlib core
- Boundaries remain unchanged:
  - `qlib.init()` is not called
  - training remains disabled
  - no model build / fit / predict / evaluate / serialize
  - no qlib core modifications and no trading scope

## Phase 17: Qlib Workflow Config Probe (No Execution, No Training)

- Added workflow-config probe module:
  - `cajas/qlib_compat/workflow_config_probe.py`
- Added CLI:
  - `./.venv-qlib313/bin/python cajas/scripts/probe_qlib_workflow_config.py --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml`
- Probe scope:
  - builds inspection-only Qlib-style workflow config draft
  - validates training/model/workflow-off schema constraints
  - writes optional local JSON artifacts under `tmp/`
- Boundaries remain unchanged:
  - Qlib is not initialized
  - Qlib workflow is not executed
  - training remains disabled
  - no qlib core changes and no trading scope

## Phase 36-40: Holdout Diagnosis and Research Decision

- Added external holdout benchmarking for internal-split vs external-holdout runs.
- Added flat-class diagnosis for rare-class support/prediction behavior.
- Added horizon label preview for `future_direction_4`, `future_direction_8`, `future_direction_16`.
- Added feature-group audit for ablation planning.
- Added phase-level research decision reporting from existing local artifacts.
- All outputs remain classification research artifacts under `tmp/`.
- No trading strategy, backtest, or profit analysis is added.

## Phase 41-45: Label Redesign and Horizon Holdout

- Added threshold-based label generation for `future_direction_{horizon}_thr_{threshold}` variants.
- Added label-variant external holdout training with `multiclass` and `binary_drop_flat` modes.
- Added label-variant comparison and phase-level label decision reporting.
- Threshold semantics are classification label thresholds only, not trading thresholds.

## Phase 46-55: Research Quality and Qlib Readiness

- Added K-line structure feature builder and feature-set registry/comparison.
- Added calibration analysis, seed stability runner, and rolling-year validation plan builder.
- Added error-slice analysis and leakage/drift audit v2.
- Added Qlib readiness report v2 and research roadmap report.
- Qlib workflow remains unexecuted; all outputs stay classification research artifacts under `tmp/`.

## Research Quality Loop Closure

- End-to-end smoke command:
  - `./.venv-qlib313/bin/python cajas/scripts/run_research_quality_loop_smoke.py --out-root tmp/research-quality-loop-smoke`
- Reproducibility inspection tools:
  - `cajas/scripts/explain_stable_reproducibility.py`
  - `cajas/scripts/build_normalization_coverage_report.py`
- Governance remediation tool:
  - `cajas/scripts/build_governance_remediation_report.py`
- Refined readiness and reviewer tools:
  - `cajas/scripts/build_final_readiness_packet.py`
  - `cajas/scripts/build_final_readiness_summary.py`
  - `cajas/scripts/build_reviewer_decision_packet.py`
- Blocked/fail statuses are expected governance signals and must remain visible for manual review.
- Reviewer approval is offline-research-only and does not permit broker integration, live trading, or paper trading execution.

## Research Remediation Workflow

- Run:
  - `./.venv-qlib313/bin/python cajas/scripts/run_research_remediation_smoke.py --out-root tmp/research-remediation-smoke`
- This workflow localizes blocker evidence, rebuilds governance remediation, and prints before/after top-level statuses.

## Semantic Reproducibility Blockers

- Use:
  - `cajas/scripts/localize_research_blockers.py`
  - `cajas/scripts/diff_normalized_artifacts.py`
- Reproducibility remediation is conservative: normalize only non-semantic run metadata/paths/ids and keep metrics/status semantics intact.

## Governance True Violation Remediation

- Governance findings are remediated without weakening forbidden-execution boundaries.
- Self-audit implementation tokens are treated as audit internals, not runtime execution behavior.

## Readiness Status After Remediation

- Acceptable non-blocked outcomes remain:
  - `research_stack_ready_for_manual_review`
  - `needs_reproducibility_review`
  - `needs_manual_governance_review`
- No readiness status permits broker/live/paper execution.

## Final Stable Reproducibility Closure

- Run:
  - `./.venv-qlib313/bin/python cajas/scripts/run_final_reproducibility_closure_smoke.py --out-root tmp/final-repro-closure-smoke`

## Deterministic Artifact Fingerprints

- Stable fingerprinting normalizes only non-semantic run-identity drift (timestamps, temp roots, run labels, generated IDs, derived hash metadata).
- Semantic fields remain strict:
  - metrics
  - statuses
  - blocked actions
  - governance finding content
  - reviewer decisions

## Readiness After Reproducibility Closure

- If stable reproducibility closes and governance remains manual-review, readiness can move to `needs_manual_governance_review`.
- No readiness status enables broker/live/paper execution.

## Manual Governance Review Closure

- Run:
  - `./.venv-qlib313/bin/python cajas/scripts/run_governance_review_closure_smoke.py --out-root tmp/governance-review-smoke`

## Research-Only Approval Packet

- Build decision:
  - `cajas/scripts/build_governance_review_decision.py`
- Build approval packet:
  - `cajas/scripts/build_research_only_approval_packet.py`

## Offline Research Approval Scope

- `offline_research_approved` means offline-research-only continuation.
- It never authorizes broker/live/paper execution, order routing/generation, position sizing, portfolio optimization, or PnL optimization.

## Validation Tiers

- Tier 0:
  - `./.venv-qlib313/bin/python -m compileall cajas`
  - `./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py`
  - `find cajas -path "*/init.py" -print`
  - `git ls-files | grep -E '(^|/)init\.py$' || true`
- Tier 1 (fast):
  - `./.venv-qlib313/bin/python -m pytest cajas/tests -m "not slow and not smoke"`
- Tier 2 (all pytest):
  - `./.venv-qlib313/bin/python -m pytest cajas/tests`
- Tier 3 (explicit smoke minimal):
  - `./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier minimal --out-root tmp/smoke-validation`

## Validation Runtime (Phase 236-275)

Recommended daily validation:

- `./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py`

Fast pytest-only command:

- `./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full"`

Smoke tiers:

- micro: `./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro`
- minimal: `./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier minimal --out-root tmp/smoke-validation-minimal`
- closure (expensive): `./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier closure --out-root tmp/smoke-validation-closure`
- full (very expensive): `./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier full --out-root tmp/smoke-validation-full`

Runtime audit:

- `./.venv-qlib313/bin/python cajas/scripts/audit_validation_runtime.py --tests-root cajas/tests --out-json tmp/validation-runtime-audit/validation_runtime_audit.json --out-md tmp/validation-runtime-audit/validation_runtime_audit.md`

Note: `python -m pytest cajas/tests` can be expensive because closure/full smoke tests invoke nested multi-stage subprocess workflows.

## Fast Validation Profiling Amendment

Daily command tiers:

- Tight edit loop:
  - `./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier quick`
- Before commit:
  - `./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast`
- Tiny smoke:
  - `./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro`

Fast default expression:

- `not smoke and not slow and not closure and not full and not integration`

Explicit commands:

- Integration checks:
  - `./.venv-qlib313/bin/python -m pytest cajas/tests -m "integration and not slow and not smoke"`
- Slow checks:
  - `./.venv-qlib313/bin/python -m pytest cajas/tests -m "slow"`

Phase 456-485 subprocess hotspot closure:

- `run_fast_validation.py` budget, timing, and command-plan behavior is testable with injected runners and deterministic timers.
- Fast-tier tests should not spawn nested `run_fast_validation.py` subprocesses.
- Keep true CLI subprocess smoke tests marked `integration` so they run only by explicit command.

## Data IO Optimization (Phase 276-315)

I/O-focused audit commands:

- `./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit.json --out-md tmp/data-io-audit/data_source_audit.md`
- `./.venv-qlib313/bin/python cajas/scripts/audit_io_runtime.py --project-root cajas --tmp-root tmp --out-json tmp/io-runtime-audit/io_runtime_audit.json --out-md tmp/io-runtime-audit/io_runtime_audit.md`

Large CSV metadata/manifest:

- `./.venv-qlib313/bin/python cajas/scripts/inspect_large_csv.py --input "/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv" --out tmp/data-io-audit/eurusd_2020_2024_metadata.json --sample-lines 100`
- `./.venv-qlib313/bin/python cajas/scripts/build_dataset_file_manifest.py --data-root /home/phiner/projects/research/data --pattern "EURUSD_15 Mins_Bid_*.csv" --out tmp/data-io-audit/eurusd_dataset_manifest.json`

Validation guardrails:

- fast validation and micro smoke do not read real data by default
- enable real-data mode explicitly with `--include-real-data`
- large real-data scans require explicit `--allow-large-data`

## Full-Read CSV Refactor (Phase 316-345)

Key updates:

- Added CSV loading policy guardrails: `cajas/data_io/csv_loading_policy.py`.
- High-risk CSV entrypoints now support policy controls:
  - `--row-limit`
  - `--chunk-size`
  - `--sample-only`
  - `--allow-large-data`
- Updated refactor plan:
  - `cajas/docs/full_read_csv_refactor_plan.md`

Current audit delta:

- `reads_full_csv_likely_count`: `25 -> 20`
- `chunking_support_count`: `7 -> 13`

## Final Delivery References

- Final validation/data-I/O workflow index:
  - `cajas/docs/final_research_stack_index.md`
- Future work checklist:
  - `cajas/docs/future_work_checklist.md`
- PR readiness checklist:
  - `cajas/docs/pr_readiness_checklist.md`
- Final phase archive index:
  - `cajas/docs/final_phase_archive_index.md`
- Post-merge next workstream plan:
  - `cajas/docs/post_merge_next_workstream_plan.md`
- Next implementation prompt:
  - `tasks/phase_746_775_dataset_quality_feature_research_prompt.md`
- Validation delivery packet builder:
  - `./.venv-qlib313/bin/python cajas/scripts/build_validation_delivery_packet.py --fast-timing tmp/validation-runtime-audit/fast_validation_phase566.json --data-source-audit tmp/data-io-audit/data_source_audit_phase566.json --runtime-audit tmp/validation-runtime-audit/validation_runtime_phase566.json --out-json tmp/validation-delivery/validation_delivery_packet.json --out-md tmp/validation-delivery/validation_delivery_packet.md --allow-missing-inputs`


### Phase 1136–1165: Validation Timing Granularity and Delivery Packet Integration
- Distinguished required vs optional runtime budget components
- Updated budget checker to only warn for missing required components
- Enhanced budget reports with component type classification (🔴 required vs optional)
- Integrated runtime budget status into validation delivery packets
- Added test for optional components not causing warnings
- Runtime budget status now **pass** (previously warn due to missing optional timings)
- Fast validation: ~84.03s (376 tests, +1 from Phase 1106)
- Reduced noise in runtime budget reporting


### Phase 1166–1195: Automated Validation Review Bundle Workflow
- Created orchestration CLI to build complete validation review bundles
- Coordinates smoke → timing → budget → diff → manifest → audit → packet
- Safe execution modes with explicit opt-in for expensive operations
- Generates bundle manifest and index with execution record
- Integrates delivery packet as subdirectory
- Added 6 tests covering orchestration logic
- Fast validation: ~103.70s (382 tests, +6 from Phase 1136)
- Single command to generate reviewer-ready bundle


### Phase 1196–1225: Fast Validation Runtime Optimization and Tier Split
- Optimized review bundle tests by mocking subprocess calls
- Review bundle tests: 12.97s → 0.22s (58x speedup)
- Fast validation: 111.73s → 97.66s (14.07s improvement)
- Runtime budget status: warn → **pass** ✅
- Back under 105s budget without weakening coverage
- No tier split needed - optimization alone sufficient
- Data-source audit: stable at read_csv_count=29


### Phase 1226–1255: Validation Review Bundle History and Trend Tracking
- Added lightweight historical tracking for validation review bundles
- Created JSONL-based snapshot history with key validation metrics
- Built history update CLI with regression detection
- Detects status regressions, runtime increases, count changes
- Generates reviewer-friendly Markdown summaries
- Added 8 tests covering history tracking (2.16s, no subprocess calls)
- Fast validation: ~90.11s (390 tests, +8 from Phase 1196)
- No impact on fast validation runtime


### Phase 1256–1285: Integrated Review Bundle History Workflow
- Integrated optional history update into `build_validation_review_bundle.py`
- Added `--update-history`, `--history-jsonl`, `--history-last-n` flags
- Reused history module directly (no subprocess history update step)
- Extended `review_bundle_manifest.json` with `history_update` section
- Extended `review_bundle_index.md` with history paths, deltas, regressions, and recommendation
- Preserved default behavior when history update is not requested
- Added conservative failure policy:
  - history requested + failure => fail by default
  - with `--warn-only` => record warning and continue
- Expanded review bundle tests for integrated history workflow and failure modes


### Phase 1286–1315: Review Bundle Index Polish and History Delta Readability
- Polished `review_bundle_index.md` history output for reviewer readability
- Replaced raw dict-style delta text with human-readable runtime delta table
- Added compact `History Summary` section in bundle index
- Added stable `history` fields in `review_bundle_manifest.json` while preserving existing `history_update` compatibility
- Kept semantics unchanged (readability-only improvement)


### Phase 1316–1345: Review Bundle History Field Standardization and Compatibility
- Standardized `history` as canonical review bundle manifest metadata
- Added normalization helper to read either canonical `history` or legacy `history_update`
- Kept `history_update` as deprecated compatibility alias with explicit deprecation markers
- Updated index rendering to consume normalized canonical history metadata
- No new workflow semantics; compatibility and contract cleanup only
