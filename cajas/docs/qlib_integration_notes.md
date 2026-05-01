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
