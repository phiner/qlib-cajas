# cajas research layer for qlib-cajas

`cajas/` is the independent research layer in this `qlib-cajas` fork.

## Goal

Qlib-based Market Recognition Research for FX K-line data.

Current focus:
- EURUSD 15m K-line market recognition research

Current scope is research-only and is **not** a trading system.

## Maintenance Mode (Phase 4166-4525)

Current maintenance posture is routine/frozen for offline validation governance:

- External consumer evidence governance is closed or external-tracking-only non-blocking context.
- Final maintenance archive closure and post-freeze handoff seal are generated reviewer artifacts.
- Canonical manifest contract remains `history` only (`history_update` alias emission stays removed).
- Legacy read normalization remains preserved for historical compatibility.
- Release readiness remains `ready`, final reviewer packet remains `ready_for_review`, milestone remains non-blocking ready-for-review context.

Routine regeneration commands:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_validation_external_consumer_evidence_closure.py --out-json tmp/validation-external-consumer-evidence-closure.json --out-md tmp/validation-external-consumer-evidence-closure.md
./.venv-qlib313/bin/python cajas/scripts/build_validation_final_maintenance_archive_closure.py --out-json tmp/validation-final-maintenance-archive-closure.json --out-md tmp/validation-final-maintenance-archive-closure.md
./.venv-qlib313/bin/python cajas/scripts/build_validation_post_freeze_handoff_seal.py --out-json tmp/validation-post-freeze-handoff-seal.json --out-md tmp/validation-post-freeze-handoff-seal.md
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_routine_release_cycle_stability.py --release-readiness-report tmp/validation-release-readiness.json --final-reviewer-packet tmp/validation-final-reviewer-packet.json --milestone-packet tmp/validation-milestone-packet.json --runtime-budget-report tmp/validation_runtime_budget_report.json --runtime-edge-report tmp/validation-runtime-edge-report.json --runtime-release-cycle-report tmp/validation-runtime-release-cycle-report.json --runtime-variance-closure-report tmp/validation-runtime-variance-closure.json --data-source-audit-report tmp/data_source_audit.json --maintenance-checklist tmp/validation-maintenance-checklist.json --maintenance-governance-closure tmp/validation-maintenance-governance-closure.json --final-maintenance-archive-closure-report tmp/validation-final-maintenance-archive-closure.json --external-consumer-evidence-closure-report tmp/validation-external-consumer-evidence-closure.json --post-freeze-handoff-seal-report tmp/validation-post-freeze-handoff-seal.json --optional-followups tmp/validation-optional-followups.json --out-json tmp/validation-routine-release-cycle-stability.json --out-md tmp/validation-routine-release-cycle-stability.md
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_routine_stability_watch_closure.py --routine-release-cycle-stability-report tmp/validation-routine-release-cycle-stability.json --release-readiness-report tmp/validation-release-readiness.json --final-reviewer-packet tmp/validation-final-reviewer-packet.json --milestone-packet tmp/validation-milestone-packet.json --optional-followups-report tmp/validation-optional-followups.json --out-json tmp/validation-routine-stability-watch-closure.json --out-md tmp/validation-routine-stability-watch-closure.md
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_final_maintenance_handoff.py --branch phase-post-merge-research-next --release-readiness-report tmp/validation-release-readiness.json --final-reviewer-packet tmp/validation-final-reviewer-packet.json --milestone-packet tmp/validation-milestone-packet.json --routine-stability-watch-closure tmp/validation-routine-stability-watch-closure.json --post-freeze-handoff-seal-report tmp/validation-post-freeze-handoff-seal.json --final-maintenance-archive-closure-report tmp/validation-final-maintenance-archive-closure.json --external-consumer-evidence-closure-report tmp/validation-external-consumer-evidence-closure.json --alias-post-removal-closure-report tmp/alias-post-removal-closure.json --optional-followups-report tmp/validation-optional-followups.json --out-json tmp/validation-final-maintenance-handoff.json --out-md tmp/validation-final-maintenance-handoff.md
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_post_merge_mainline.py --branch main --source-branch phase-post-merge-research-next --merge-confirmed --release-readiness-report tmp/validation-release-readiness.json --final-reviewer-packet tmp/validation-final-reviewer-packet.json --final-maintenance-handoff-report tmp/validation-final-maintenance-handoff.json --milestone-packet tmp/validation-milestone-packet.json --routine-stability-watch-closure-report tmp/validation-routine-stability-watch-closure.json --optional-followups-report tmp/validation-optional-followups.json --alias-post-removal-closure-report tmp/alias-post-removal-closure.json --review-bundle-manifest tmp/validation-review-bundle/review_bundle_manifest.json --fast-validation-timing-json tmp/fast_validation_latest.json --out-json tmp/validation-post-merge-mainline.json --out-md tmp/validation-post-merge-mainline.md
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_routine_maintenance_continuation.py --post-merge-mainline-report tmp/validation-post-merge-mainline.json --release-readiness-report tmp/validation-release-readiness.json --final-reviewer-packet tmp/validation-final-reviewer-packet.json --milestone-packet tmp/validation-milestone-packet.json --optional-followups-report tmp/validation-optional-followups.json --alias-post-removal-closure-report tmp/alias-post-removal-closure.json --out-json tmp/validation-routine-maintenance-continuation.json --out-md tmp/validation-routine-maintenance-continuation.md
```

Watch-closure semantics:
- Routine stability may stay `watch` while release readiness remains `ready` when watch closure is `closed_non_blocking`.
- Remaining `slow_test_optimization` followup is maintenance-only and non-blocking.

Manual merge policy:
- Final maintenance handoff is review-only and requires manual GitHub merge by a human reviewer.
- Do not run automated merge operations from Codex or local scripts.

Post-merge baseline:
- After manual GitHub merge, run post-merge mainline validation and continue routine maintenance cadence.
- Routine continuation now records frozen repository posture for this cycle: fork kept, no upstream sync planned, no repo migration planned, and manual GitHub merge policy unchanged.

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

## Phase 3086-3205: Controlled Apply Readiness and Alias Fallback Removal Scheduling

- Added controlled canonical evidence apply hardening for:
  - `cajas/scripts/apply_canonical_evidence_update.py`
  - `cajas/reports/validation_canonical_evidence_apply.py`
- In apply mode, the target is the explicit `--out-evidence` path.
- This phase uses controlled target apply under:
  - `tmp/applied-canonical-evidence/history_alias_external_consumers.json`
- Added applied readiness report:
  - `cajas/reports/validation_applied_evidence_readiness.py`
  - `cajas/scripts/build_applied_evidence_readiness_report.py`
- Added alias fallback removal scheduling-readiness packet:
  - `cajas/reports/validation_alias_fallback_removal_readiness.py`
  - `cajas/scripts/build_alias_fallback_removal_readiness.py`
- Integrated both into release readiness and milestone packet builders.

Current outcome snapshot:
- applied readiness: `ready_for_real_apply`
- fallback removal readiness: `ready_to_schedule`
- real release readiness: `watch`
- real milestone: `watch`

Safety constraints:
- manual real apply remains required
- fallback alias removal remains out of scope for this phase
- no Qlib core modification
- offline validation only (no trading/broker/live execution)
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


### Phase 1346–1375: Canonical History Consumer Migration Guard
- Audited internal `history_update` consumer paths and routed consumers through canonical helper path
- Added shared utility `cajas/reports/validation_review_bundle_metadata.py`
- Added compatibility warnings helper for canonical/legacy mismatch detection
- Added `check_review_bundle_manifest_compatibility.py` for manifest compatibility reporting
- Retained `history_update` only as deprecated compatibility alias for migration window


### Phase 1376–1405: Integrated Manifest Compatibility Report in Review Bundle Workflow
- Integrated optional manifest compatibility report generation into review bundle builder
- Added manifest compatibility metadata section to bundle manifest and index
- Preserved default behavior when compatibility check flag is not used
- Reused existing canonical/compatibility helpers directly without subprocess overhead


### Phase 1406–1435: Manifest Compatibility Severity and Bundle Gating
- Added explicit compatibility severities and status model: `pass|warn|fail`
- Added severity counts and issue list to compatibility report
- Updated compatibility CLI exit behavior and added `--fail-on-warn`
- Added review bundle compatibility gating: fail status raises unless `--warn-only`
- Kept canonical `history` contract and deprecated `history_update` compatibility window


## Phase 1436–1465 Addendum: Fast Validation Timing Freshness and Consistency Guard

- Added timing freshness metadata to fast validation timing JSON:
  - `created_at`, `run_id`, `command`, `timing_source`
- Added timing consistency assessment to runtime budget reporting with `pass|warn|fail` semantics.
- Runtime budget reports now include a `timing_consistency` section in JSON/Markdown outputs.
- Review bundle workflow now records timing consistency status in manifest/index and gates failure-level consistency unless `--warn-only`.
- This improves reviewer confidence that budget checks are using fresh, internally consistent timing inputs.


## Phase 1466–1525 Addendum: CI-Friendly Validation Automation Bundle

- Added CI-oriented gate aggregation for validation review bundles.
- Added final status artifacts (`final_status.json`, `final_status.md`) with machine-readable gate-level outcomes.
- Added `--ci` workflow mode with explicit skip/fail behavior controls (`--fail-on-warn`, skip flags, timing-age control).
- Review bundle index now starts with an overall status and CI gate summary table.
- Timing freshness/consistency remains integrated through runtime budget reporting and is surfaced in final status.


## Phase 1526–1585 Addendum: CI Gate Explainability and Warn Reduction

- Added explicit gate reason/action fields for reviewer and CI explainability.
- Added profile-aware final status aggregation (`local|ci|strict`) to reduce noisy warnings in local workflows.
- Hardened final status artifact schema with run metadata and structured reason sections.
- Final status markdown now highlights primary reason, reviewer next action, and primary artifact.


## Phase 1586–1645 Addendum: CI Profile Policy Externalization, Runtime Variance Margin, and Final-Reason Selection

- Added external CI profile policy config: `cajas/data_examples/validation_ci_profiles.json`.
- Added `--ci-profile-config` to `build_validation_review_bundle.py` for policy loading without editing Python constants.
- Final status now includes:
  - `profile_policy` (source + active policy booleans)
  - per-gate `escalated` and `profile_effect`
  - prioritized `overall_reason_code`
- Review bundle index now starts with profile-aware escalation summary:
  - escalated gate count
  - non-escalated warning gate count
  - primary artifact and reviewer next action
- Runtime budget configuration now supports variance margins:
  - `warn_margin_seconds` (per component)
  - `global_warn_margin_seconds`
- Runtime budget report now includes per-component:
  - `reason_code` (`within_budget`, `within_variance_margin`, `over_budget_warn`, `over_budget_fail`, `missing_required_timing`)
  - `warn_margin_seconds`
- Runtime variance handling improves explainability without weakening required gate semantics.


## Phase 1646–1705 Addendum: Runtime Utility Budget Calibration and Final-Status Recovery

- Audited runtime budget components into two classes:
  - core: `fast_total`, `pytest_fast`
  - utility: `path_hygiene`, `compileall`, `init_py_find`, `git_init_py_check`, and other optional checks
- Calibrated `path_hygiene` budget from `5.0s` to `12.0s` with `warn_margin_seconds.path_hygiene=2.0`.
- Added `component_categories` in `validation_runtime_budgets.json` for explicit core vs utility semantics.
- Runtime budget aggregation now treats utility over-budget failures as overall `warn` instead of `fail` unless core required components fail.
- Added per-component runtime output fields:
  - `category`
  - `action`
- Action guidance now differentiates:
  - utility: `review_utility_budget` / `optimize_utility_step`
  - core: `optimize_tests`
- Local-profile CI review-bundle final status recovers from false fail caused by unrealistic utility budget.


## Phase 1766–1825 Addendum: CI Profile Matrix Validation and Automation Presets

- Added Profile Matrix generator to compare `local`, `ci`, and `strict` gate behavior side-by-side.
- Added `--preset` parameter to review bundle builder (`local_review`, `ci_required`, `strict_release`).
- Embedded profile matrix summary into `review_bundle_index.md`.

- Audited delivery packet warning root cause:
  - optional artifacts that were not explicitly requested were counted as missing warnings
  - final status could remain `pass` while reason code pointed to `delivery_packet_warn`
- Delivery packet behavior now distinguishes:
  - required missing artifacts (fail)
  - optional missing artifacts with explicit path input (warn)
  - optional artifacts not requested by this run (note/info, non-escalated)
- Added packet summary counters:
  - `required_present_count`
  - `required_missing_count`
  - `optional_present_count`
  - `optional_missing_count`
  - `optional_note_count`
- Final status reasoning for pass cases improved:
  - `pass_with_non_escalated_warnings` when optional warnings exist but do not escalate
  - `all_required_gates_passed` for clean pass
- Primary artifact selection for pass now points to reviewer-friendly summaries:
  - `review_bundle_index.md` for pass with notes
  - `final_status.md` for clean pass


## Phase 1766–1825 Recovery Addendum: Validation Closure and Test Repair

- Completed recovery closure for partially implemented profile-matrix/preset work.
- Validation environment standardized on `./.venv-qlib313/bin/python` for this phase.
- Repaired numeric sanitizer compatibility across pandas/numpy variants:
  - `to_numpy(..., copy=True)` to avoid read-only array assignment failures.
- Repaired feature-importance summary test behavior for stale local run directories:
  - test now skips when run dir exists but has zero usable artifacts.
- Hardened profile matrix implementation:
  - removed dependency on private gate-summary helpers
  - aligned reason-code handling with current final-status pass/warn semantics
- Profile matrix CLI artifacts are generated and linked from review bundle outputs.


## Phase 1826–1885 Addendum: Manifest Compatibility Closure and Audit Schema Normalization

- Root cause of manifest compatibility fail:
  - canonical `history.status` used `pass|warn|fail`
  - legacy alias `history_update.status` still used `ok` on success
  - compatibility gate correctly flagged `canonical_legacy_status_mismatch`
- Compatibility repair:
  - synchronized `history_update.status` with canonical status semantics
  - preserved strict compatibility failure behavior for real malformed manifests
- Data-source audit schema normalization:
  - review-bundle consumer now supports both:
    - top-level `read_csv_count`
    - nested `summary.read_csv_count`
- Result:
  - manifest compatibility gate recovers to `pass` for healthy generated bundles
  - runtime budget and timing consistency remain `pass`
  - profile matrix no longer fails all profiles due to manifest compatibility mismatch

## Phase 1886-1945 Addendum: History Alias Deprecation and Strict Profile Warning Clarity

- Added explicit deprecation metadata for compatibility alias `history_update`:
  - `deprecation_stage=compatibility_alias`
  - `removal_target_phase=future`
  - `consumer_action=Read manifest.history instead.`
- Added `--omit-history-update-alias` to `build_validation_review_bundle.py`:
  - default keeps compatibility alias
  - optional mode emits canonical `history` only
- Compatibility expectations now covered by tests:
  - canonical-only `history`: `pass`
  - canonical `history` + synchronized alias: `pass`
  - legacy-only alias fallback: `warn`
  - canonical/alias mismatch: `fail`
- Strict-profile outputs now explicitly explain expected warn behavior:
  - `strict_warning_reason=optional_not_run_or_warn_escalated_by_strict_policy`
  - `profile_matrix.md` includes `Strict Warning Note` when strict is `warn` with zero blocking gates

Example canonical-only run:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_review_bundle.py \
  --ci \
  --ci-profile local \
  --ci-profile-config cajas/data_examples/validation_ci_profiles.json \
  --bundle-name dataset_quality_review_bundle_no_alias \
  --out-root tmp/validation-review-bundle-no-alias \
  --smoke-root tmp/dataset-quality-smoke \
  --fast-timing-json tmp/fast_validation_latest.json \
  --budgets cajas/data_examples/validation_runtime_budgets.json \
  --create-baseline-from-current \
  --update-history \
  --history-jsonl tmp/validation-review-bundle-no-alias/history/review_bundle_history.jsonl \
  --history-last-n 10 \
  --check-manifest-compatibility \
  --warn-only \
  --omit-history-update-alias
```

## Phase 1946-2005 Addendum: Default No-Alias Migration Readiness and Preset Regression

- Added history alias migration readiness report module and CLI:
  - `cajas/reports/validation_history_alias_migration.py`
  - `cajas/scripts/build_history_alias_migration_report.py`
- Readiness report compares default alias bundle vs canonical-only no-alias bundle and evaluates:
  - manifest compatibility
  - local/ci/strict profile status equivalence
  - required gate equivalence
  - optional gate differences
- Preset behavior hardening:
  - explicit CLI flags now override preset defaults
  - presets remain available: `local_review`, `ci_required`, `strict_release`
- Current readiness result (`tmp/history-alias-migration-readiness.json`):
  - `status=pass`
  - `recommendation=ready_for_default_no_alias_trial`
  - default/no-alias profile outcomes equivalent (`local=pass`, `ci=pass`, `strict=warn`)

Known limitation:
- Recommendation is for a controlled future default-flip phase; this phase does not flip default alias behavior.

## Phase 2006-2065 Addendum: Controlled Default No-Alias Trial and Compatibility Fallback

- Default generated review-bundle manifests now emit canonical `history` only.
- Added explicit fallback flag `--include-history-update-alias` to emit deprecated alias metadata when needed.
- Retained `--omit-history-update-alias` as compatibility/no-op transition flag.
- Compatibility checker semantics unchanged:
  - canonical-only: pass
  - canonical + alias synced: pass
  - legacy-only: warn
  - mismatch/malformed alias: fail
- Consumer final check (`tmp/history_alias_consumer_scan.txt`) shows active internal consumers already rely on canonical path or compatibility normalization (`normalize_history_metadata`).
- Current trial readiness remains `pass` with recommendation `ready_for_default_no_alias_trial`.

## Phase 2066-2125 Addendum: Alias Fallback Sunset Guard and Runtime Edge Stabilization

- Added hard no-alias regression guard coverage in review-bundle tests:
  - default manifest remains canonical-only (`history`)
  - fallback alias requires `--include-history-update-alias`
  - transition `--omit-history-update-alias` remains accepted/no-op
- Extended migration readiness output with `alias_fallback` block:
  - fallback flag, alias presence checks, deprecation metadata visibility, sunset recommendation
- Added runtime edge risk report:
  - `cajas/reports/validation_runtime_edge.py`
  - `cajas/scripts/build_validation_runtime_edge_report.py`
  - outputs `tmp/validation-runtime-edge-report.json|md`
- Runtime edge report is reviewer-facing and does not replace runtime budget pass/fail gate.

## Phase 2126-2185 Addendum: Phase 2000+ Milestone Review Packet

- Added milestone packet report and CLI:
  - `cajas/reports/validation_milestone_packet.py`
  - `cajas/scripts/build_validation_milestone_packet.py`
- Milestone packet consolidates operating model, artifact map, gate/profile/runtime/alias state, risks, and next actions.
- Generated outputs:
  - `tmp/validation-milestone-packet.json`
  - `tmp/validation-milestone-packet.md`
- Latest milestone packet status: `pass`.

## Phase 2186-2245 Addendum: Alias Sunset Review and Runtime Release-Cycle Monitoring

- Added alias sunset review module + CLI:
  - `cajas/reports/validation_alias_sunset_review.py`
  - `cajas/scripts/build_alias_sunset_review.py`
- Added runtime release-cycle monitor module + CLI:
  - `cajas/reports/validation_runtime_release_cycle.py`
  - `cajas/scripts/build_validation_runtime_release_cycle_report.py`
- Added milestone packet optional integration for:
  - `--alias-sunset-review`
  - `--runtime-release-cycle-report`
- Current alias sunset review result (`external-consumer-status=unknown`): `watch`, action `keep_fallback`.
- Current runtime release-cycle result: `pass`, recommendation `ok`.

## Phase 2246-2305 Addendum: Consumer Evidence Intake and Runtime Variance Triage

- Added external consumer evidence example:
  - `cajas/data_examples/history_alias_external_consumers.json`
- Extended alias sunset review to ingest consumer evidence:
  - `cajas/reports/validation_alias_sunset_review.py`
  - `cajas/scripts/build_alias_sunset_review.py`
- Alias sunset precedence:
  - explicit `--external-consumer-status` overrides evidence file status for the current run
- Alias sunset evidence summary now includes:
  - `evidence_source`
  - `consumers`
  - `requires_alias_count`
  - `confirmed_clear_count`
  - `unresolved_count`
- Added runtime variance triage report + CLI:
  - `cajas/reports/validation_runtime_variance.py`
  - `cajas/scripts/build_validation_runtime_variance_report.py`
- Runtime variance status rules:
  - `fail`: runtime budget/timing consistency fail
  - `warn`: runtime budget warns
  - `watch`: material delta over configured threshold (default 10%) with budget pass
  - `pass`: budget/timing pass and deltas below watch threshold
- Integrated runtime variance into release-cycle monitor:
  - `cajas/reports/validation_runtime_release_cycle.py`
  - `cajas/scripts/build_validation_runtime_release_cycle_report.py`
- Integrated alias evidence + runtime variance into milestone packet:
  - `cajas/reports/validation_milestone_packet.py`
  - `cajas/scripts/build_validation_milestone_packet.py`

Current outputs:
- alias sunset review: `tmp/history-alias-sunset-review.json|md`
- runtime variance report: `tmp/validation-runtime-variance-report.json|md`
- runtime release-cycle report: `tmp/validation-runtime-release-cycle-report.json|md`
- milestone packet: `tmp/validation-milestone-packet.json|md`

Current status snapshot:
- alias sunset review: `watch`, action `keep_fallback` (external consumer unresolved)
- runtime variance: `pass` (`88.806s`, below 10% watch threshold vs baselines)
- runtime release-cycle: `pass`, recommendation `ok`
- milestone overall: `watch` (driven by alias sunset watch)

Scope confirmation:
- Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 3026-3085 Addendum: Canonical Evidence Apply Dry-Run Guard

- Added guarded apply workflow:
  - `cajas/reports/validation_canonical_evidence_apply.py`
  - `cajas/scripts/apply_canonical_evidence_update.py`
  - output:
    - `tmp/canonical-evidence-apply-dry-run.json`
    - `tmp/canonical-evidence-apply-dry-run.md`
- Guard behavior:
  - defaults to dry-run/non-destructive behavior.
  - requires approved approval + ready update plan + valid candidate before dry-run-ready/apply.
  - includes backup/rollback instructions and post-apply validation command checklist.
  - `alias_fallback_removal_allowed=false` in this phase.
- Readiness/milestone integration:
  - `--canonical-evidence-apply-report` optional input added to both report builders.

Current status snapshot:
- apply dry-run report: `dry_run_ready`
- real release readiness: `watch`
- real milestone packet: `watch`

Runtime snapshot:
- fast validation total: `55.92s`
- runtime budget overall: `pass`
- timing consistency: `pass`

Scope confirmation:
- Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2966-3025 Addendum: Approved Simulation and Canonical Evidence Update Plan

- Added approved simulation approval example:
  - `cajas/data_examples/history_alias_evidence_candidate_approval.approved.example.json`
  - explicitly marked `approval_scope=simulation_only`.
- Added canonical evidence update planning report:
  - `cajas/reports/validation_canonical_evidence_update_plan.py`
  - `cajas/scripts/build_canonical_evidence_update_plan.py`
  - outputs:
    - `tmp/canonical-evidence-update-plan.json`
    - `tmp/canonical-evidence-update-plan.md`
- Added readiness/milestone optional integration:
  - `--canonical-evidence-update-plan`
- Approved simulation outputs:
  - `tmp/simulated-approved/evidence-candidate-approval-report.json|md`
  - `tmp/simulated-approved/history-alias-sunset-schedule.json|md`

Current status snapshot:
- real approval gate: `approval_required` (real path still unapproved)
- approved simulation gate: `approved_candidate`
- approved simulation schedule: `ready_to_schedule`
- canonical update plan: `ready_to_apply` with `manual_update_required=true` and `do_not_auto_apply=true`
- real release readiness remains `watch`
- real milestone remains `watch`

Runtime snapshot:
- fast validation total: `53.22s`
- runtime budget overall: `pass`
- timing consistency: `pass`

Scope confirmation:
- Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2906-2965 Addendum: Evidence Approval Gate and Sunset Scheduling Packet

- Added evidence candidate approval gate:
  - `cajas/reports/validation_evidence_candidate_approval.py`
  - `cajas/scripts/build_evidence_candidate_approval_report.py`
  - `cajas/data_examples/history_alias_evidence_candidate_approval.example.json` (default `approved=false`)
- Added alias sunset scheduling packet:
  - `cajas/reports/validation_alias_sunset_schedule.py`
  - `cajas/scripts/build_alias_sunset_schedule.py`
- Added readiness/milestone optional integrations:
  - `--evidence-candidate-approval-report`
  - `--alias-sunset-schedule`
- Current approval/schedule state:
  - approval report: `approval_required`
  - schedule packet: `not_scheduled`
  - real release readiness: `watch`
  - real milestone packet: `watch`
- Runtime snapshot:
  - fast validation total: `52.646s`
  - runtime budget overall: `pass`
  - timing consistency: `pass`

Scope confirmation:
- Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2846-2905 Addendum: Confirmed-Clear Candidate Review and Evidence Apply Dry-Run

- Added confirmed-clear simulation owner response example:
  - `cajas/data_examples/history_alias_consumer_owner_response.confirmed_clear.example.json`
  - explicitly marked as example-only, not production evidence.
- Hardened owner response apply-dry-run metadata:
  - validator now reports `candidate_written`, `candidate_output_path`, `manual_approval_required`, `do_not_auto_apply`.
  - `--apply-to-out` writes a candidate only for valid responses.
  - candidate keeps untouched consumers and adds candidate provenance metadata.
- Added candidate-readiness simulation report:
  - `cajas/reports/validation_consumer_evidence_candidate.py`
  - `cajas/scripts/build_consumer_evidence_candidate_report.py`
  - output: `tmp/simulated-confirmed-clear/history-alias-consumer-evidence-candidate.json|md`
- Added optional candidate summary integration:
  - release readiness supports `--consumer-evidence-candidate-report`
  - milestone packet supports `--consumer-evidence-candidate-report`
  - real readiness remains based on real evidence (`watch`) while surfacing candidate projection.

Current real vs simulated status snapshot:
- real owner response validation: `incomplete`, `safe_to_update_evidence=false`
- simulated confirmed-clear validation: `valid_ready_to_apply`, `candidate_written=true`
- candidate simulation status: `ready_candidate`, `release_readiness_projected_status=ready`
- real release readiness: `watch`
- real milestone packet overall: `watch`

Runtime snapshot:
- fast validation total: `56.757s`
- runtime budget overall: `pass`
- timing consistency: `pass`

Scope confirmation:
- Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2306-2365 Addendum: Alias Sunset Decision Gate and Release Readiness Dashboard

- Added external consumer confirmation template:
  - `cajas/data_examples/history_alias_external_consumers.template.json`
- Strengthened alias sunset review with decision-gate output:
  - `decision_gate.status`: `blocked|watch|ready`
  - `required_evidence_complete`
  - `unresolved_consumers`
  - `consumers_requiring_alias`
  - `ready_conditions`
  - `blocking_conditions`
  - `next_actions`
- Alias sunset action semantics now distinguish:
  - `collect_consumer_evidence` for unresolved/watch evidence
  - `migrate_consumers` when alias dependency is confirmed
  - `schedule_removal` only when ready conditions are satisfied
- Added release-readiness dashboard report + CLI:
  - `cajas/reports/validation_release_readiness.py`
  - `cajas/scripts/build_validation_release_readiness_report.py`
- Release-readiness status rules:
  - `blocked`: any required gate fails or alias decision gate blocked
  - `watch`: alias watch or runtime watch/warn conditions
  - `ready`: required gates pass and alias decision gate ready
- Integrated release-readiness summary into milestone packet:
  - `--release-readiness-report`
  - milestone markdown now includes readiness status/reason/next actions

Current outputs:
- alias sunset review: `tmp/history-alias-sunset-review.json|md`
- release readiness dashboard: `tmp/validation-release-readiness.json|md`
- runtime variance report: `tmp/validation-runtime-variance-report.json|md`
- runtime release-cycle report: `tmp/validation-runtime-release-cycle-report.json|md`
- milestone packet: `tmp/validation-milestone-packet.json|md`

Current status snapshot:
- alias sunset decision gate: `watch`, action `collect_consumer_evidence`
- release readiness: `watch`, reason `alias_sunset_decision_gate=watch`
- runtime variance: `pass` (`88.472s`; vs phase_2126 `-0.166s`, vs phase_2186 `-8.400s`)
- runtime release-cycle: `pass`, recommendation `ok`
- milestone overall: `watch` with actionable release-readiness next actions

Known limitations:
- Alias fallback sunset remains deferred until unresolved external consumers are confirmed clear.
- Runtime health is pass in this cycle but remains a release-cycle monitoring input.

Scope confirmation:
- Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2366-2425 Addendum: External Consumer Evidence Closure and Alias Removal Plan Packet

- Added confirmed-clear simulation evidence example:
  - `cajas/data_examples/history_alias_external_consumers.confirmed_clear.example.json`
  - explicitly marked as simulation/example only, not real clearance.
- Added alias removal plan report + CLI:
  - `cajas/reports/validation_alias_removal_plan.py`
  - `cajas/scripts/build_alias_removal_plan.py`
- Removal plan output covers:
  - `status`: `not_ready|ready_to_schedule|blocked`
  - preconditions and blockers
  - future removal steps
  - explicit non-goal note (no fallback removal in this phase)
- Extended release-readiness dashboard integration:
  - optional `--alias-removal-plan`
  - includes removal-plan status/recommendation/blockers as watch context
- Extended milestone packet integration:
  - optional `--alias-removal-plan`
  - includes removal-plan summary block in packet JSON/Markdown

Real current outputs:
- alias removal plan: `tmp/history-alias-removal-plan.json|md`
- release readiness: `tmp/validation-release-readiness.json|md`
- milestone packet: `tmp/validation-milestone-packet.json|md`

Simulated confirmed-clear outputs:
- `tmp/simulated-confirmed-clear/history-alias-sunset-review.json|md`
- `tmp/simulated-confirmed-clear/history-alias-removal-plan.json|md`

Current status snapshot:
- real alias sunset: `watch` (unresolved external consumer remains)
- real removal plan: `not_ready`, recommendation `keep_fallback`
- real release readiness: `watch`
- simulated alias sunset: `ready`
- simulated removal plan: `ready_to_schedule`

Runtime snapshot (latest fast run):
- fast validation total: `94.03s`
- runtime budget: `pass`
- runtime edge: `watch`
- runtime release-cycle: `watch`
- runtime variance: `pass`

Scope confirmation:
- Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2426-2485 Addendum: Real Consumer Evidence Closure and Runtime Watch Triage

- Extended real consumer evidence tracking in:
  - `cajas/data_examples/history_alias_external_consumers.json`
  - fields now include `review_owner`, `last_checked`, `next_action`, `due_phase`.
- Added consumer evidence closure report + CLI:
  - `cajas/reports/validation_consumer_evidence_closure.py`
  - `cajas/scripts/build_consumer_evidence_closure_report.py`
- Added runtime watch triage report + CLI:
  - `cajas/reports/validation_runtime_watch_triage.py`
  - `cajas/scripts/build_validation_runtime_watch_triage_report.py`
- Extended release readiness optional integration:
  - `--consumer-evidence-closure-report`
  - `--runtime-watch-triage-report`
- Extended milestone packet optional integration:
  - `--consumer-evidence-closure-report`
  - `--runtime-watch-triage-report`

Current outputs:
- consumer evidence closure: `tmp/history-alias-consumer-evidence-closure.json|md`
- runtime watch triage: `tmp/validation-runtime-watch-triage-report.json|md`
- release readiness: `tmp/validation-release-readiness.json|md`
- milestone packet: `tmp/validation-milestone-packet.json|md`

Current status snapshot:
- consumer evidence closure: `incomplete` (1 unresolved consumer, next action `identify_owner`)
- alias sunset: `watch`
- alias removal plan: `not_ready`, recommendation `keep_fallback`
- runtime watch triage: `pass`, recommendation `monitor`
- runtime edge/release-cycle: both `pass` in latest run
- release readiness overall: `watch` (driven by unresolved consumer evidence, not runtime)

Runtime comparison:
- latest fast total: `88.418s`
- vs phase_2306 baseline `88.472s`: `-0.054s`
- vs phase_2366 baseline `94.03s`: `-5.612s`

Scope confirmation:
- Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2486-2545 Addendum: Consumer Owner Resolution and Timing Observability

- Updated real evidence owner/action details in:
  - `cajas/data_examples/history_alias_external_consumers.json`
  - unresolved consumer now explicitly uses:
    - `owner=external-review-needed`
    - `next_action=identify_owner`
    - `due_phase=future`
    - `blocking_alias_sunset=true`
- Extended consumer evidence closure report with action tracking:
  - `action_plan`
  - `blocking_consumer_count`
  - `owner_missing_count`
  - markdown action table
- Added fast timing test-summary extraction in:
  - `cajas/scripts/run_fast_validation.py`
  - emits `test_summary` with `passed|deselected|failed|total_reported` when parseable
- Extended runtime watch triage with test-count observability:
  - `test_count`
  - `tests_deselected`
  - `seconds_per_test`
  - `test_count_source`
- Extended readiness/milestone summaries with:
  - consumer evidence action plan
  - runtime test-count fields

Current outputs:
- consumer evidence closure: `tmp/history-alias-consumer-evidence-closure.json|md`
- runtime watch triage: `tmp/validation-runtime-watch-triage-report.json|md`
- release readiness: `tmp/validation-release-readiness.json|md`
- milestone packet: `tmp/validation-milestone-packet.json|md`

Current status snapshot:
- consumer evidence closure: `incomplete` (one blocking unresolved consumer)
- alias sunset/removal: `watch` / `not_ready`
- runtime budget: `warn` in latest run (`fast_total=109.788s`, `pytest_fast=105.537s`)
- runtime watch triage: `warn`, recommendation `optimize`
- release readiness: `watch` (evidence + runtime warn)

Known limitation:
- `test_summary` remains `null` in real runs when pytest output is not captured by the runner environment; parser remains conservative and non-failing.

Scope confirmation:
- Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2546-2605 Addendum: Pytest Fast Runtime Profiling and Summary Reliability

- Added pytest runtime profile report path:
  - `cajas/reports/validation_pytest_runtime_profile.py`
  - `cajas/scripts/profile_pytest_fast_runtime.py`
- Improved fast validation summary reliability:
  - `cajas/scripts/run_fast_validation.py` now requests subprocess output capture and expands summary fields (`passed|failed|deselected|skipped|xfailed|xpassed|errors|total_reported`).
- Extended runtime watch triage integration:
  - optional `--pytest-runtime-profile`
  - emits profile status + slowest tests/files summaries.
- Extended release readiness and milestone packet integration:
  - optional `--pytest-runtime-profile`
  - readiness/milestone now surface runtime-profile summary fields.

Current outputs:
- `tmp/validation-pytest-runtime-profile.json|md`
- `tmp/validation-runtime-watch-triage-report.json|md`
- `tmp/validation-release-readiness.json|md`
- `tmp/validation-milestone-packet.json|md`

Current runtime snapshot:
- fast validation total: `96.83s`
- pytest_fast: `92.79s`
- runtime budget: `pass`
- runtime edge: `watch`
- runtime variance: `warn` (vs older baselines)
- runtime watch triage: `watch`, recommendation `optimize_slow_tests`

Scope confirmation:
- Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2606-2665 Addendum: Targeted Pytest Runtime Optimization and Edge Recovery

- Reviewed profile artifacts:
  - `tmp/validation-pytest-runtime-profile.json|md`
  - top slowdown pattern was repeated one-test CLI subprocess launches.
- Applied safe optimization:
  - converted selected CLI smoke tests from `subprocess.run([sys.executable, ...])` to direct `main(argv)` calls.
  - updated corresponding script `main()` entrypoints to accept optional `argv` while preserving CLI behavior.
- Generated before/after profile snapshots:
  - `tmp/validation-pytest-runtime-profile-before.json|md`
  - `tmp/validation-pytest-runtime-profile.json|md`

Current runtime snapshot after optimization:
- fast validation total: `78.623s`
- pytest_fast: `73.181s`
- runtime budget: `pass`
- runtime edge: `pass`
- runtime variance: `pass`
- runtime watch triage: `pass`, recommendation `monitor`

Status impact:
- runtime edge recovered from prior `warn` to `pass`.
- release readiness remains `watch` because alias consumer evidence remains incomplete (`blocking_consumer_count=1`), not because runtime health.

Scope confirmation:
- Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2666-2725 Addendum: Runtime Optimization Round 2 and Consumer Closure Path

- Second-round profile findings (`tmp/validation-pytest-runtime-profile.json|md`):
  - top hotspot remains `test_baseline_runner`.
  - next hotspots are still mostly single-test CLI wrappers.
  - runtime/data-audit CLI tests remained meaningful contributors before this round.
- Applied safe round-2 optimization:
  - `cajas/scripts/audit_data_sources.py` and `cajas/scripts/audit_validation_runtime.py` now support `main(argv)`.
  - corresponding tests switched from subprocess launches to direct `main(argv)` invocation:
    - `cajas/tests/test_data_source_audit.py`
    - `cajas/tests/test_validation_runtime_audit.py`
  - validation assertions preserved; no test skip/tier downgrade.
- Consumer evidence closure path tightened:
  - `cajas/reports/validation_consumer_evidence_closure.py` now includes explicit `closure_checklist` in JSON and Markdown.
  - checklist covers owner identification, `manifest.history` dependency confirmation, alias-required migration handling, and evidence update requirements.

Current runtime snapshot:
- fast validation total: `79.427s`
- pytest_fast: `70.796s`
- runtime budget: `pass`
- timing consistency: `pass`
- runtime edge: `pass`
- runtime variance: `pass`
- runtime watch triage: `pass`

Consumer closure/readiness snapshot:
- consumer evidence closure: `incomplete` (`unresolved_count=1`, `blocking_consumer_count=1`)
- alias sunset review: `watch` (`recommended_action=collect_consumer_evidence`)
- release readiness: `watch` (evidence/alias reasons, runtime healthy)
- milestone packet: `watch`

Scope confirmation:
- Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2726-2785 Addendum: Remaining CLI Hotspots and Consumer Owner Handoff

- Converted remaining safe CLI wrapper hotspots to direct `main(argv)` tests:
  - `build_artifact_lineage.py`
  - `build_final_readiness_packet.py`
  - `build_final_research_bundle.py`
  - `build_candidate_promotion_manifest.py`
  - corresponding CLI tests now call `main([...])` directly.
- Baseline runner review:
  - `test_baseline_runner` still a top hotspot.
  - safe fixture optimization applied by writing compact CSV text directly (removed `pandas` fixture dependency in test setup).
  - disabled-training assertions were preserved.
- Added consumer owner handoff packet:
  - `cajas/reports/validation_consumer_owner_handoff.py`
  - `cajas/scripts/build_consumer_owner_handoff.py`
  - outputs:
    - `tmp/history-alias-consumer-owner-handoff.json`
    - `tmp/history-alias-consumer-owner-handoff.md`
- Integrated owner handoff into readiness/milestone reports:
  - release readiness optional arg `--consumer-owner-handoff`
  - milestone packet optional arg `--consumer-owner-handoff`

Current runtime snapshot:
- fast validation total: `66.579s`
- pytest_fast: `59.935s`
- runtime budget: `pass`
- timing consistency: `pass`
- runtime edge: `pass`
- runtime variance: `pass`
- runtime watch triage: `pass`

Consumer/readiness snapshot:
- owner handoff: `open` with one blocking unresolved consumer
- consumer evidence closure: `incomplete`
- alias sunset review: `watch`
- release readiness: `watch` (evidence/owner handoff reasons, not runtime)
- milestone packet: `watch`

Scope confirmation:
- Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2786-2845 Addendum: CLI-Heavy Wrapper Round and Owner Response Intake

- Converted additional CLI-heavy wrappers to direct `main(argv)` tests:
  - `train_qlib_model_bridge_baseline.py`
  - `compare_qlib_model_runs.py`
  - `build_dataset_quality_research_bundle.py`
  - `audit_io_runtime.py`
- Updated corresponding tests to direct-call mode:
  - `test_train_qlib_model_bridge_baseline_cli.py`
  - `test_compare_qlib_model_runs_cli.py`
  - `test_dataset_quality_research_bundle.py`
  - `test_io_runtime_audit.py`
- Added owner response intake schema and validation workflow:
  - example input: `cajas/data_examples/history_alias_consumer_owner_response.example.json`
  - validation module: `cajas/reports/validation_consumer_owner_response.py`
  - validation CLI: `cajas/scripts/validate_consumer_owner_response.py`
  - output:
    - `tmp/history-alias-consumer-owner-response-validation.json`
    - `tmp/history-alias-consumer-owner-response-validation.md`
- Owner response validation integrated into:
  - release readiness (`--consumer-owner-response-validation`)
  - milestone packet (`--consumer-owner-response-validation`)

Current runtime snapshot:
- fast validation total: `59.314s`
- pytest_fast: `51.599s`
- runtime budget: `pass`
- timing consistency: `pass`
- runtime edge: `pass`
- runtime variance: `pass`
- runtime watch triage: `pass`

Owner/evidence snapshot:
- owner handoff: `open` (`blocking_consumer_count=1`)
- owner response validation: `incomplete` (example response not ready to apply)
- consumer evidence closure: `incomplete`
- release readiness: `watch` (owner/evidence reasons)
- milestone packet: `watch`

Scope confirmation:
- Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 3206-3325 Alias Fallback Removal Readiness

- Active `history_update` alias emission was removed from review bundle generation.
- `--include-history-update-alias` is sunset and fails fast with a migration message.
- Canonical-only manifest output (`history`) is now enforced.
- Legacy archived manifests remain readable via `normalize_history_metadata` compatibility normalization.
- Release readiness and milestone packet now include post-removal alias status and rollback planning.
- This remains offline validation infrastructure work; not trading logic.

## Phase 3326-3445 Post-Removal Closure

- Added post-removal closure packet for canonical-only alias migration state.
- Release readiness now supersedes stale pre-removal consumer-evidence/sunset watch items when post-removal mode is active and closure/runtime/compatibility remain healthy.
- Milestone packet now includes alias post-removal closure summary.
- Legacy read normalization for archived manifests remains intentionally preserved.
- Rollback readiness remains explicit.

## Phase 3446-3565 Runtime Release-Ready Closure

- Runtime release-cycle monitor now includes structured reason codes and gate lists for blocker/watch diagnosis.
- Added final release-ready closure report and wired it into release readiness and milestone outputs.
- Runtime status now reflects fresh budget/edge/variance/watch-triage inputs rather than stale release-cycle artifacts.

## Phase 3566-3685 Runtime Variance Closure and Reviewer Finalization Packet

- Added runtime variance closure classification and artifacts:
  - `tmp/validation-runtime-variance-closure.json`
  - `tmp/validation-runtime-variance-closure.md`
- Runtime closure semantics:
  - `blocked` when runtime budget/edge/timing fails
  - `monitoring_only` when runtime gates pass but runtime variance/release-cycle remains watch
  - `closed` when all runtime gates and variance/release-cycle pass
- Updated release-ready closure semantics to separate blocker state from non-blocking monitoring follow-up:
  - when only non-blocking runtime monitoring remains, closure keeps watch status while reporting `review_state=ready_for_review` and `blocking=false`
- Added final reviewer packet:
  - `tmp/validation-final-reviewer-packet.json`
  - `tmp/validation-final-reviewer-packet.md`
- Final reviewer packet summarizes:
  - canonical-only manifest enforcement
  - alias post-removal closure state
  - preserved legacy read normalization for archived manifests
  - runtime budget/edge and runtime variance closure posture
  - data-source audit read count and remaining follow-up cadence
- Release readiness and milestone packet now include final reviewer packet status and primary artifact linkage.
- Scope remains offline Qlib validation automation only; no trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 3686-3805 Milestone Watch Governance Closure and Stable Maintenance Cadence

- Milestone `watch` reason was audited and classified as non-blocking governance carryover, not a release/runtime blocker.
- Milestone packet now provides explicit reviewer-facing semantics:
  - `review_state`
  - `blocking`
  - `blocking_reasons`
  - `non_blocking_governance_notes`
  - `superseded_watch_items`
  - `maintenance_cadence`
- Added maintenance cadence report and CLI:
  - `tmp/validation-maintenance-cadence.json`
  - `tmp/validation-maintenance-cadence.md`
- Cadence integration added to:
  - final reviewer packet
  - release readiness report
  - milestone packet
- Final reviewer packet now includes a concise reviewer handoff section with canonical policy, alias closure status, runtime summary, data-source audit stability, and next cadence action.
- Maintenance mode remains routine release-cycle monitoring with explicit command list; optional governance evidence follow-up remains non-blocking.

Scope confirmation:
- Offline Qlib validation automation only.
- No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 3806-3925 Maintenance Mode Hardening and Checklist Freeze

- Added maintenance checklist report and CLI:
  - `tmp/validation-maintenance-checklist.json`
  - `tmp/validation-maintenance-checklist.md`
- Added optional follow-up queue report and CLI:
  - `tmp/validation-optional-followups.json`
  - `tmp/validation-optional-followups.md`
- Maintenance checklist now defines:
  - routine release-cycle commands and expected pass states
  - canonical artifact freeze surface
  - generated/transient/preserved-compatibility artifact policy
  - blocking policy vs non-blocking optional follow-up handling
- Final reviewer packet, release readiness, and milestone packet now include checklist/follow-up summaries.
- Maintenance mode remains review-ready while optional queue stays explicitly non-blocking.

Scope confirmation:
- Offline Qlib validation automation only.
- No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

EURUSD 15m pattern research kickoff commands:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_dataset_contract_report.py --input "/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv" --input "/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv" --symbol EURUSD --timeframe 15m --price-side Bid --out-json tmp/validation-eurusd-dataset-contract.json --out-md tmp/validation-eurusd-dataset-contract.md
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_dataset_audit_report.py --input "/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv" --input "/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv" --out-json tmp/validation-eurusd-dataset-audit.json --out-md tmp/validation-eurusd-dataset-audit.md
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_research_readiness_report.py --base-maintenance-continuation-report tmp/validation-routine-maintenance-continuation.json --dataset-contract-report tmp/validation-eurusd-dataset-contract.json --dataset-audit-report tmp/validation-eurusd-dataset-audit.json --out-json tmp/validation-eurusd-research-readiness.json --out-md tmp/validation-eurusd-research-readiness.md
```

Policy notes:
- This track is fixed to EURUSD 15m Bid structure research.
- No 1H/4H aggregation in this phase.
- No live trading, broker routing, order generation, or Qlib core changes.

EURUSD 15m anomaly triage and clean-view commands:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_ohlc_anomaly_triage_report.py --input "/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv" --input "/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv" --symbol EURUSD --timeframe 15m --price-side Bid --output-json tmp/validation-eurusd-ohlc-anomaly-triage.json --output-md tmp/validation-eurusd-ohlc-anomaly-triage.md
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_clean_dataset_view_report.py --input "/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv" --input "/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv" --anomaly-triage-report tmp/validation-eurusd-ohlc-anomaly-triage.json --output-clean-csv tmp/eurusd/EURUSD_15m_Bid_clean_view.csv --output-quarantine-csv tmp/eurusd/EURUSD_15m_Bid_quarantined_rows.csv --output-json tmp/validation-eurusd-clean-dataset-view.json --output-md tmp/validation-eurusd-clean-dataset-view.md
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_research_readiness_report.py --base-maintenance-continuation-report tmp/validation-routine-maintenance-continuation.json --dataset-contract-report tmp/validation-eurusd-dataset-contract.json --dataset-audit-report tmp/validation-eurusd-dataset-audit.json --clean-dataset-view-report tmp/validation-eurusd-clean-dataset-view.json --out-json tmp/validation-eurusd-research-readiness.json --out-md tmp/validation-eurusd-research-readiness.md
```

Readiness rule:
- Keep raw audit status explicit (it may remain blocked).
- Pattern research can proceed only with approved clean-view status (`ready` or non-blocking `watch`).
- Raw CSV files remain immutable.

EURUSD 15m pattern candidate pack commands:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_pattern_candidate_pack.py --clean-view-csv tmp/eurusd/EURUSD_15m_Bid_clean_view.csv --output-candidates-csv tmp/eurusd/EURUSD_15m_pattern_candidates.csv --output-samples-csv tmp/eurusd/EURUSD_15m_pattern_review_samples.csv --output-samples-jsonl tmp/eurusd/EURUSD_15m_pattern_review_samples.jsonl --output-json tmp/validation-eurusd-pattern-candidate-pack.json --output-md tmp/validation-eurusd-pattern-candidate-pack.md --max-samples-per-type 50 --min-confidence 0.6
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_research_readiness_report.py --base-maintenance-continuation-report tmp/validation-routine-maintenance-continuation.json --dataset-contract-report tmp/validation-eurusd-dataset-contract.json --dataset-audit-report tmp/validation-eurusd-dataset-audit.json --clean-dataset-view-report tmp/validation-eurusd-clean-dataset-view.json --pattern-candidate-pack-report tmp/validation-eurusd-pattern-candidate-pack.json --out-json tmp/validation-eurusd-research-readiness.json --out-md tmp/validation-eurusd-research-readiness.md
```

Policy notes:
- Candidate tags are review labels, not trading signals.
- No buy/sell/order/position outputs are allowed.
- Clean view remains the approved source; raw files remain immutable.
- Scope remains EURUSD 15m Bid with no 1H/4H aggregation.

EURUSD 15m pattern review QA and label schema commands:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_pattern_review_qa_report.py --candidates-csv tmp/eurusd/EURUSD_15m_pattern_candidates.csv --samples-csv tmp/eurusd/EURUSD_15m_pattern_review_samples.csv --candidate-pack-report tmp/validation-eurusd-pattern-candidate-pack.json --clean-view-csv tmp/eurusd/EURUSD_15m_Bid_clean_view.csv --output-json tmp/validation-eurusd-pattern-review-qa.json --output-md tmp/validation-eurusd-pattern-review-qa.md
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_pattern_label_schema_report.py --output-json tmp/validation-eurusd-pattern-label-schema.json --output-md tmp/validation-eurusd-pattern-label-schema.md
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_pattern_review_template.py --samples-csv tmp/eurusd/EURUSD_15m_pattern_review_samples.csv --label-schema tmp/validation-eurusd-pattern-label-schema.json --output-template-csv tmp/eurusd/EURUSD_15m_pattern_review_template.csv --output-template-jsonl tmp/eurusd/EURUSD_15m_pattern_review_template.jsonl --output-json tmp/validation-eurusd-pattern-review-template.json --output-md tmp/validation-eurusd-pattern-review-template.md
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_research_readiness_report.py --base-maintenance-continuation-report tmp/validation-routine-maintenance-continuation.json --dataset-contract-report tmp/validation-eurusd-dataset-contract.json --dataset-audit-report tmp/validation-eurusd-dataset-audit.json --clean-dataset-view-report tmp/validation-eurusd-clean-dataset-view.json --pattern-candidate-pack-report tmp/validation-eurusd-pattern-candidate-pack.json --pattern-review-qa-report tmp/validation-eurusd-pattern-review-qa.json --pattern-label-schema-report tmp/validation-eurusd-pattern-label-schema.json --pattern-review-template-report tmp/validation-eurusd-pattern-review-template.json --out-json tmp/validation-eurusd-research-readiness.json --out-md tmp/validation-eurusd-research-readiness.md
```

Review policy:
- Candidate samples are QA-reviewed and label-schema-governed before manual annotation.
- Template rows default to `review_status=pending` under schema `eurusd_15m_pattern_review_v1`.
- No trading signal/order fields are allowed in review exports.
- Scope remains EURUSD 15m Bid clean view only.

