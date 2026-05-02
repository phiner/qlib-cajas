# Dataset Quality Loop

This workflow is for offline dataset QA and feature research readiness only.

## Combined bundle CLI

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

## Modular CLIs

```bash
./.venv-qlib313/bin/python cajas/scripts/build_dataset_quality_report.py --help
./.venv-qlib313/bin/python cajas/scripts/build_label_coverage_diagnostics.py --help
./.venv-qlib313/bin/python cajas/scripts/build_time_coverage_diagnostics.py --help
./.venv-qlib313/bin/python cajas/scripts/run_chunked_feature_dry_run.py --help
./.venv-qlib313/bin/python cajas/scripts/build_feature_schema_manifest.py --help
./.venv-qlib313/bin/python cajas/scripts/build_offline_research_queue_summary.py --help
```

## Smoke runner

```bash
./.venv-qlib313/bin/python cajas/scripts/run_dataset_quality_smoke.py \
  --out-root tmp/dataset-quality-smoke
```

Default fixtures:

- input: `cajas/data_examples/validation_fixtures/eurusd_tiny.csv`
- labels: `cajas/data_examples/validation_fixtures/eurusd_tiny_labels.csv`

Outputs:

- `dataset_quality/dataset_quality_report.{json,md}`
- `labels/label_coverage_diagnostics.{json,md}`
- `time/time_coverage_diagnostics.{json,md}`
- `features/chunked_feature_dry_run.{json,md}`
- `features/feature_schema_manifest.{json,md}`
- `research_queue/offline_research_queue_summary.{json,md}`

## Boundaries

- offline research only
- no model training
- no execution simulation
- no broker/order/trading logic


## Runtime and Testing

Fast validation:

- Modular CLI tests use in-process `main(argv)` calls for speed.
- Test runtime: `~0.05s` for full modular CLI coverage.
- Fast validation tier includes dataset-quality tests.

Explicit smoke:

- Run full dataset-quality smoke workflow:
  ```bash
  ./.venv-qlib313/bin/python cajas/scripts/run_dataset_quality_smoke.py --out-root tmp/dataset-quality-smoke
  ```
- Smoke runtime: `~2-3s` with tiny fixtures.

Programmatic usage:

- All modular CLIs support `main(argv)` for testing and scripting:
  ```python
  from cajas.scripts.build_dataset_quality_report import main
  ret = main(["--input", "data.csv", "--labels", "label", "--out-json", "out.json", "--out-md", "out.md"])
  ```
