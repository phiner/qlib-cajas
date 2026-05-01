# Qlib Integration Notes for cajas EURUSD 15m Research

## Current prepared dataset

- Input local output:
  - `tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv`
  - `tmp/cajas/eurusd_15m_phase1/dataset_manifest.json`
- Label:
  - `future_direction_8`
- Snapshot from Phase 1 output:
  - row_count: `24896`
  - datetime range: `2025-01-01 22:00:00` to `2025-12-31 19:45:00`
  - label distribution: `down=12100`, `flat=106`, `up=12690`
- Important warning:
  - This label is for market recognition research only.
  - It is not a trading signal.

## Qlib components reviewed

- `examples/benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml`
  - baseline YAML shape for `qlib_init`, `task.model`, `task.dataset`, and `record`.
- `examples/benchmarks/LightGBM/workflow_config_lightgbm_configurable_dataset.yaml`
  - shows `DatasetH` + `DataHandlerLP` composition in config form.
- `examples/workflow_by_code.py`
  - code-based workflow using `init_instance_by_config`, `model.fit(dataset)`, and `R.start`.
- `qlib/data/dataset/__init__.py`
  - `DatasetH` accepts a handler config object and segment definitions.
- `qlib/data/dataset/handler.py`
  - `DataHandler`/`DataHandlerLP` rely on pluggable `data_loader` and can be initialized by config.
- `examples/benchmarks/LightGBM/multi_freq_handler.py`
  - external custom handler pattern (`DataHandlerLP` subclass) without editing qlib core.
- `examples/highfreq/highfreq_handler.py`
  - additional custom handler examples outside qlib core path.

## Candidate integration paths

### Path A: Qlib native provider format

Description:
- Convert prepared CSV into Qlib provider/bin format, then consume with native handler configs.

Pros:
- Closest to existing benchmark workflows and docs.
- Reuses standard `provider_uri` + dataset conventions.

Cons:
- Requires a dedicated conversion step and validation for forex schema compatibility.
- Adds data-format coupling before the research schema stabilizes.

Next step needed:
- Evaluate a reproducible CSV->Qlib provider conversion pipeline for EURUSD 15m.

### Path B: Custom external DataHandler / Dataset

Description:
- Keep Phase 1 prepared CSV as source of truth and add custom handler code under `cajas/` (for example `cajas/handlers/...`) to feed `DatasetH`.

Pros:
- No qlib core changes required.
- Faster iteration on feature/label schema while research target is evolving.
- Clear separation between upstream qlib and cajas research layer.

Cons:
- Requires implementing and maintaining a lightweight custom loader/handler.
- Must define clear mapping from flat CSV columns to handler output structure.

Next step needed:
- Implement a minimal custom handler in `cajas/` that reads prepared CSV and returns data consumable by `DatasetH` for a no-training smoke flow.

## Recommended next step

- Recommended Phase 3 route: start with **Path B (minimal external integration layer)**.
- Keep qlib core untouched; add a small custom handler/loader in `cajas/` and validate that `DatasetH.prepare()` works on train/valid/test segments using Phase 1 CSV.
- Defer provider-format migration (Path A) until schema and label contracts are stable.

## Phase 3 Update

- Path B implementation has started with:
  - `cajas.handlers.prepared_csv_handler.PreparedCsvHandler`
  - `cajas/scripts/validate_prepared_dataset_handler.py`
- Current status:
  - This is not a full Qlib provider implementation.
  - It is a minimal prepared CSV contract validation layer.
  - It prepares the data shape and segment semantics needed for a later Qlib `DatasetH` wrapper.
- Feature policy in Phase 3:
  - `future_close_8` and `future_return_8` are audit columns only.
  - They are explicitly excluded from candidate feature columns.

## Phase 4 Recommendation

- Add a Qlib-compatible wrapper or experiment runner that validates DatasetH-like prepare semantics end-to-end.
- Keep qlib core unchanged.
- Continue to avoid model training until dataset contract and split semantics are stable.

## Phase 4 Update

- Added a Qlib-inspired external adapter:
  - `cajas.datasets.prepared_dataset.PreparedDataset`
- This adapter wraps `PreparedCsvHandler` and exposes segment-wise `(features, labels)` via `prepare(segment)`.
- Adapter scope:
  - research-only data contract checks
  - feature/label shape and segment slicing verification
  - explicit exclusion of leakage fields from features
- Adapter boundary:
  - intentionally outside `qlib/` core
  - not a full Qlib DatasetH subclass
  - does not run Qlib LightGBM training in this phase

## Next Integration Step

- Wire the external adapter contract into a small Qlib-facing runner in `cajas/` to validate DatasetH-style workflow calls.
- Keep training disabled until the data contract is stable and reproducible.

## Phase 5 Update

- Added a Qlib-inspired external workflow bridge:
  - `cajas.workflows.prepared_workflow.PreparedWorkflow`
- Bridge behavior in this phase:
  - consumes `PreparedDataset`
  - validates train/valid/test feature-label shapes
  - checks leakage columns are excluded from features
  - exposes dry-run summary only
- Boundary:
  - still external to `qlib/` core
  - not a full Qlib workflow execution
  - no LightGBM training in this phase

## Phase 6 Recommendation

- Add a minimal training-disabled experiment config loader that maps this bridge contract to Qlib-style config semantics.
- If feasible, add a true Qlib-compatible `DatasetH` wrapper under `cajas/` while keeping qlib core unchanged.
- Only after contract stability should a controlled baseline training attempt be considered in a later phase.

## Phase 6 Update

- Added YAML-driven experiment config loader and validator:
  - `cajas.config.experiment_config.load_experiment_config`
  - `cajas.config.experiment_config.validate_experiment_config`
  - `cajas.config.experiment_config.assert_training_disabled`
  - `cajas.config.experiment_config.build_workflow_config`
- Added plan dry-run bridge CLI:
  - `cajas/scripts/run_experiment_plan_dry_run.py`
- Bridge flow:
  - YAML config -> typed config dataclasses -> PreparedWorkflowConfig -> `PreparedWorkflow.dry_run()`
- Boundaries preserved:
  - no qlib core changes
  - no model training
  - no trading semantics

## Phase 7 Recommendation

- Add a minimal Qlib-style dry-run report/recorder artifact that captures config and segment-shape evidence.
- Keep training disabled by default until config contract stability is confirmed across repeated datasets.

## Phase 7 Update

- Added local dry-run artifact recorder in `cajas/recorders/`:
  - run manifest
  - normalized config snapshot
  - workflow summary
  - validation report
- Extended `run_experiment_plan_dry_run.py` to optionally persist artifacts.
- This recorder is Qlib-recorder-inspired but remains fully external to `qlib/` core.
- Model training remains disabled.

## Phase 8 Recommendation

- Add a controlled baseline-training preparation gate that stays disabled by default.
- Or add a deeper DatasetH compatibility probe before enabling any training switch.

## Phase 8 Update

- Added baseline readiness gate for future baseline planning:
  - config validation
  - training-disabled enforcement
  - feature leakage/schema audits
  - label class/distribution audits
- Added readiness CLI with text/JSON/strict and optional local artifact output.
- This remains a safety and data-quality gate only. It is not model training.

## Phase 9 Recommendation

- Add a training-disabled LightGBM baseline plan object with explicit activation gate.
- If explicitly approved later, add a controlled baseline training command that writes local artifacts only and does not include trading behaviors.

## Phase 9 Update

- Added baseline planning artifact (training-disabled):
  - readiness (non-strict/strict)
  - dependency probe (`pandas`, `yaml`, `sklearn`, `lightgbm`)
  - model spec for future baseline phases
  - blockers and warnings summary
- Added `build_baseline_plan.py` CLI for planning output only.
- No model build/fit/predict/evaluate/serialize logic is included.

## Phase 10 Recommendation

- Add a controlled baseline training scaffold with `training.enabled: false` as default.
- Or add a deeper Qlib DatasetH compatibility probe before enabling any training action.

## Phase 10 Update

- Added a training guard to make accidental training impossible in this phase.
- Added a baseline scaffold report that combines:
  - baseline plan
  - readiness summary
  - dependency probe
  - dataset spec
  - label encoding plan (spec-only)
- Added scaffold CLI and optional local scaffold artifact output.
- This remains a safety wrapper and planning layer; no model is built or trained.

## Phase 11 Recommendation

- Add a controlled training command scaffold with `training.enabled` still false by default and explicit multi-flag safety checks.
- Or prioritize a deeper Qlib DatasetH compatibility probe before any training enablement.

## Phase 11 Update

- Added baseline execution contract to separate allowed planning actions from forbidden model/trading actions.
- Added baseline preflight report that consolidates:
  - config checks
  - readiness
  - baseline plan
  - baseline scaffold
  - dependency probe
  - path hygiene
- Added path hygiene checks to catch typo paths such as `caixas/`.
- Training remains disabled and preflight keeps `can_train_now: false`.

## Phase 12 Recommendation

- Add an explicitly disabled training command skeleton with no model fit path.
- Or, if explicitly approved, move to a controlled baseline training phase with artifact-only outputs and no trading behaviors.

## Phase 12 Update

- Added Phase 12 baseline run contract:
  - `cajas.baseline.run_contract.build_phase12_baseline_run_contract`
- Added training-disabled baseline runner entry point:
  - `cajas.baseline.baseline_runner.run_training_disabled_baseline`
  - `cajas/scripts/run_baseline_disabled.py`
- Runner flow:
  - runs baseline preflight
  - builds a Phase 12 run contract
  - returns blocked-run metadata
  - stops before model creation
- Safety boundaries in this phase:
  - no model build
  - no fit
  - no predict
  - no evaluate
  - no model serialization
  - no trading behavior

## Phase 13 Recommendation

- Option A: add an explicit user-approved training enable switch while preserving no-trading boundaries.
- Option B: first add a stronger Qlib DatasetH compatibility probe and keep training disabled.

## Phase 18 Update

- Added class-path resolution utilities for config-declared classes:
  - `cajas.qlib_compat.class_resolver`
- Added workflow dry-run loader:
  - `cajas.qlib_compat.workflow_dry_run_loader`
  - `cajas/scripts/run_qlib_workflow_dry_run_loader.py`
- Phase 18 extends Phase 17 by validating class paths and disabled execution flags in one dry-run report.
- This remains inspection-only:
  - no qlib initialization
  - no qlib workflow execution
  - no model construction
  - no model training

## Phase 19 Recommendation

- Add a workflow dry-run manifest registry for comparing multiple config snapshots, or
- If explicitly approved by the user, prepare a separately gated baseline training phase.

## Phase 19-20 Update

## Research Decision Packet Workflow

The phase 56-65 decision layer is a conservative research audit path:

1. aggregate label/feature/calibration/stability/readiness artifacts
2. produce a research decision packet
3. optionally build a candidate promotion manifest for manual review
4. index generated artifacts for traceability

Reference commands:

```bash
python cajas/scripts/build_research_decision_packet.py --reports-dir ... --out-dir ...
python cajas/scripts/build_candidate_promotion_manifest.py --decision-packet ... --out-dir ... --label-variant-id ... --feature-set-id ... --target-name ... --horizon 8 --model-family LightGBM
python cajas/scripts/build_research_report_index.py --root-dir ... --out-dir ...
python cajas/scripts/run_research_packet_smoke.py --out-root tmp/research-packet-smoke
```

Boundaries:
- research readiness only
- no trading strategy or order execution behavior
- no qlib core modifications
- `candidate_for_qlib_trial` means candidate for controlled manual review, not production deployment

## Phase 66-75: Adapter Contract and Dry-Run Promotion Boundary

This phase adds a strict handoff boundary from research artifacts to Qlib-facing dry-run packets:

1. build adapter contract from promotion manifest
2. validate required identifiers and artifact paths
3. build dry-run integration packet
4. build compatibility report

Commands:

```bash
python cajas/scripts/build_qlib_adapter_contract.py --promotion-manifest ... --out ... --candidate-id ... --feature-set-id ... --label-variant-id ... --target-name ... --frequency 15m
python cajas/scripts/build_qlib_integration_packet.py --adapter-contract ... --out-dir ...
python cajas/scripts/build_qlib_compatibility_report.py --adapter-contract ... --out-dir ...
python cajas/scripts/run_qlib_adapter_smoke.py --out-root tmp/qlib-adapter-smoke
```

Artifact interpretation:
- blocking `error` issues indicate handoff is not ready
- non-blocking `warning` issues indicate conservative manual follow-up
- all outputs are dry-run research artifacts only

## Qlib Dataset/Handler Offline Ingestion Workflow

Phase 76-85 adds an offline ingestion layer between adapter handoff and later model bridge:

1. build dataset contract from feature/label CSV artifacts
2. build normalized handler input package
3. validate handler input package in dry-run mode
4. run deterministic smoke command

Commands:

```bash
python cajas/scripts/build_qlib_dataset_contract.py --input-csv ... --out ... --dataset-id ... --label-col future_direction_8
python cajas/scripts/build_qlib_handler_input.py --input-csv ... --out-dir ... --label-col future_direction_8
python cajas/scripts/validate_qlib_handler_input.py --handler-dir ... --out ...
python cajas/scripts/run_qlib_dataset_handler_smoke.py --out-root tmp/qlib-dataset-handler-smoke
```

Boundaries remain unchanged:
- no model training in this phase
- no Qlib core modifications
- no trading execution logic

## Phase 086-095 Model / Experiment Bridge

This phase enables a controlled, CPU-first research model bridge:

1. build model training contract from handler artifacts
2. train bounded baseline model (research-only)
3. write experiment artifacts and metrics
4. register run in research registry
5. build comparison report across runs

Commands:

```bash
python cajas/scripts/build_qlib_model_training_contract.py --handler-input ... --handler-manifest ... --dataset-contract ... --handler-smoke-report ... --out ...
python cajas/scripts/train_qlib_model_bridge_baseline.py --training-contract ... --out-dir ... --seed 42 --max-rows 5000
python cajas/scripts/register_qlib_model_run.py --experiment-dir ... --registry ...
python cajas/scripts/compare_qlib_model_runs.py --registry ... --out ...
python cajas/scripts/run_qlib_model_bridge_smoke.py --out-root tmp/qlib-model-bridge-smoke
```

Safety constraints:
- CPU only
- deterministic seed
- bounded rows in smoke
- no trading/broker/live execution semantics

## Research Gate and No-Broker Dry Run Workflow

Phase 096-105 adds a conservative review gate above model bridge artifacts:

1. build research gate packet from contract, experiment, registry, and comparison artifacts
2. build no-broker dry-run packet that explicitly disables execution capabilities
3. build markdown summary for manual review

Commands:

```bash
python cajas/scripts/build_research_gate_packet.py --contract ... --experiment-dir ... --registry ... --comparison ... --out ...
python cajas/scripts/build_no_broker_dry_run_packet.py --gate-packet ... --out ...
python cajas/scripts/build_research_gate_summary.py --gate-packet ... --no-broker-packet ... --out ...
python cajas/scripts/run_research_gate_smoke.py --out-root tmp/research-gate-smoke
```

Interpretation:
- `offline_review_ready`: conservative checks passed
- `needs_manual_review`: warnings exist and must be reviewed
- `blocked`: required checks failed or required artifacts missing

This phase remains research-only with no broker/live/paper execution integration.

- Added local run registry support for append-only run tracking under `tmp/cajas/run_registry/`.
- Added first controlled local baseline training path:
  - classification-only supervised model
  - valid/test prediction artifacts for inspection
  - classification metrics only (accuracy/F1/confusion matrix/per-class precision-recall-f1)
- This training path is local baseline research and is not qlib workflow training.
- Boundaries remain:
  - no qlib workflow execution
  - no trading/backtest/profit analysis outputs

## Phase 21 Recommendation

- Add model artifact inspection and prediction review tooling.
- Optionally compare LightGBM and sklearn fallback behavior on repeatable runs.
- Keep trading logic out of scope.

## Phase 21 Update

- Added post-training artifact inspection for local baseline run directories.
- Added prediction review reports for valid/test splits:
  - low-confidence samples
  - high-confidence errors
  - per-class error summary
- These review artifacts are for human/data QA and remain classification-only.
- No qlib workflow execution, and no trading/backtest/profit analysis outputs were introduced.

## Phase 22 Recommendation

- Add baseline comparison across multiple run directories using registry metadata.
- Optionally add model feature-importance inspection where model family support exists.

## Phase 23-26 Update

- Added baseline report pack generation from existing run artifacts.
- Added controlled multi-model baseline runs (LightGBM/RandomForest/HistGradientBoosting) with classification-only comparison.
- Added feature importance aggregation across runs.
- Added run registry summary reporting from local JSONL records.
- These workflows extend local baseline research and remain separate from qlib workflow execution.

## Phase 27 Recommendation

- Add report-pack markdown export for human-friendly review.
- Optionally add dashboard-ready JSON export for baseline comparison views.

## Phase 27-30 Update

- Addressed sklearn robustness by adding numeric feature-value auditing and model-input sanitation.
- Sanitization is applied only to training/prediction matrices and does not mutate source prepared CSV files.
- Added robust multi-model status artifacts with per-model completion/failure tracking.
- Added markdown report export and run health checks over registry/artifact consistency.
- All outputs remain classification-only and outside trading/backtest/profit scope.

## Phase 31 Recommendation

- Add confidence-focused classification calibration analysis and export.
- Optionally add dashboard data export for prediction-review and health status timelines.

## Phase 31-34 Update

- Added registry cleanup classification to separate active, temp-test, stale, and missing-artifact records.
- Added dashboard-ready data exports (JSON/CSV) without introducing UI code.
- Added confidence-bucket analysis for classification QA from prediction artifacts.
- Added consolidated research report pack (Markdown + JSON) referencing baseline, confidence, feature, and health summaries.
- Historical temp registry paths are now explicitly classified instead of being treated as unexplained failures.

## Phase 35 Recommendation

- Add static dashboard rendering from exported dashboard JSON files.
- Optionally add confidence calibration experiments for classification-only analysis.

## Phase 35 Update

- Added external holdout validation workflow:
  - train period: 2020-2024
  - holdout period: 2025
- This replaces single-year internal-only splitting for the main validation path.
- 2025 results are interpreted as out-of-sample classification validation only.
- This remains outside trading strategy and backtest/profit interpretation.

## Phase 13 Update

- Added explicit training enable contract with required gates:
  - `cajas.baseline.training_enable_contract.build_phase13_training_enable_contract`
- Added future training skeleton entry:
  - `cajas.baseline.future_training_skeleton.build_future_training_skeleton`
  - `cajas/scripts/build_future_training_skeleton.py`
- The skeleton is intentionally blocked by default gates in this phase:
  - user approval false
  - phase policy false
  - config `training.enabled` false
- Resulting behavior:
  - no model construction
  - no fit
  - no predict
  - no evaluate
  - no model serialization
  - no trading behavior

## Phase 14 Recommendation

- If explicitly user-approved, add a controlled baseline training implementation with artifact-only output and no trading scope.
- Otherwise, prioritize a deeper true Qlib `DatasetH` compatibility probe before any training enablement.

## Phase 14 Update

- Added training input materialization preview flow for inspection-only artifacts:
  - `cajas/baseline/label_encoding.py`
  - `cajas/baseline/metric_plan.py`
  - `cajas/baseline/training_input_materialization.py`
  - `cajas/scripts/materialize_training_inputs_preview.py`
- Materialization output remains local under `tmp/` and can include:
  - `training_input_materialization_report.json`
  - `label_encoding_preview.json`
  - `metric_plan.json`
  - optional train/valid/test features, labels, encoded-label CSV previews
- This phase still does not build, fit, predict, evaluate, or serialize any model.
- This phase still does not change Qlib core or introduce trading behavior.

## Phase 15 Update

- Added Qlib import/API compatibility probe:
  - `cajas.qlib_compat.qlib_probe.probe_qlib_dataset_api`
- Added DatasetH-shape compatibility probe:
  - `cajas.qlib_compat.dataset_shape_probe.run_dataset_h_shape_probe`
- Added local DatasetH-like shim for API-shape comparison:
  - `cajas.qlib_compat.prepared_dataset_h_like.PreparedDatasetHLike`
- Added CLI:
  - `cajas/scripts/probe_qlib_dataset_compat.py`
- This phase validates compatibility shape only:
  - no qlib.init()
  - no model training or predictions
  - no qlib core modifications

## Phase 16 Recommendation

- If feasible, add a true Qlib `DatasetH` wrapper in `cajas/` while keeping training disabled.
- Controlled baseline training remains a separate, explicit-approval phase.

## Phase 16 Update

- Phase 15 confirmed Qlib import availability and DatasetH/DataHandler symbols in this environment.
- Added external real-adapter probe path:
  - `cajas.qlib_compat.prepared_dataset_h_adapter.PreparedQlibDatasetHAdapter`
- Added adapter comparison probe:
  - `cajas.qlib_compat.adapter_comparison_probe.run_adapter_comparison_probe`
- Added CLI:
  - `cajas/scripts/probe_qlib_dataset_h_adapter.py`
- This remains compatibility-only:
  - no qlib.init()
  - no training
  - no qlib core changes

## Phase 17 Recommendation

- If this adapter probe remains stable, add a controlled no-fit baseline trainer object that emits model-config metadata only.
- Or add a real Qlib workflow-config probe without training execution.

## Phase 17 Update

- Phase 15 proved import-level compatibility for Qlib Dataset symbols.
- Phase 16 proved adapter-shape compatibility against current prepared dataset output.
- Phase 17 adds an inspection-only workflow config probe:
  - `cajas.qlib_compat.workflow_config_probe`
  - `cajas/scripts/probe_qlib_workflow_config.py`
- This phase builds a Qlib-style draft workflow config only:
  - no qlib.init()
  - no workflow execution
  - no training

## Phase 18 Recommendation

- Add a true Qlib workflow dry-run loader without execution.
- Or, with explicit approval, add controlled baseline training outside Qlib first.

## Phase 36-40 Update

- External holdout benchmarking now separates internal-split and external-holdout metrics.
- Flat-class behavior is diagnosed explicitly from holdout prediction artifacts.
- Horizon label preview compares 4/8/16 label distributions as research-only diagnostics.
- Feature-group audits provide ablation planning inputs without running trading workflows.
- Research decision reporting is classification-only and does not include trading/backtest/profit conclusions.

## Phase 41-45 Update

- Label redesign workflow now tests threshold-based flat definitions and horizon-specific label variants.
- Binary up/down (`binary_drop_flat`) is available as a classification comparison baseline.
- External holdout comparison remains 2020-2024 train vs 2025 holdout.
- Label thresholds are classification-only label semantics and are not trading thresholds.

## Phase 46-55 Update

- Feature engineering and feature-set versioning are now explicit and testable.
- Calibration, seed stability, rolling-year planning, and error-slice diagnostics extend classification QA.
- Leakage/drift auditing and readiness reporting prepare for future controlled Qlib integration decisions.
- Qlib remains uninitialized and workflow execution remains disabled in this phase range.
