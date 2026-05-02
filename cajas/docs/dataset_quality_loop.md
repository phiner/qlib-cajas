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

## New in Phase 956-985

Enhanced drift semantics and trend tracking:

- **Semantic Validation**: Validates critical field semantics beyond shape
  - `quality_score` must be in [0, 100]
  - Count fields must be non-negative integers
  - Grade/status fields must be known enum values
  - Semantic errors fail contract validation
  - Semantic warnings flag suspicious values
- **Trend Snapshots**: Compact metrics from each smoke run
  - Generated at `tmp/dataset-quality-smoke/contract/dataset_quality_trend_snapshot.json`
  - Captures quality score, status, validation counts, drift counts
  - Deterministic for tests, includes timestamp
- **Trend Comparison**: Compare snapshots across runs
  - CLI: `compare_dataset_quality_trends.py`
  - Detects quality score deltas, status changes, regression patterns
  - Optional `--fail-on-regression` for CI gates
- **Regression Detection**: Automatic detection of clear regressions
  - Contract status pass → fail
  - Semantic errors increase
  - Breaking drift count increase
  - Quality score drops > 5 points
  - Status degradation (pass → warn → review_needed → blocked)

Trend comparison:

```bash
./.venv-qlib313/bin/python cajas/scripts/compare_dataset_quality_trends.py \
  --current tmp/dataset-quality-smoke/contract/dataset_quality_trend_snapshot.json \
  --previous path/to/previous_snapshot.json \
  --out-json tmp/trend_compare.json \
  --out-md tmp/trend_compare.md \
  --fail-on-regression
```

**Scope**: Semantic validation covers only clearly established field semantics. Quality scores remain data quality indicators only, not trading/model performance metrics.

## Contract Workflow

**Running contract validation manually:**

```bash
./.venv-qlib313/bin/python cajas/scripts/validate_dataset_quality_contract.py \
  --bundle-root tmp/dataset-quality-smoke \
  --out-json tmp/dataset-quality-smoke/contract/dataset_quality_contract_report.json \
  --out-md tmp/dataset-quality-smoke/contract/dataset_quality_contract_report.md
```

**Integrated validation:**

Dataset quality smoke now automatically validates schema contracts after generating outputs. Contract validation results are written to:
- `<smoke-root>/contract/dataset_quality_contract_report.json`
- `<smoke-root>/contract/dataset_quality_contract_report.md`

Smoke exits with error if contract validation fails.

**Breaking vs additive changes:**

- **Breaking**: Removing required fields, changing field types
- **Additive**: Adding new optional fields, adding new report sections
- **Allowed**: Extra fields beyond required schema

Golden shapes enforce required fields but allow additive changes.

**Reviewing contract failures:**

1. Check contract report: `tmp/dataset-quality-smoke/contract/dataset_quality_contract_report.md`
2. Review error/warning messages
3. Review drift summary:
   - **Breaking drift**: Missing required fields, type changes, removed fields
   - **Additive drift**: New optional fields added
4. If intentional schema change:
   - Update schema contract in `cajas/reports/dataset_quality_schema_contract.py`
   - Rebuild golden shapes
   - Update tests
5. If unintentional:
   - Fix report generation code
   - Rerun smoke validation

**Reading drift reports:**

Drift summary shows:
- `files_checked`: Number of golden shapes compared
- `files_with_drift`: Number of files with any drift
- `breaking_count`: Breaking changes (requires action)
- `additive_count`: New fields (informational)
- `type_change_count`: Type mismatches (breaking)
- `missing_required_count`: Missing required fields (breaking)

Drift items list specific changes with:
- `file`: Golden shape filename
- `path`: JSON path to changed field
- `kind`: `missing_required`, `type_change`, `additive`, `removed`
- `expected`: Expected value/type
- `actual`: Actual value/type

**Refreshing golden shapes:**

When schema changes are intentional:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_dataset_quality_smoke.py --out-root tmp/dataset-quality-smoke
./.venv-qlib313/bin/python cajas/scripts/build_dataset_quality_golden_shapes.py \
  --smoke-root tmp/dataset-quality-smoke \
  --out-dir cajas/data_examples/golden/dataset_quality
git add cajas/data_examples/golden/dataset_quality
git commit -m "test: update dataset quality golden shapes"
```

## New in Phase 986-1015

Golden fixture scenario expansion:

- **Scenario Coverage**: Multiple edge-case scenarios for robust regression testing
  - `tiny_balanced`: Healthy balanced fixture (baseline)
  - `missing_label_values`: Rows with missing/null labels
  - `single_class_label`: Label with only one class (imbalance)
  - `time_gap`: Timestamp series with deliberate gap
  - `minimal_columns`: Minimal required columns only
- **Scenario Manifest**: Committed manifest describing each scenario
- **Scenario Builder**: CLI to regenerate scenario golden shapes
- **Scenario Tests**: Regression tests for all scenarios (6 tests, ~2s)

Scenario golden shapes location:

```text
cajas/data_examples/golden/dataset_quality_scenarios/
  scenario_manifest.json
  tiny_balanced/
    dataset_quality_report_shape.json
    feature_schema_manifest_shape.json
    offline_research_queue_summary_shape.json
    bundle_shape.json
  missing_label_values/
    ...
  single_class_label/
    ...
  time_gap/
    ...
  minimal_columns/
    ...
```

Build scenario golden shapes:

```bash
# Build all scenarios
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_dataset_quality_golden_scenarios.py \
  --out-dir cajas/data_examples/golden/dataset_quality_scenarios

# Build specific scenario
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_dataset_quality_golden_scenarios.py \
  --out-dir cajas/data_examples/golden/dataset_quality_scenarios \
  --scenario tiny_balanced
```

**Scenario refresh workflow:**

1. Review scenario manifest: `cajas/data_examples/golden/dataset_quality_scenarios/scenario_manifest.json`
2. Regenerate scenario shapes (if needed)
3. Run scenario tests: `pytest cajas/tests/test_dataset_quality_golden_scenarios.py -v`
4. Review diffs before committing
5. Commit updated shapes if intentional changes

**Scope**: Scenarios test schema shape stability only, not exact values. Quality scores remain data quality indicators, not trading/model performance metrics.

## New in Phase 1016-1045

Qlib experiment reproducibility strengthening:

- **Experiment Manifest**: Lightweight reproducibility metadata for offline Qlib research
  - Links dataset quality reports, contract reports, trend snapshots, golden scenarios
  - Captures git branch/commit, Python version, platform info
  - Reviewer-friendly Markdown summary
  - Validation of referenced artifact paths
- **Manifest Builder CLI**: Generate experiment manifests from smoke outputs
- **Reproducibility Status**: Aggregates dataset quality, contract, semantic, drift status
- **Artifact Table**: Shows which reproducibility artifacts are present

Build experiment manifest:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_qlib_experiment_manifest.py \
  --experiment-name dataset_quality_smoke_baseline \
  --dataset-path cajas/data_examples/validation_fixtures/eurusd_tiny.csv \
  --dataset-quality-report tmp/dataset-quality-smoke/dataset_quality/dataset_quality_report.json \
  --contract-report tmp/dataset-quality-smoke/contract/dataset_quality_contract_report.json \
  --trend-snapshot tmp/dataset-quality-smoke/contract/dataset_quality_trend_snapshot.json \
  --golden-scenario-manifest cajas/data_examples/golden/dataset_quality_scenarios/scenario_manifest.json \
  --out-json tmp/qlib-experiment-manifest/experiment_manifest.json \
  --out-md tmp/qlib-experiment-manifest/experiment_manifest.md
```

Manifest validation:

- Checks required fields exist
- Validates referenced paths exist
- Parses referenced JSON files
- Reads dataset quality status, contract status, semantic counts, drift summary
- Generates reviewer-friendly Markdown with artifact table

**Scope**: Experiment manifests are for offline Qlib research reproducibility only. They are not trading execution artifacts. Quality scores remain data quality indicators only.

## New in Phase 1046-1075

Runtime budget enforcement and test optimization:

- **Runtime Budgets**: Engineering guardrails for validation sustainability
  - Budget configuration: `cajas/data_examples/validation_runtime_budgets.json`
  - Component budgets: fast_total (105s), pytest_fast (95s), individual steps
  - Warn threshold: 15% overage allowed before warning
- **Budget Checking**: Automated runtime budget validation
  - CLI: `check_validation_runtime_budget.py`
  - Pass/warn/fail classification
  - Reviewer-friendly reports with component table
- **Current Performance**: Fast validation ~83.5s (Phase 986: ~100s, Phase 1016: ~85s)

Check runtime budget:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/check_validation_runtime_budget.py \
  --budgets cajas/data_examples/validation_runtime_budgets.json \
  --timing-json tmp/fast_validation_latest.json \
  --out-json tmp/validation_runtime_budget_report.json \
  --out-md tmp/validation_runtime_budget_report.md
```

Budget status interpretation:

- **pass**: All components within budget
- **warn**: Some components slightly over budget (≤15% overage) or missing timing data
- **fail**: One or more components significantly over budget (>15% overage)

**Scope**: Runtime budgets are engineering guardrails for validation sustainability. They are not performance claims or trading/model performance metrics.

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

## New in Phase 1076-1105

Reviewer report enhancements — diffs and trends:

- **Reviewer Diff Reports**: Compare baseline vs current research infrastructure artifacts
  - CLI: `build_reviewer_diff_report.py`
  - Compares dataset quality, contract, semantic, drift, runtime budget status
  - Detects quality score deltas, status changes, error increases
  - Pass/warn/fail classification for reviewer action
- **Artifact Comparison**: Structured diff of research infrastructure reports
  - Quality score delta
  - Contract status changes
  - Semantic error delta
  - Breaking drift delta
  - Runtime budget status changes

Build reviewer diff report:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_reviewer_diff_report.py \
  --baseline-root tmp/dataset-quality-smoke-baseline \
  --current-root tmp/dataset-quality-smoke \
  --out-json tmp/reviewer-diff/reviewer_diff_report.json \
  --out-md tmp/reviewer-diff/reviewer_diff_report.md \
  --warn-only
```

Diff status interpretation:

- **pass**: No material changes or improvements only
- **warn**: Quality score decreased, missing artifacts, or minor regressions
- **fail**: Contract status changed to fail, semantic errors increased

**Scope**: Reviewer diff reports compare offline Qlib research infrastructure artifacts only. They are not trading, execution, alpha, or model performance reports.
