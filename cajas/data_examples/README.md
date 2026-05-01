# FX Dataset Schema Notes (Phase 0-3)

## Input CSV

Expected raw input is a 15m EURUSD Bid CSV.

Required columns:
- `Time (UTC)`
- `Open`
- `High`
- `Low`
- `Close`
- `Volume` or `Volume `

Header compatibility:
- the script trims header whitespace, so both `Volume` and `Volume ` are accepted

Input format details:
- datetime format: `YYYY.MM.DD HH:MM:SS`
- timeframe: `15m`
- default symbol: `EURUSD`

## Output CSV (Research Dataset)

Phase 0 output is a plain research dataset CSV (not Qlib binary format).

Expected fields include at least:
- `datetime`
- `symbol`
- `timeframe`
- `open`
- `high`
- `low`
- `close`
- `volume`
- lightweight K-line feature columns
- `future_return_8` (or `future_return_{horizon}`)
- `future_direction_8` (or `future_direction_{horizon}`)

## Temporary Label Definition

Use future close over horizon bars:
- `future_return_8 = close.shift(-8) / close - 1`

Three-class label rule:
- `up` when `future_return_8 > flat_threshold`
- `down` when `future_return_8 < -flat_threshold`
- `flat` otherwise

Default `flat_threshold` is `0.0002`.

Important: `future_direction_8` is a research label, not a trading signal.

## Phase 3 Prepared Handler Rules

- Required columns for `PreparedCsvHandler`:
  - `datetime`
  - `symbol`
  - `timeframe`
  - `open`
  - `high`
  - `low`
  - `close`
  - `volume`
  - `future_direction_8`
- Candidate feature columns are numeric columns excluding:
  - `datetime`
  - `symbol`
  - `timeframe`
  - label column (`future_direction_8` by default)
  - leakage columns: `future_close_8`, `future_return_8`
- `future_close_8` and `future_return_8` may remain in dataset output for auditability, but must not be used as model features.

## Phase 4 Adapter Notes

- `PreparedDataset` (DatasetH-like adapter) returns segment-wise features and labels.
- Audit columns remain allowed in the dataset file:
  - `future_close_8`
  - `future_return_8`
- These audit columns are explicitly excluded from feature sets.
- Labels remain string classes (`up`, `down`, `flat`) in this phase.

## Phase 5 Workflow Bridge Notes

- Workflow bridge input remains the Phase 1 prepared CSV output.
- `PreparedWorkflow` validates segment data shapes in dry-run mode only.
- Leakage audit columns are never used as features:
  - `future_close_8`
  - `future_return_8`
- Labels remain string classes (`up`, `down`, `flat`).

## Phase 6 Experiment Config Notes

- Default config path:
  - `cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml`
- Config points to the Phase 1 prepared CSV by default.
- CSV path can be overridden in local dry-run testing with `--input-override`.
- Leakage audit columns remain non-feature fields:
  - `future_close_8`
  - `future_return_8`

## Phase 7 Dry-Run Artifact Notes

- Dry-run artifacts are local metadata files and do not contain raw dataset rows.
- Prepared CSV remains a local source input for dry-run validation.
- Artifact output under `tmp/` is local-only and should not be committed.

## Phase 8 Audit Rules

- Feature audit rules:
  - leakage columns must not appear in feature inputs
  - non-numeric features are rejected
  - all-null feature columns are rejected
  - constant feature columns are warnings
- Label audit rules:
  - expected classes are `down`, `flat`, `up`
  - unknown classes are rejected
  - missing labels are rejected
  - very rare classes are warnings
- `future_close_8` and `future_return_8` remain audit columns, not model features.

## Phase 9 Planning Notes

- Missing-value audit now includes:
  - missing counts
  - missing ratios
  - top missing feature summary
- Baseline plan artifacts do not contain raw rows.
- Dependency probe is environment-only and does not install packages.

## Phase 10 Scaffold Notes

- Label encoding plan (`down:0`, `flat:1`, `up:2`) is planning metadata only.
- Prepared CSV labels remain string classes in this phase.
- Baseline scaffold artifacts do not contain raw rows.

## Phase 11 Preflight Notes

- Preflight reports do not contain raw rows.
- Path hygiene checks protect command/path accuracy (`cajas/` vs typo `caixas/`).
- Prepared CSV labels remain string classes.

## Phase 12 Disabled Baseline Runner Notes

- Blocked-run artifacts do not contain raw dataset rows.
- Blocked-run artifacts are metadata only:
  - `baseline_blocked_run_report.json`
  - `baseline_run_contract.json`
- No model artifacts are produced in Phase 12.
- Prepared CSV labels remain string classes (`down`, `flat`, `up`).

## Phase 13 Future Training Skeleton Notes

- Future training skeleton artifacts do not contain raw dataset rows.
- Future training skeleton artifacts are metadata only:
  - `future_training_skeleton_report.json`
  - `training_enable_contract.json`
- Labels remain string classes until a future explicitly approved training phase.
- Label encoding plan remains metadata-only in this phase.

## Phase 14 Preview Artifacts

Phase 14 adds derived training-input preview artifacts under local `tmp/` output paths.

Examples:
- `train_features.csv`, `valid_features.csv`, `test_features.csv`
- `train_labels.csv`, `valid_labels.csv`, `test_labels.csv`
- `train_encoded_labels.csv`, `valid_encoded_labels.csv`, `test_encoded_labels.csv`
- `training_input_materialization_report.json`
- `label_encoding_preview.json`
- `metric_plan.json`

Notes:
- These are derived preview artifacts for inspection only.
- Encoded labels are preview artifacts only; source prepared CSV labels remain unchanged.
- Source prepared CSV remains local data input and should not be modified by preview materialization.

## Phase 15 Compatibility Probe Artifacts

- Dataset compatibility probe consumes the prepared CSV output as local input.
- Compatibility reports are written under local `tmp/` paths (for example `tmp/cajas/qlib_compat/`).
- No raw market rows are committed by this probe flow.

## Phase 16 Adapter Probe Artifacts

- Adapter probe consumes prepared CSV outputs as local inputs.
- Probe artifacts live under local `tmp/` paths (for example `tmp/cajas/qlib_adapter/`).
- No raw rows are committed by this flow.
- No model artifacts are produced.

## Phase 17 Workflow Config Probe Artifacts

- Workflow-config probe artifacts are local files under `tmp/` (for example `tmp/cajas/qlib_workflow_config/`).
- The draft workflow config does not include raw dataset rows.
- The probe output is compatibility metadata, not a training output.

## Phase 18 Workflow Dry-Run Loader Artifacts

- Dry-run loader artifacts are local files under `tmp/` (for example `tmp/cajas/qlib_workflow_dry_run_loader/`).
- Class resolution reports are metadata only and do not contain raw dataset rows.
- The generated workflow config draft remains inspection-only for disabled execution validation.

## Phase 19-20 Local Baseline Training Artifacts

- Local baseline training consumes the prepared CSV and existing train/valid/test segments.
- Prediction artifacts are classification inspection outputs and are not trading signals.
- Metrics artifacts are classification-only and exclude trading/performance metrics.

## Phase 21 Baseline Review Artifacts

- Baseline review files are derived local artifacts under `tmp/` and should not be committed.
- Review outputs summarize classification behavior from prediction CSV artifacts.
- Prediction labels remain market-recognition classes and are not trading actions.

## Phase 23-26 Reporting Artifacts

- Baseline report packs, multi-model comparisons, feature summaries, and registry summaries are derived local artifacts under `tmp/`.
- These files should not be committed.
- Reported metrics remain classification-only and do not include trading/performance outputs.

## Phase 27-30 Sanitation and Health Artifacts

- Numeric sanitation reports are model-input diagnostics only and do not modify source prepared CSV.
- Markdown exports and run-health outputs are derived local artifacts under `tmp/`.
- These outputs should not be committed.

## Phase 31-34 Registry and Research Artifacts

- Registry cleanup outputs, dashboard exports, confidence summaries, and research report packs are derived local artifacts under `tmp/`.
- Confidence buckets are classification QA summaries and are not trading thresholds.
- These outputs should not be committed.

## Phase 35 External Holdout Layout

- Raw multi-year CSV files remain outside the repo under local data paths.
- Prepared train (2020-2024) and holdout (2025) outputs are intentionally separated under `tmp/`.
- External holdout artifacts are derived local files and should not be committed.

## Phase 36-40 Derived Artifacts

- Horizon label previews (`future_direction_4/8/16`) are derived from prepared datasets and written under `tmp/`.
- Feature-group audit outputs are derived metadata for classification feature analysis.
- Research decision reports are research artifacts and are not trading guidance.
