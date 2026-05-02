# Dataset Quality Loop

This workflow is for offline dataset QA and feature research readiness only.

## New in Phase 836-865

Dataset quality reports now include:

- **Quality Score**: Offline data quality score (0-100) with grade (A-D or review_needed)
  - Components: schema completeness, timestamp availability, row count confidence, label coverage, column completeness, bounded read confidence
  - Not a trading/model performance indicator
- **Status Levels**: pass, warn, review_needed, blocked
- **Label Review Buckets**: Prioritized label issues (missing labels, sparse labels, dominant imbalance, etc.)
- **Ranked Review Items**: Prioritized offline research queue with recommended actions
- **Feature Readiness**: Categories for ready/review/blocked feature columns
- **Time Quality**: Enhanced time coverage with session distribution and gap severity

All reports include `schema_version` fields for stable parsing.

## New in Phase 866-895

Schema contracts and golden fixture regression:

- **Schema Contracts**: Explicit validation for all report types
  - Required fields enforced
  - Type checking
  - Additive changes allowed, breaking changes detected
- **Golden Shape Snapshots**: Stable shape fixtures in `cajas/data_examples/golden/dataset_quality/`
- **Contract Validation CLI**: `validate_dataset_quality_contract.py`
- **Regression Tests**: Prevent accidental field removal or type changes

Contract validation:

```bash
./.venv-qlib313/bin/python cajas/scripts/validate_dataset_quality_contract.py \
  --bundle-root tmp/dataset-quality-smoke \
  --out-json tmp/dataset-quality-smoke/contract/dataset_quality_contract_report.json \
  --out-md tmp/dataset-quality-smoke/contract/dataset_quality_contract_report.md
```

Build golden shapes:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_dataset_quality_golden_shapes.py \
  --smoke-root tmp/dataset-quality-smoke \
  --out-dir cajas/data_examples/golden/dataset_quality
```

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
