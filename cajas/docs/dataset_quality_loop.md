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

## New in Phase 1106-1135

Validation delivery packet and artifact index:

- **Validation Delivery Packet**: Bundle all validation artifacts into one reviewer-friendly package
  - CLI: `build_validation_delivery_packet.py`
  - Indexes dataset quality, contract, trend, budget, diff, manifest, audit artifacts
  - Status aggregation: pass/warn/fail based on critical artifacts
  - Artifact presence table with critical/optional classification
- **Packet Index**: Reviewer-friendly Markdown summary
  - Executive summary with overall status
  - Artifact index table
  - Reviewer notes and recommended actions
  - Scope note: offline research infrastructure only

Build validation delivery packet:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_delivery_packet.py \
  --packet-name dataset_quality_validation_packet \
  --smoke-root tmp/dataset-quality-smoke \
  --contract-report tmp/dataset-quality-smoke/contract/dataset_quality_contract_report.json \
  --trend-snapshot tmp/dataset-quality-smoke/contract/dataset_quality_trend_snapshot.json \
  --out-dir tmp/validation-delivery-packet
```

Packet status interpretation:

- **pass**: All critical artifacts present and passing
- **warn**: Optional artifacts missing or warnings detected
- **fail**: Critical artifacts missing or validation failures

**Scope**: Validation delivery packets summarize offline Qlib research infrastructure validation artifacts only. They are not trading, execution, alpha, or model performance reports.


## Phase 1136–1165: Validation Timing Granularity and Delivery Packet Integration

**Goal**: Improve runtime budget reporting by distinguishing required vs optional components and integrating runtime status into delivery packets.

**Problem**: Previous runtime budget checks warned when optional component timings were missing, creating noise. Delivery packets didn't surface runtime budget status clearly.

**Solution**:

1. **Required vs Optional Components**:
   - Extended `validation_runtime_budgets.json` with `required_components` and `optional_components` lists
   - Updated `check_validation_runtime_budgets()` to only warn/fail for missing required components
   - Optional components missing no longer cause overall warn status

2. **Enhanced Budget Reports**:
   - Added "Type" column to budget report showing 🔴 required vs optional
   - Updated reviewer recommendations to distinguish required vs optional missing timings
   - Improved clarity of pass/warn/fail status

3. **Delivery Packet Integration**:
   - Delivery packet now includes `runtime_budget_status` in summary
   - Shows measured fast validation runtime when available
   - Links to runtime budget report artifact

**Key Files**:
- `cajas/data_examples/validation_runtime_budgets.json` - added required/optional classification
- `cajas/reports/validation_runtime_budget.py` - updated status logic
- `cajas/reports/validation_delivery_packet.py` - integrated runtime status
- `cajas/tests/test_validation_runtime_budget.py` - added optional component test

**Validation**:
- Fast validation: ~84.03s (376 tests passed, +1 from Phase 1106)
- Runtime budget status: **pass** (previously warn due to missing optional timings)
- Data-source audit: stable at read_csv_count=29
- All required components measured and within budget
- Optional components missing as expected (not measured in fast validation)

**Impact**:
- Reduced noise in runtime budget reports
- Clearer distinction between critical and nice-to-have timings
- Better reviewer guidance on when action is needed
- Delivery packets now surface runtime status prominently

**Limitations**:
- Optional component timings still not captured by fast validation
- No automated timing summary report yet (can be added if needed)
- No convenience bundle script (manual commands still required)


## Phase 1166–1195: Automated Validation Review Bundle Workflow

**Goal**: Reduce manual artifact assembly by adding orchestration script that builds complete validation review bundles.

**Problem**: Reviewers had to manually run multiple CLIs in sequence to assemble validation artifacts. No single command to generate a complete review bundle.

**Solution**:

1. **Review Bundle Orchestration CLI**:
   - Created `build_validation_review_bundle.py` to orchestrate existing validation CLIs
   - Coordinates: smoke → timing → budget → diff → manifest → audit → packet
   - Safe execution modes with explicit opt-in for expensive operations

2. **Execution Modes**:
   - `--skip-fast-validation`: use existing timing JSON only (default)
   - `--run-fast-validation`: run fast validation
   - `--create-baseline-from-current`: create no-op diff baseline
   - `--build-experiment-manifest`: generate experiment manifest
   - `--run-data-source-audit`: run audit with data root
   - `--warn-only`: don't fail on warnings

3. **Bundle Manifest and Index**:
   - Generates `review_bundle_manifest.json` with execution record
   - Generates `review_bundle_index.md` with reviewer guidance
   - Tracks commands executed vs skipped
   - Surfaces delivery packet status, runtime budget status, reviewer diff status

4. **Delivery Packet Integration**:
   - Bundle workflow invokes delivery packet builder
   - Packet artifacts placed in `delivery_packet/` subdirectory
   - Bundle index includes packet status summary

**Key Files**:
- `cajas/scripts/build_validation_review_bundle.py` - orchestration CLI
- `cajas/tests/test_validation_review_bundle.py` - 6 tests covering orchestration logic

**Validation**:
- Fast validation: ~103.70s (382 tests passed, +6 from Phase 1136)
- Runtime budget status: **pass**
- Data-source audit: stable at read_csv_count=29
- Review bundle tests: 6 passed
- All validation tests: 77 passed (was 71, +6 for review bundle)

**Example Usage**:

```bash
# Minimal bundle (smoke + packet only)
python cajas/scripts/build_validation_review_bundle.py \
  --bundle-name dataset_quality_review_bundle \
  --out-root tmp/validation-review-bundle \
  --smoke-root tmp/dataset-quality-smoke \
  --warn-only

# Full bundle with baseline diff
python cajas/scripts/build_validation_review_bundle.py \
  --bundle-name dataset_quality_review_bundle \
  --out-root tmp/validation-review-bundle \
  --smoke-root tmp/dataset-quality-smoke \
  --fast-timing-json tmp/fast_validation_latest.json \
  --budgets cajas/data_examples/validation_runtime_budgets.json \
  --create-baseline-from-current \
  --warn-only
```

**Impact**:
- Single command to generate complete review bundle
- Explicit control over expensive operations
- Clear execution record for reviewers
- Reduced manual artifact assembly
- Better CI integration path

**Limitations**:
- Does not run fast validation by default (must opt-in)
- Does not run data source audit by default (must opt-in)
- No historical bundle comparison yet
- No bundle-level trend tracking


## Phase 1196–1225: Fast Validation Runtime Optimization and Tier Split

**Goal**: Bring fast validation back under 105s budget after Phase 1166 exceeded it.

**Problem**: Fast validation runtime increased to ~111.73s in Phase 1166, exceeding the 105s budget. Review bundle tests were running real subprocess commands, taking ~12.97s for 6 tests.

**Solution**:

1. **Profiling**:
   - Used `pytest --durations=30` to identify slow tests
   - Found review bundle tests taking 3-4 seconds each
   - Identified subprocess calls as the bottleneck

2. **Review Bundle Test Optimization**:
   - Refactored tests to mock `run_command` function
   - Replaced real subprocess calls with fake command runner
   - Tests now use minimal fake artifacts
   - Preserved test coverage while eliminating subprocess overhead

3. **Results**:
   - Review bundle tests: **12.97s → 0.22s** (58x speedup)
   - Fast validation total: **111.73s → 97.66s** (14.07s improvement)
   - Runtime budget status: **warn → pass**

**Key Files**:
- `cajas/tests/test_validation_review_bundle.py` - optimized with mocking

**Validation**:
- Fast validation: ~97.66s (382 tests passed, same count)
- Runtime budget status: **pass** ✅
- Required components within budget:
  - `fast_total`: 97.66s / 105.0s (0.93x, -7.34s under budget)
  - `pytest_fast`: 93.55s / 95.0s (0.98x, -1.45s under budget)
- Data-source audit: stable at read_csv_count=29
- Review bundle workflow: still works correctly

**Profiling Findings**:
- Slowest test before optimization: `test_bundle_index_created` at 3.81s
- Slowest test after optimization: `test_audit_cli_writes_json_and_markdown` at 4.29s (different test)
- Review bundle tests now all < 0.01s each
- No tier split needed - optimization alone brought runtime under budget

**Impact**:
- Fast validation back under budget without weakening coverage
- 14.07s improvement (12.6% faster)
- Review bundle tests 58x faster
- No need to raise budget or split tiers
- Deterministic local validation preserved

**Limitations**:
- Fast validation at 93% of budget (97.66s / 105s)
- Limited headroom for future test additions (~7s remaining)
- May need tier split or budget increase in future phases
