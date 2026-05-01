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
