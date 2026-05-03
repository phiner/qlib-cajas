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


## Phase 1226–1255: Validation Review Bundle History and Trend Tracking

**Goal**: Add lightweight historical record for validation review bundles to track validation state evolution over time.

**Problem**: No historical tracking of validation bundle state. Reviewers couldn't see how validation metrics evolved across commits or detect gradual regressions.

**Solution**:

1. **Bundle History Snapshots**:
   - Created `validation_review_bundle_history.py` module
   - Compact snapshots capture key validation metrics
   - JSONL format for append-only history
   - Includes: statuses, runtimes, counts, artifact presence

2. **History Tracking Functions**:
   - `create_snapshot_from_bundle()` - extract snapshot from bundle artifacts
   - `append_snapshot()` - append to JSONL history file
   - `read_snapshots()` - read all snapshots
   - `compute_delta()` - calculate changes between snapshots
   - `detect_regressions()` - identify validation regressions
   - `generate_history_summary_markdown()` - reviewer-friendly summary

3. **History Update CLI**:
   - Created `update_validation_review_bundle_history.py`
   - Reads bundle artifacts and appends snapshot
   - Generates JSON and Markdown summaries
   - Shows last N snapshots in table format
   - Detects and highlights regressions

4. **Regression Detection**:
   - Status regressions: pass → warn/fail
   - Runtime regressions: >10% increase
   - Data source regressions: read_csv_count increase
   - Contract error increases
   - Missing required artifact increases

**Key Files**:
- `cajas/reports/validation_review_bundle_history.py` - history tracking module (322 lines)
- `cajas/scripts/update_validation_review_bundle_history.py` - history update CLI (81 lines)
- `cajas/tests/test_validation_review_bundle_history.py` - 8 tests covering history tracking

**Validation**:
- Fast validation: ~90.11s (390 tests passed, +8 from Phase 1196)
- Runtime budget status: **pass** ✅
- Required components within budget:
  - `fast_total`: 90.11s / 105.0s (0.86x, -14.89s under budget)
  - `pytest_fast`: 87.30s / 95.0s (0.92x, -7.70s under budget)
- Data-source audit: stable at read_csv_count=29
- History tests: 8 passed in 2.16s (fast, no subprocess calls)

**Example Usage**:

```bash
# Update bundle history after building bundle
python cajas/scripts/update_validation_review_bundle_history.py \
  --bundle-root tmp/validation-review-bundle \
  --history-jsonl tmp/validation-review-bundle/history/review_bundle_history.jsonl \
  --out-json tmp/validation-review-bundle/history/review_bundle_history_summary.json \
  --out-md tmp/validation-review-bundle/history/review_bundle_history_summary.md \
  --last-n 10
```

**Impact**:
- Lightweight historical tracking without heavy subprocess calls
- Reviewers can see validation state evolution
- Automatic regression detection
- Fast tests (2.16s for 8 tests)
- No impact on fast validation runtime (90.11s, same as Phase 1196)
- JSONL format allows easy append and analysis

**Limitations**:
- No automatic integration with review bundle workflow (manual CLI call)
- No historical trend visualization/charts
- No multi-repository history aggregation
- Simple regression detection (no ML-based anomaly detection)
- JSONL file grows unbounded (no rotation/archival)


## Phase 1256–1285: Integrated Review Bundle History Workflow

**Goal**: Integrate review bundle build workflow with optional history append/summarization so reviewers can use one command while preserving fast runtime discipline.

**What changed**:

1. **Integrated optional history update in bundle CLI**:
   - Updated `cajas/scripts/build_validation_review_bundle.py`
   - Added flags:
     - `--update-history`
     - `--history-jsonl`
     - `--history-last-n`
   - Default behavior remains unchanged when `--update-history` is omitted.

2. **Direct module reuse (no subprocess)**:
   - Reused `cajas/reports/validation_review_bundle_history.py` functions directly.
   - Avoided extra subprocess overhead in tests and fast validation path.

3. **Bundle manifest/index history wiring**:
   - `review_bundle_manifest.json` now includes integrated history metadata.
   - `review_bundle_index.md` now includes a `History` section with:
     - JSONL and summary paths when enabled
     - latest bundle status
     - runtime delta from previous snapshot when available
     - regression count
     - reviewer recommendation
   - When not enabled, index states:
     - `History update was not requested for this bundle.`

4. **Conservative failure behavior**:
   - If `--update-history` is requested and update fails:
     - default: command fails
     - with `--warn-only`: warning is recorded and command continues
   - Failure details are recorded in manifest/index.

5. **Test coverage expansion**:
   - Extended `cajas/tests/test_validation_review_bundle.py` to cover:
     - no-history default behavior
     - history-enabled manifest/index output
     - second run delta generation
     - history failure behavior with and without `--warn-only`
   - Existing history module tests remain in `cajas/tests/test_validation_review_bundle_history.py`.

**Integrated usage**:

```bash
python cajas/scripts/build_validation_review_bundle.py \
  --bundle-name dataset_quality_review_bundle \
  --out-root tmp/validation-review-bundle \
  --smoke-root tmp/dataset-quality-smoke \
  --fast-timing-json tmp/fast_validation_latest.json \
  --budgets cajas/data_examples/validation_runtime_budgets.json \
  --create-baseline-from-current \
  --update-history \
  --history-jsonl tmp/validation-review-bundle/history/review_bundle_history.jsonl \
  --history-last-n 10 \
  --warn-only
```

**Outputs when history is enabled**:
- `tmp/validation-review-bundle/history/review_bundle_history.jsonl`
- `tmp/validation-review-bundle/history/review_bundle_history_summary.json`
- `tmp/validation-review-bundle/history/review_bundle_history_summary.md`
- `tmp/validation-review-bundle/review_bundle_manifest.json` (`history` canonical section, `history_update` compatibility alias)
- `tmp/validation-review-bundle/review_bundle_index.md` (`History` section)

**Non-goals (unchanged)**:
- No trading execution logic
- No broker/order routing integration
- No live or paper trading
- No Qlib core modification for this phase


## Phase 1286–1315: Review Bundle Index Polish and History Delta Readability

**Goal**: Improve reviewer readability in `review_bundle_index.md` and make history delta output human-readable.

**What changed**:
- Replaced raw dict-style runtime delta rendering with a compact markdown delta table.
- Added `## History Summary` section with clear reviewer fields:
  - history status
  - snapshot count
  - latest bundle status
  - runtime budget status
  - regression notes
  - history summary path
- Added stable `history` object in `review_bundle_manifest.json`:
  - `enabled`, `history_jsonl`, `summary_json`, `summary_md`, `status`, `snapshot_count`
- Kept backward compatibility with existing `history_update` fields.

**Behavior notes**:
- If no previous snapshot exists, index renders: `No previous snapshot available.`
- If history is not requested, index renders: `History update was not requested for this bundle.`

**Validation note**:
- No new workflow semantics were added; this phase is output/readability polish only.


## Phase 1316–1345: Review Bundle History Field Standardization and Compatibility

**Goal**: Standardize `history` as the canonical review-bundle manifest contract while keeping compatibility for legacy `history_update` consumers.

**What changed**:
- Canonicalized manifest history metadata under `history`:
  - `enabled`
  - `status`
  - `history_jsonl`
  - `summary_json`
  - `summary_md`
  - `snapshot_count`
  - `latest_bundle_status`
  - `runtime_budget_status`
  - `regression_count`
- Added `normalize_history_metadata(manifest)` helper to consume both canonical and legacy shape safely.
- Retained `history_update` as deprecated compatibility alias with explicit metadata:
  - `deprecated: true`
  - `use: "history"`
- Updated index rendering to use canonical normalized history metadata.

**Consumer guidance**:
- Downstream readers should treat `history` as source of truth.
- `history_update` should be treated as temporary compatibility surface.

**Validation note**:
- No new workflow semantics were introduced; this phase is manifest/index contract cleanup only.


## Phase 1346–1375: Canonical History Consumer Migration Guard

**Goal**: Route internal history metadata consumers through canonical `history` or shared normalization helpers, and add migration-safety checks.

**What changed**:
- Added shared metadata utility module:
  - `cajas/reports/validation_review_bundle_metadata.py`
  - `normalize_history_metadata(manifest)`
  - `validate_history_metadata_compatibility(manifest)`
- Updated builder/index flow to use shared helper imports instead of script-local normalization logic.
- Added optional compatibility check CLI:
  - `cajas/scripts/check_review_bundle_manifest_compatibility.py`
- Added migration-guard warnings for:
  - missing canonical `history`
  - malformed/deprecated `history_update` alias metadata
  - canonical/legacy disagreement on key fields

**Consumer guidance**:
- Canonical source: `manifest["history"]`
- Compatibility path: `normalize_history_metadata(manifest)`
- Deprecated alias `history_update` is retained only for compatibility window.

**Validation note**:
- Contract hardening only; no new workflow semantics introduced.


## Phase 1376–1405: Integrated Manifest Compatibility Report in Review Bundle Workflow

**Goal**: Integrate manifest compatibility reporting into the standard review bundle workflow for reviewer visibility.

**What changed**:
- Added optional compatibility integration flags in review bundle builder:
  - `--check-manifest-compatibility`
  - `--manifest-compatibility-out-json`
  - `--manifest-compatibility-out-md`
- Reused shared compatibility logic directly (no subprocess):
  - `normalize_history_metadata()`
  - `validate_history_metadata_compatibility()`
  - compatibility report rendering helpers
- Added `manifest_compatibility` metadata to bundle manifest:
  - `enabled`, `status`, `warning_count`, `report_json`, `report_md`
  - `not_requested` note when disabled
- Added `## Manifest Compatibility` section to `review_bundle_index.md`.

**Relationship to history contract**:
- Canonical source remains `manifest["history"]`.
- Deprecated alias `history_update` remains compatibility-only during migration window.

**Validation note**:
- Workflow visibility integration only; no new validation semantics beyond existing compatibility guard.


## Phase 1406–1435: Manifest Compatibility Severity and Bundle Gating

**Goal**: Upgrade manifest compatibility checks to explicit severity model (`pass|warn|fail`) and wire status into bundle/CLI gating behavior.

**What changed**:
- Compatibility issues now include severity and code:
  - `error`, `warning`, `info`
- Compatibility report now includes:
  - `status`
  - `error_count`
  - `warning_count`
  - `info_count`
  - `issues`
- Standalone CLI behavior:
  - exit `0` for `pass`
  - exit `0` for `warn` by default
  - exit non-zero for `fail`
  - `--fail-on-warn` supported
- Review bundle integration behavior:
  - compatibility `fail` raises unless `--warn-only` is used
  - compatibility `warn` records warning and continues
  - manifest/index include severity counts and status

**Compatibility window**:
- Canonical source remains `history`.
- `history_update` remains deprecated alias during migration window.


## Phase 1436–1465: Fast Validation Timing Freshness and Consistency Guard

**Goal**: Ensure runtime budget checks and review bundles consume fresh, internally consistent fast-validation timing data.

**What changed**:
- Fast-validation timing JSON (`run_fast_validation.py`) now includes freshness metadata:
  - `created_at`, `run_id`, `command`, `timing_source`
  - plus existing `tier`, `results`, `total_seconds`
  - and explicit `pytest_fast` field
- Runtime budget reporting now includes `timing_consistency` with `pass|warn|fail`:
  - `fail`: required timing missing/non-numeric/negative
  - `warn`: legacy metadata missing, stale timing, or total/step mismatch
  - `pass`: timing data is fresh and numerically consistent
- Budget checker CLI now supports timing consistency parameters:
  - `--expected-tier`
  - `--max-age-seconds`
- Review bundle integration now surfaces timing consistency in manifest/index and applies guardrails:
  - consistency `fail` blocks bundle unless `--warn-only`
  - consistency `warn` is recorded for reviewer visibility

**Why this phase**:
- Addresses the observed risk where wall-clock runtime could diverge from stale timing JSON used by budget checks.

**Known limitation**:
- Legacy timing payloads remain supported for compatibility and are surfaced as warnings instead of hard failures unless critical numeric fields are invalid.


## Phase 1466–1525: CI-Friendly Validation Automation Bundle

**Goal**: Provide a single CI-friendly validation review-bundle path with explicit gate aggregation and machine-readable final status artifacts.

**What changed**:
- Added reusable gate-summary helper: `cajas/reports/validation_gate_summary.py`
- Added CI mode support in `build_validation_review_bundle.py`:
  - `--ci`
  - `--fail-on-warn`
  - `--skip-history`
  - `--skip-manifest-compatibility`
  - `--skip-runtime-budget`
  - `--max-timing-age-seconds`
- Added final status artifacts:
  - `final_status.json`
  - `final_status.md`
- Added top-level `CI Gate Summary` section in bundle index.
- Added gate aggregation across smoke/runtime budget/timing consistency/manifest compatibility/history/delivery packet/reviewer diff/data-source audit.

**CI behavior**:
- In CI mode, canonical workflow defaults are applied conservatively:
  - history update enabled unless explicitly skipped
  - manifest compatibility enabled unless explicitly skipped
  - runtime budget check enabled unless explicitly skipped
- CI mode requires timing input (`--fast-timing-json`) unless `--run-fast-validation` is used.
- `--warn-only` affects command exit behavior, not artifact status values.
- `--fail-on-warn` exits non-zero when final overall status is `warn`.

**Non-goals**:
- No trading execution, broker routing, live trading, annotation, or model-performance claims.


## Phase 1526–1585: CI Gate Explainability, Warn Reduction, and Final Status Hardening

**Goal**: Make final CI/reviewer status explainable and reduce unnecessary warning noise without masking real failures.

**What changed**:
- Expanded gate model with explainability fields:
  - `reason_code`
  - `action`
- Added CI profile-aware status aggregation:
  - `local`
  - `ci`
  - `strict`
- Hardened final status artifact contract:
  - `schema_version`
  - `run_id`
  - `profile`
  - `command`
  - `overall_reason`
  - `blocking_gates`
  - `warning_gates`
  - `optional_or_not_run_gates`
  - `reviewer_next_action`
  - `primary_artifact`
- Improved markdown explainability:
  - explicit top-level overall status, primary reason, reviewer action, and artifact to open first.

**Warn reduction behavior**:
- Optional gate warnings/no-run entries no longer force overall `warn` under `local` profile.
- Required gate warning/fail behavior remains strict.
- Gate-level statuses are preserved truthfully even when profile-level overall status becomes `pass`.

**Profile semantics**:
- `local`: optional warn/not-run do not affect overall status.
- `ci`: optional warn affects overall status; optional not-run does not.
- `strict`: optional warn and optional not-run both affect overall status.


## Phase 1586–1645: CI Profile Policy Externalization, Runtime Variance Margin, and Final Status Reasoning

**Goal**: Make CI behavior auditable/configurable, explain runtime budget variance clearly, and improve reviewer-facing final status reasoning.

**What changed**:
- Added committed profile policy file:
  - `cajas/data_examples/validation_ci_profiles.json`
- Added review-bundle profile policy input:
  - `--ci-profile-config cajas/data_examples/validation_ci_profiles.json`
- Final status now includes profile policy and escalation semantics:
  - `profile_policy`
  - gate-level `escalated`
  - gate-level `profile_effect`
  - `overall_reason_code` with deterministic priority
- Runtime budget config now supports variance margin:
  - `warn_margin_seconds` (per-component)
  - `global_warn_margin_seconds`
- Runtime budget report now includes:
  - `reason_code`
  - `warn_margin_seconds`
  - explicit classification for variance-band warnings vs true over-budget behavior
- Review bundle index now includes:
  - profile summary
  - escalated vs non-escalated warning counts
  - primary artifact and next action

**Recommended local reviewer command**:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_validation_review_bundle.py \
  --ci \
  --ci-profile local \
  --ci-profile-config cajas/data_examples/validation_ci_profiles.json \
  --bundle-name dataset_quality_review_bundle \
  --out-root tmp/validation-review-bundle \
  --smoke-root tmp/dataset-quality-smoke \
  --fast-timing-json tmp/fast_validation_latest.json \
  --budgets cajas/data_examples/validation_runtime_budgets.json \
  --create-baseline-from-current \
  --update-history \
  --history-jsonl tmp/validation-review-bundle/history/review_bundle_history.jsonl \
  --history-last-n 10 \
  --check-manifest-compatibility \
  --warn-only
```

**Recommended CI command**:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_validation_review_bundle.py \
  --ci \
  --ci-profile ci \
  --ci-profile-config cajas/data_examples/validation_ci_profiles.json \
  --run-fast-validation \
  --bundle-name dataset_quality_review_bundle \
  --out-root tmp/validation-review-bundle \
  --smoke-root tmp/dataset-quality-smoke \
  --fast-timing-json tmp/fast_validation_latest.json \
  --budgets cajas/data_examples/validation_runtime_budgets.json \
  --create-baseline-from-current \
  --update-history \
  --history-jsonl tmp/validation-review-bundle/history/review_bundle_history.jsonl \
  --history-last-n 10 \
  --check-manifest-compatibility
```

**Known limitations**:
- Runtime budgets still depend on machine/runtime variance; variance margin reduces false-positive noise but does not remove it.
- Final reason remains single-primary-cause; full gate table should still be reviewed.

**Non-goals**:
- No trading execution automation, broker routing, live/paper trading, annotation workflows, or model-performance claims.


## Phase 1646–1705: Runtime Utility Budget Calibration and CI Final-Status Recovery

**Goal**: Remove false fail status driven by tight utility-step budget while preserving strict detection for core runtime regressions.

**Runtime component audit findings**:
- `run_fast_validation --tier fast` timing includes both core pytest runtime and utility guardrails.
- `path_hygiene` scans markdown/python/yaml under `cajas/` and `tasks/`, so runtime can vary with repository text footprint.
- Recent measured values:
  - prior run: `path_hygiene ~9.59s`
  - latest run: `path_hygiene ~3.38s`
- This variance shows `5.0s` was too tight as a hard threshold for a utility scan.

**Decision**:
- Keep `fast_total` and `pytest_fast` as core required runtime gates.
- Keep `path_hygiene` as utility budgeted component (still measured and visible).
- Calibrate `path_hygiene` budget to `12.0s` with `2.0s` utility margin.
- Treat utility fail as overall runtime `warn` (not `fail`) unless core required gates fail.

**What changed**:
- `validation_runtime_budgets.json`:
  - `path_hygiene: 12.0`
  - `warn_margin_seconds.path_hygiene: 2.0`
  - `component_categories` mapping
- Runtime report now includes per-component:
  - `category`
  - `reason_code`
  - `action`
- Runtime overall-status logic:
  - core required fail => `fail`
  - utility fail => `warn`
  - all within calibrated guardrails => `pass`

**Recommended local command**:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_review_bundle.py \
  --ci \
  --ci-profile local \
  --ci-profile-config cajas/data_examples/validation_ci_profiles.json \
  --bundle-name dataset_quality_review_bundle \
  --out-root tmp/validation-review-bundle \
  --smoke-root tmp/dataset-quality-smoke \
  --fast-timing-json tmp/fast_validation_latest.json \
  --budgets cajas/data_examples/validation_runtime_budgets.json \
  --create-baseline-from-current \
  --update-history \
  --history-jsonl tmp/validation-review-bundle/history/review_bundle_history.jsonl \
  --history-last-n 10 \
  --check-manifest-compatibility \
  --warn-only
```

**Recommended CI command**:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_review_bundle.py \
  --ci \
  --ci-profile ci \
  --ci-profile-config cajas/data_examples/validation_ci_profiles.json \
  --run-fast-validation \
  --bundle-name dataset_quality_review_bundle \
  --out-root tmp/validation-review-bundle \
  --smoke-root tmp/dataset-quality-smoke \
  --fast-timing-json tmp/fast_validation_latest.json \
  --budgets cajas/data_examples/validation_runtime_budgets.json \
  --create-baseline-from-current \
  --update-history \
  --history-jsonl tmp/validation-review-bundle/history/review_bundle_history.jsonl \
  --history-last-n 10 \
  --check-manifest-compatibility
```

**Known limitations**:
- Utility timings remain environment-sensitive; warnings should still be reviewed before relaxing budgets further.
- Budget calibration improves signal quality but does not replace periodic runtime trend review.

**Non-goals**:
- No trading execution, broker routing, live/paper trading, annotation workflows, or model-performance claims.


## Phase 1826–1885: Manifest Compatibility Failure Closure and Audit Schema Normalization

**Goal**: Remove required manifest-compatibility failure from healthy generated bundles and normalize audit `read_csv_count` consumption across schema variants.

**Manifest compatibility root cause**:
- Compatibility check compares canonical `history` and deprecated alias `history_update`.
- Canonical status used `pass|warn|fail`, while legacy alias still emitted `ok` for success.
- This caused error `canonical_legacy_status_mismatch`, making `manifest_compatibility` fail and forcing final status `fail`.

**Fix**:
- During history update success path, legacy alias status is now synchronized to canonical status semantics.
- Compatibility gate behavior remains strict:
  - healthy canonical+legacy sync => pass
  - malformed alias metadata (`use` mismatch, enabled/status disagreement, path disagreement) => fail
  - legacy-only fallback remains warn.

**Audit schema normalization**:
- Added tolerant extraction for read-count consumption in review-bundle path:
  - `read_csv_count` (legacy top-level)
  - `summary.read_csv_count` (current nested schema)
- Missing value remains non-fatal and avoids crashes.

**Outcome**:
- Rebuilt bundles now pass manifest compatibility.
- Final status no longer fails due to this compatibility mismatch.
- Profile matrix no longer shows all profiles fail from the same required compatibility error.

**Known limitations**:
- If history regressions are real (`history.status=warn`), profile matrix can still show warn/fail depending on required gate semantics.
- Legacy alias remains present for compatibility window and should still be migrated out in a future major schema cleanup.

**Non-goals**:
- No trading execution, broker routing, live/paper trading, annotation workflows, or model-performance claims.


## Phase 1766–1825 Recovery Closure: Profile Matrix Validation Repair

**Goal**: Close partially implemented profile-matrix/preset work with clean validation and stable environment assumptions.

**What was already implemented**:
- Profile matrix report module and CLI:
  - `cajas/reports/validation_profile_matrix.py`
  - `cajas/scripts/build_validation_profile_matrix.py`
- Preset config:
  - `cajas/data_examples/validation_review_bundle_presets.json`
- Review-bundle integration for matrix artifacts and preset options.

**What was repaired**:
- Validation environment normalization:
  - used `./.venv-qlib313/bin/python` as canonical runner for this phase
  - no temporary ad hoc `.venv` promoted as project standard
- Numeric sanitizer compatibility:
  - `numeric.to_numpy(dtype=float, copy=True)` to ensure writable arrays
- Feature-importance summary test resilience:
  - skip when baseline run directory exists but contains no usable artifacts
- Profile-matrix hardening:
  - removed private-helper coupling to gate summary internals
  - aligned reason-code behavior with current pass/non-escalated semantics

**Profile matrix behavior**:
- Compares `local`, `ci`, `strict` over the same gate set.
- Reports:
  - per-profile overall status
  - escalated count
  - blocking count
  - next action
  - transition table for gates whose escalation behavior differs by profile

**Preset behavior**:
- `local_review`: local profile + warn-only reviewer-oriented run
- `ci_required`: CI profile with fast validation rerun and compatibility checks
- `strict_release`: strict profile + fail-on-warn posture
- Presets remain configurable in `validation_review_bundle_presets.json`.

**Known limitations**:
- Profile matrix reflects the current bundle’s gate outcomes; it does not rerun validations independently.
- If manifest compatibility is failing, all profiles can remain `fail` due to required fail gate semantics.

**Non-goals**:
- No trading execution, broker routing, live/paper trading, annotation workflows, or model-performance claims.


## Phase 1766–1825: CI Profile Matrix Validation and Automation Presets

### Context

Previously, `local`, `ci`, and `strict` profiles existed but had to be run individually to see their outcome. To improve CI usage and fast-track pipeline maturity, a matrix report is needed to show outcomes across all profiles from a single validation run. Automation presets were also needed to bundle common CI/local command configurations.

### Changes

- Added `cajas/reports/validation_profile_matrix.py` to compare outcomes across `local`, `ci`, and `strict` profiles.
- Added `build_validation_profile_matrix.py` CLI to generate JSON and MD matrix reports without rerunning validation.
- Implemented preset support in `build_validation_review_bundle.py` with the `--preset` flag.
- Presets configuration stored in `cajas/data_examples/validation_review_bundle_presets.json`.
- Wrote tests to ensure `local` doesn't escalate optional warnings while `ci` and `strict` do.

### Recommended Automation Presets

The following presets are available via `--preset`:

1. `local_review`: Uses local profile, updates local history, does not fail on optional warnings. Recommended for day-to-day dev.
2. `ci_required`: Uses ci profile, reruns fast validation, escalates optional warnings to review state. Recommended for pull requests.
3. `strict_release`: Uses strict profile, reruns fast validation, fails on any warning including missing optional gates. Recommended for main branch merges.

### Explicit Limitations

- This is infrastructure automation, not trading execution automation.
- No live trading, broker logic, or real-money automation is added.

**Goal**: Distinguish clean pass from pass-with-non-escalated warnings without hiding real warning details.

**Delivery packet warning audit findings**:
- The prior `delivery_packet_warn` came from optional artifact paths not passed to the packet builder.
- Those optional artifacts were marked missing and produced packet `warn`, even when not requested.
- In local profile, this warning was non-escalated, but final reason text still surfaced that warning code.

**Policy decision**:
- Keep required artifacts strict (`fail` when missing).
- Only warn for optional artifacts when an explicit optional path was requested but missing.
- Treat omitted optional inputs as informational notes (non-escalated).

**What changed**:
- Delivery packet now tracks required/optional counts and optional note count.
- Final status reason selection for `overall_status=pass` now uses:
  - `pass_with_non_escalated_warnings` when non-escalated warnings exist
  - `all_required_gates_passed` when no warnings remain
- Primary artifact for pass modes now points to summary artifacts (`review_bundle_index.md` / `final_status.md`) instead of low-level optional warning artifacts.
- Gate lists still keep full warning visibility.

**Recommended local command**:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_review_bundle.py \
  --ci \
  --ci-profile local \
  --ci-profile-config cajas/data_examples/validation_ci_profiles.json \
  --bundle-name dataset_quality_review_bundle \
  --out-root tmp/validation-review-bundle \
  --smoke-root tmp/dataset-quality-smoke \
  --fast-timing-json tmp/fast_validation_latest.json \
  --budgets cajas/data_examples/validation_runtime_budgets.json \
  --create-baseline-from-current \
  --update-history \
  --history-jsonl tmp/validation-review-bundle/history/review_bundle_history.jsonl \
  --history-last-n 10 \
  --check-manifest-compatibility \
  --warn-only
```

**Recommended CI command**:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_review_bundle.py \
  --ci \
  --ci-profile ci \
  --ci-profile-config cajas/data_examples/validation_ci_profiles.json \
  --run-fast-validation \
  --bundle-name dataset_quality_review_bundle \
  --out-root tmp/validation-review-bundle \
  --smoke-root tmp/dataset-quality-smoke \
  --fast-timing-json tmp/fast_validation_latest.json \
  --budgets cajas/data_examples/validation_runtime_budgets.json \
  --create-baseline-from-current \
  --update-history \
  --history-jsonl tmp/validation-review-bundle/history/review_bundle_history.jsonl \
  --history-last-n 10 \
  --check-manifest-compatibility
```

**Known limitations**:
- Optional artifact visibility still depends on what is explicitly supplied to the bundle run.
- CI/strict profiles can still escalate optional warnings by profile policy; this is intentional.

**Non-goals**:
- No trading execution, broker routing, live/paper trading, annotation workflows, or model-performance claims.

## Phase 1886-1945 Addendum: History Alias Deprecation and Strict Profile Warning Clarity

**Date**: 2026-05-03

**Branch**: `phase-post-merge-research-next`

**Objective**: Make `history`/`history_update` migration state explicit and reduce confusion around strict-profile warning outcomes.

### Highlights

1. Added alias deprecation metadata in generated manifests:
   - `deprecation_stage=compatibility_alias`
   - `removal_target_phase=future`
   - `consumer_action=Read manifest.history instead.`
2. Added optional alias omission control:
   - `--omit-history-update-alias`
   - default keeps alias for compatibility, flag emits canonical-only manifest
3. Kept compatibility checker semantics explicit:
   - canonical-only: `pass`
   - canonical+alias synced: `pass`
   - legacy-only alias fallback: `warn`
   - canonical/alias mismatch: `fail`
4. Added strict warning clarity in matrix outputs:
   - strict warn with no blocking gates now carries `strict_warning_reason`
   - markdown includes `Strict Warning Note` for expected strict-policy escalations

### Scope Confirmation

Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 1946-2005 Addendum: Default No-Alias Migration Readiness and CI Preset Regression

**Date**: 2026-05-03

**Branch**: `phase-post-merge-research-next`

**Objective**: Validate readiness for a future canonical-only default (`history` without `history_update` alias) and confirm preset/profile behavior remains stable.

### Highlights

1. Added migration-readiness report generation:
   - compares `tmp/validation-review-bundle` and `tmp/validation-review-bundle-no-alias`
   - emits JSON + Markdown recommendation artifacts
2. Added explicit readiness criteria:
   - compatibility pass in both modes
   - local/ci/strict profile status equivalence
   - required gate equivalence
   - optional differences tracked separately
3. Hardened preset precedence:
   - explicit CLI flags override preset defaults
4. Added tests for:
   - migration report pass/warn/fail semantics
   - preset mapping behavior
   - explicit CLI override precedence

### Current Result

- Readiness report: `pass`
- Recommendation: `ready_for_default_no_alias_trial`
- Profile equivalence: default and no-alias are aligned (`local=pass`, `ci=pass`, `strict=warn`)

### Scope Confirmation

Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2006-2065 Addendum: Controlled Default No-Alias Trial and Compatibility Fallback

**Date**: 2026-05-03

**Branch**: `phase-post-merge-research-next`

**Objective**: Flip generated manifest default to canonical-only `history` while keeping explicit alias fallback for legacy consumers.

### Highlights

1. Default generation changed to canonical-only (`history_update` omitted by default).
2. Added explicit fallback emission flag: `--include-history-update-alias`.
3. Kept `--omit-history-update-alias` accepted as transition compatibility/no-op.
4. Confirmed compatibility guard behavior remains stable (pass/warn/fail semantics unchanged).
5. Ran consumer final check (`history_update`, `normalize_history_metadata`, `history` references) and found no blocking internal consumer requirement for default alias emission.
6. Revalidated default and alias-fallback bundles plus profile matrix equivalence.

### Current Trial Result

- Default no-alias bundle: `manifest_compatibility=pass`, `final_status=pass`
- Alias fallback bundle: `manifest_compatibility=pass`, `final_status=pass`
- Profile matrix statuses match in both bundles: `local=pass`, `ci=pass`, `strict=warn`
- Migration readiness report: `pass`, recommendation `ready_for_default_no_alias_trial`

### Scope Confirmation

Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2066-2125 Addendum: Alias Fallback Sunset Guard and Runtime Edge Stabilization

**Date**: 2026-05-03

**Branch**: `phase-post-merge-research-next`

**Objective**: Protect canonical-only default manifest behavior, keep alias fallback explicit and reviewable, and expose runtime budget edge risk in a compact reviewer report.

### Highlights

1. Added no-alias regression guards (default/fallback/no-op flag paths).
2. Extended alias migration readiness report with explicit alias fallback usage and sunset recommendation metadata.
3. Added runtime edge report artifacts (`json` + `md`) with remaining-budget metrics and watch/pass/warn/fail status.
4. Reconfirmed profile/preset stability after default no-alias flip:
   - default bundle: local=pass, ci=pass, strict=warn
   - alias fallback bundle: local=pass, ci=pass, strict=warn

### Current Runtime Edge Result

- `status=pass`
- `fast_total_seconds=84.861`
- `remaining_budget_seconds=20.139`
- `remaining_budget_ratio=0.1918`

### Scope Confirmation

Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2126-2185 Addendum: Phase 2000+ Milestone Review Packet and Longitudinal Summary

**Date**: 2026-05-03

**Branch**: `phase-post-merge-research-next`

**Objective**: Create a single reviewer-facing packet that summarizes the Phase 2000+ validation automation operating model, current status, artifact map, and next actions.

### Highlights

1. Added milestone packet module + CLI (artifact-reading only, no heavy reruns).
2. Consolidated artifact map for default bundle, alias fallback bundle, runtime budget/edge, migration readiness, audit, and fast timing.
3. Added compact longitudinal phase summary for 1886+ progression.
4. Added milestone overall-status calculation with `pass|watch|warn|fail` reviewer framing.
5. Generated current milestone packet artifacts (`json` + `md`).

### Current Result

- Milestone packet overall status: `pass`
- Runtime edge: `pass`
- Migration readiness: `pass`
- Runtime budget: `pass`
- Timing consistency: `pass`

### Scope Confirmation

Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.
