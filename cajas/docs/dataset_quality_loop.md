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

## Phase 2846-2905 Addendum: Owner Response Candidate Review Workflow

### Confirmed-Clear Example

- Added:
  - `cajas/data_examples/history_alias_consumer_owner_response.confirmed_clear.example.json`
- Purpose:
  - provide a reviewer-friendly simulated `confirmed_clear` response.
  - keep example clearly non-production by note text and usage guidance.

### Owner Response Apply-to-Out Hardening

- `validate_consumer_owner_response.py` + report module now expose:
  - `candidate_written`
  - `candidate_output_path`
  - `manual_approval_required`
  - `do_not_auto_apply`
- Candidate write rules:
  - only when response is valid for application (`valid_ready_to_apply`).
  - invalid/incomplete payloads do not write candidate evidence output.

### Candidate Readiness Simulation

- New report:
  - `cajas/reports/validation_consumer_evidence_candidate.py`
  - `cajas/scripts/build_consumer_evidence_candidate_report.py`
- Simulated outputs under:
  - `tmp/simulated-confirmed-clear/`
- Decision framing:
  - `status=ready_candidate|blocked|invalid`
  - manual approval remains required.
  - report is explicit `do_not_auto_apply=true`.

### Readiness/Milestone Optional Candidate Note

- Release readiness optional input:
  - `--consumer-evidence-candidate-report`
- Milestone packet optional input:
  - `--consumer-evidence-candidate-report`
- Current behavior:
  - real readiness remains tied to real evidence (`watch`).
  - candidate projection can show potential `ready` if manually approved and applied.

### Validation Snapshot

- Focused tests:
  - owner response + candidate + readiness + milestone: pass
- Related phase suite:
  - `199 passed, 319 deselected`
- Fast validation:
  - `56.757s`, `overall_status=pass`
- Runtime budget:
  - `overall_status=pass`
- Data source audit:
  - `read_csv_count=29`

### Non-Goals

- No automatic overwrite of `cajas/data_examples/history_alias_external_consumers.json`.
- No automatic alias fallback removal.
- No trading execution expansion.

## Phase 2546-2605 Addendum: Pytest Runtime Profile and Fast Timing Reliability

**Date**: 2026-05-03

**Branch**: `phase-post-merge-research-next`

**Objective**: Produce actionable pytest-fast runtime profile artifacts, improve fast timing summary extraction reliability, and integrate profile signals into triage/readiness/milestone reviewers.

### Implemented Changes

1. Added runtime profile module + CLI:
   - `cajas/reports/validation_pytest_runtime_profile.py`
   - `cajas/scripts/profile_pytest_fast_runtime.py`
2. Improved `run_fast_validation.py` summary extraction:
   - capture subprocess stdout/stderr when possible.
   - extended summary fields to include skipped/xfailed/xpassed/errors.
3. Extended runtime watch triage:
   - optional `--pytest-runtime-profile`
   - includes profile status + slowest tests/files summaries.
4. Extended release readiness and milestone packet:
   - optional `--pytest-runtime-profile`
   - includes profile summary fields in output JSON/Markdown.
5. Added focused tests:
   - `cajas/tests/test_validation_pytest_runtime_profile.py`
   - updated runners/triage/readiness/milestone tests.

### Validation Snapshot

- Focused suites: pass
- Related suites: pass (`189 passed`, `319 deselected`)
- Fast validation: pass (`96.83s total`, `pytest_fast=92.79s`)
- Runtime budget: `pass`
- Timing consistency: `pass`
- Data-source audit: `read_csv_count=29`
- Hygiene: pass

### Runtime Findings

- Profile artifact now captures slowest tests/files and recommendation.
- Current run recovered from prior 109.788s spike, but remains above older baseline:
  - phase_2426 baseline: `88.418s`
  - current: `96.83s`
- Runtime watch triage currently remains `watch` with `optimize_slow_tests`.

### Known Limitations

- Summary extraction still conservatively returns null fields when output is unavailable; this is intentionally non-failing behavior.
- No test was removed from fast tier in this phase.

### Scope Confirmation

Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2606-2665 Addendum: Targeted Pytest Runtime Optimization and Edge-Warn Recovery

**Date**: 2026-05-03

**Branch**: `phase-post-merge-research-next`

**Objective**: Use runtime-profile evidence to apply narrow, safe test-level optimizations and recover runtime-edge status without weakening validation.

### Slowest-Test Findings (Profile)

Initial top slow tests were dominated by one-off CLI subprocess tests, including:
- `test_build_no_broker_dry_run_packet_cli.py`
- `test_build_qlib_model_training_contract_cli.py`
- `test_build_qlib_dataset_contract_cli.py`
- `test_build_qlib_compatibility_report_cli.py`
- `test_build_research_decision_packet_cli.py`
- `test_build_final_readiness_summary_cli.py`
- `test_build_qlib_integration_packet_cli.py`
- `test_build_stable_fingerprint_cli.py`

Pattern:
- many tests spent time in Python process startup + script bootstrap rather than core assertion logic.

### Optimization Applied

1. Converted selected CLI tests to direct `main(argv)` calls.
2. Updated corresponding script entrypoints so `main(argv: list[str] | None = None)` is supported.
3. Preserved behavior assertions (output files/status checks); no gate removal and no coverage downgrading.

### Validation and Runtime Outcome

- Targeted optimized test set: pass (`8 passed`)
- Focused runtime/profile/watch/readiness/milestone tests: pass
- Related suite: pass (`189 passed`, `319 deselected`)
- Fast validation: `78.623s` total (`pytest_fast=73.181s`)
- Runtime budget: `pass`
- Timing consistency: `pass`
- Runtime edge: `pass`
- Runtime variance: `pass`
- Runtime watch triage: `pass` (`runtime_variance`, recommendation `monitor`)
- Data-source audit: `read_csv_count=29`
- Hygiene: pass

### Before/After Snapshot

- Previous phase reference: `96.83s` fast total
- Current after optimization: `78.623s`
- Delta: `-18.207s`

### Remaining Constraints

- Alias fallback removal remains blocked by unresolved external consumer evidence (`blocking_consumer_count=1`).
- Readiness remains `watch` for consumer-evidence reasons, not runtime reasons.

### Scope Confirmation

Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2666-2725 Addendum: Runtime Optimization Round 2 and External Consumer Closure Path

**Date**: 2026-05-03

**Branch**: `phase-post-merge-research-next`

**Objective**: Preserve runtime edge pass-state with a second safe hotspot pass and make the remaining external consumer blocker operationally explicit.

### Round-2 Slowest-Test Findings

Current top profile hotspots after prior rounds:
- `test_baseline_runner.py::...::test_training_and_model_actions_are_disabled`
- several remaining single-test CLI wrappers (`build_artifact_lineage`, `build_final_readiness_packet`, `build_final_research_bundle`, etc.)
- runtime/data audit tests remained in the top set before round-2 optimization.

### Optimization Applied

1. Updated audit CLIs to support direct call testing:
   - `cajas/scripts/audit_data_sources.py` -> `main(argv)`
   - `cajas/scripts/audit_validation_runtime.py` -> `main(argv)`
2. Converted audit CLI tests from subprocess to direct `main(argv)`:
   - `cajas/tests/test_data_source_audit.py`
   - `cajas/tests/test_validation_runtime_audit.py`
3. Preserved output assertions and status checks; no assertion weakening.

### Consumer Evidence Closure Path Improvement

Updated `validation_consumer_evidence_closure` report surface:
- added `closure_checklist` in JSON and Markdown.
- markdown now contains `## Closure Checklist` with explicit required actions:
  - identify owner for unresolved consumer
  - confirm `manifest.history` dependency
  - keep fallback + migration item if alias required
  - update evidence fields when confirmed clear

### Validation Snapshot

- Focused modified suites: pass
- Required phase focused suites: pass
- Related suite: pass (`189 passed`, `319 deselected`)
- Fast validation: pass (`79.427s total`, `pytest_fast=70.796s`)
- Runtime budget: `pass`
- Timing consistency: `pass`
- Runtime edge: `pass`
- Runtime variance: `pass`
- Runtime watch triage: `pass`
- Data-source audit: `read_csv_count=29`
- Hygiene: pass

### Runtime Comparison

- Phase 2546 baseline: `96.83s`
- Phase 2606 baseline: `78.623s`
- Current: `79.427s`

Result:
- runtime remains healthy (`edge=pass`) with substantial margin vs Phase 2546.
- small variance vs Phase 2606 is within pass-state triage (`runtime_variance=pass`).

### Consumer Closure / Readiness State

- consumer evidence closure: `incomplete` (`unresolved_count=1`, `blocking_consumer_count=1`)
- alias sunset review: `watch`, action `collect_consumer_evidence`
- release readiness: `watch` (evidence/alias reasons)
- milestone packet: `watch`

### Scope Confirmation

Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2726-2785 Addendum: Remaining CLI Hotspot Optimization and Consumer Owner Handoff

**Date**: 2026-05-03

**Branch**: `phase-post-merge-research-next`

**Objective**: Convert remaining safe CLI wrapper hotspots, review baseline runner hotspot behavior, and introduce an owner-facing handoff packet for unresolved external consumer closure.

### Remaining Hotspot Findings

Pre-change hotspot candidates included:
- `test_build_artifact_lineage_cli`
- `test_build_final_readiness_packet_cli`
- `test_build_final_research_bundle_cli`
- `test_build_candidate_promotion_manifest_cli`
- `test_baseline_runner`

After this phase profile:
- top hotspot remains `test_baseline_runner` (~3.64s)
- several next hotspots moved to other CLI tests not yet converted
- converted wrapper tests dropped out of the top list

### Runtime Optimization Applied

1. Added `main(argv)` support for:
   - `build_artifact_lineage.py`
   - `build_final_readiness_packet.py`
   - `build_final_research_bundle.py`
   - `build_candidate_promotion_manifest.py`
2. Converted corresponding CLI tests to direct function invocation.
3. Baseline runner test fixture optimization:
   - replaced pandas-generated CSV fixture with direct compact CSV text write.
   - preserved disabled-training behavioral assertions.

### Consumer Owner Handoff Packet

Added owner-facing unresolved-consumer handoff artifacts:
- module: `cajas/reports/validation_consumer_owner_handoff.py`
- CLI: `cajas/scripts/build_consumer_owner_handoff.py`
- outputs:
  - `tmp/history-alias-consumer-owner-handoff.json`
  - `tmp/history-alias-consumer-owner-handoff.md`

Behavior:
- status is `open` when unresolved consumers remain.
- status is `blocked` when a consumer still requires alias.
- status is `ready` when no unresolved blockers remain.
- markdown includes a copyable owner message with required evidence checklist.

### Readiness/Milestone Integration

Added optional owner handoff integration:
- release readiness: `--consumer-owner-handoff`
- milestone packet: `--consumer-owner-handoff`

Summaries now surface:
- owner handoff status
- blocking consumer count
- handoff items

### Validation Snapshot

- Converted CLI test set: pass
- Required focused suites: pass
- Related suite: pass (`192 passed`, `319 deselected`)
- Fast validation: pass (`66.579s total`, `pytest_fast=59.935s`)
- Runtime budget: `pass`
- Timing consistency: `pass`
- Runtime edge: `pass`
- Runtime variance: `pass`
- Runtime watch triage: `pass`
- Data-source audit: `read_csv_count=29`
- Hygiene: pass

### Runtime Comparison

- Phase 2606 baseline: `78.623s`
- Phase 2666 baseline: `79.427s`
- Current: `66.579s`

### Consumer Closure State

- consumer evidence closure: `incomplete`
- consumer owner handoff: `open` (one blocking unresolved external consumer)
- release readiness: `watch` (evidence/owner handoff reasons)
- milestone packet: `watch`

### Scope Confirmation

Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2786-2845 Addendum: Remaining CLI-Heavy Wrappers and Owner Response Intake

**Date**: 2026-05-03

**Branch**: `phase-post-merge-research-next`

**Objective**: Convert remaining safe CLI-heavy wrappers and add an owner-response intake workflow that validates response quality before any evidence update.

### Runtime Findings and CLI Targets

Targeted hotspots in this phase:
- `test_train_qlib_model_bridge_baseline_cli`
- `test_compare_qlib_model_runs_cli`
- `test_dataset_quality_research_bundle` CLI path
- `test_io_runtime_audit` CLI path

Actions:
- added `main(argv)` support where needed.
- converted subprocess-based CLI tests to direct function calls.
- preserved output assertions and non-trading scope semantics.

### Baseline Runner Review

- `test_baseline_runner` remains the top single-test hotspot.
- no additional assertion-lowering optimization was applied this phase; it remains a monitored heavy path.

### Owner Response Intake Workflow

Added owner response example schema:
- `cajas/data_examples/history_alias_consumer_owner_response.example.json`

Added validation report flow:
- module: `cajas/reports/validation_consumer_owner_response.py`
- CLI: `cajas/scripts/validate_consumer_owner_response.py`
- output:
  - `tmp/history-alias-consumer-owner-response-validation.json`
  - `tmp/history-alias-consumer-owner-response-validation.md`

Validation behavior:
- `confirmed_clear`: requires owner/evidence/last_checked and `requires_history_update=false`
- `requires_alias`: requires owner/evidence and `requires_history_update=true`
- `unknown`: remains `incomplete` unless upgraded by owner response data
- unknown consumer id => `invalid`
- optional `--apply-to-out` supported for writing a candidate updated evidence file only when safe
- default behavior never mutates real evidence file

### Readiness/Milestone Integration

Integrated optional `--consumer-owner-response-validation` into:
- release readiness builder/report
- milestone packet builder/report

Outputs now surface:
- owner response status
- safe-to-update flag
- validation issues list

### Validation Snapshot

- Focused suites: pass (including new owner-response tests)
- Converted CLI tests: pass
- Related suite: pass (`196 passed`, `319 deselected`)
- Fast validation: pass (`59.314s total`, `pytest_fast=51.599s`)
- Runtime budget: `pass`
- Timing consistency: `pass`
- Runtime edge: `pass`
- Runtime variance: `pass`
- Runtime watch triage: `pass`
- Data-source audit: `read_csv_count=29`
- Hygiene: pass

### Runtime Comparison

- Phase 2666 baseline: `79.427s`
- Phase 2726 baseline: `66.579s`
- Current: `59.314s`

### Current Alias/Evidence Status

- owner handoff: `open`
- owner response validation (example): `incomplete`
- consumer evidence closure: `incomplete`
- release readiness: `watch` (owner/evidence reasons)
- milestone packet: `watch`

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

## Phase 2186-2245 Addendum: External Consumer Alias Sunset Review and Release-Cycle Runtime Monitoring

**Date**: 2026-05-03

**Branch**: `phase-post-merge-research-next`

**Objective**: Add a conservative external-consumer alias sunset checklist and a repeatable release-cycle runtime monitor, then surface both in milestone packet review outputs.

### Highlights

1. Added alias sunset review report with external-consumer status options:
   - `unknown`
   - `confirmed_clear`
   - `requires_alias`
2. Added runtime release-cycle monitor report based on runtime-edge + budget + fast timing.
3. Extended milestone packet to include optional alias-sunset/runtime-cycle summaries.
4. Kept alias fallback in place for this phase (no removal).

### Current Results

- Alias sunset review: `watch` (external consumer status unknown)
- Runtime release-cycle monitor: `pass`
- Milestone packet overall status: `watch` (conservative due alias sunset watch)

### Scope Confirmation

Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2246-2305 Addendum: External Consumer Evidence and Runtime Variance Triage

**Date**: 2026-05-03

**Branch**: `phase-post-merge-research-next`

**Objective**: Move alias sunset review from status-only input to evidence-aware review while adding runtime variance triage and integrating both into release-cycle and milestone reporting.

### Highlights

1. Added consumer evidence example file:
   - `cajas/data_examples/history_alias_external_consumers.json`
2. Extended alias sunset review to ingest evidence file and derive evidence counts.
3. Kept explicit CLI override precedence:
   - `--external-consumer-status` overrides evidence-file status for the current run.
4. Added runtime variance triage report module and CLI.
5. Extended runtime release-cycle report to consume variance status.
6. Extended milestone packet to include runtime variance summary.

### Current Outputs

- `tmp/history-alias-sunset-review.json`
- `tmp/history-alias-sunset-review.md`
- `tmp/validation-runtime-variance-report.json`
- `tmp/validation-runtime-variance-report.md`
- `tmp/validation-runtime-release-cycle-report.json`
- `tmp/validation-runtime-release-cycle-report.md`
- `tmp/validation-milestone-packet.json`
- `tmp/validation-milestone-packet.md`

### Current Results

- Alias sunset review:
  - status: `watch`
  - action: `keep_fallback`
  - reason: unresolved external consumer evidence remains.
- Runtime variance triage:
  - status: `pass`
  - `current_fast_total_seconds=88.806`
  - largest delta vs baselines: `+3.945s` (`+4.65%`), below `10%` watch threshold.
- Runtime release-cycle:
  - status: `pass`
  - recommendation: `ok`
  - trigger: `manual_next_release`
- Milestone packet:
  - overall status: `watch`
  - primary watch driver: alias sunset unresolved external consumer evidence.

### Known Limitations

- Alias fallback sunset remains blocked on external consumer confirmation.
- Runtime variance classification is baseline-dependent; trend tracking must continue across future cycles.

### Scope Confirmation

Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2306-2365 Addendum: Alias Sunset Decision Gate and Release Readiness Dashboard

**Date**: 2026-05-03

**Branch**: `phase-post-merge-research-next`

**Objective**: Convert milestone `watch` posture into an actionable release-readiness workflow with explicit alias sunset evidence requirements and next actions.

### Highlights

1. Added external consumer confirmation template:
   - `cajas/data_examples/history_alias_external_consumers.template.json`
2. Extended alias sunset review with a structured `decision_gate` block.
3. Added release-readiness dashboard report and CLI:
   - `cajas/reports/validation_release_readiness.py`
   - `cajas/scripts/build_validation_release_readiness_report.py`
4. Extended milestone packet with optional `--release-readiness-report` integration.
5. Updated phase tests to cover `ready|watch|blocked` readiness flow and actionable next actions.

### Decision Gate Rules

- `ready` only when:
  - migration readiness is `pass`
  - milestone packet is not `fail`
  - external status is `confirmed_clear`
  - unresolved consumers are `0`
  - consumers requiring alias are `0`
- `blocked` when:
  - any consumer still requires alias, or
  - migration readiness fails, or
  - milestone packet fails
- `watch` for unresolved/unknown external evidence cases.

### Current Outputs

- `tmp/history-alias-sunset-review.json`
- `tmp/history-alias-sunset-review.md`
- `tmp/validation-release-readiness.json`
- `tmp/validation-release-readiness.md`
- `tmp/validation-runtime-variance-report.json`
- `tmp/validation-runtime-release-cycle-report.json`
- `tmp/validation-milestone-packet.json`
- `tmp/validation-milestone-packet.md`

### Current Results

- Alias sunset decision gate:
  - status: `watch`
  - recommended action: `collect_consumer_evidence`
  - unresolved consumers: `1`
- Release readiness:
  - status: `watch`
  - reason: `alias_sunset_decision_gate=watch`
  - next actions: `collect_consumer_evidence`, `keep_fallback`
- Runtime health:
  - runtime variance: `pass`
  - runtime release-cycle: `pass`
  - runtime budget: `pass`
  - timing consistency: `pass`

### Known Limitations

- Current external evidence includes unresolved consumers, so alias fallback sunset remains deferred.
- Release readiness remains `watch` until external-consumer confirmation is complete.

### Scope Confirmation

Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2366-2425 Addendum: Evidence Closure Workflow and Alias Removal Planning

**Date**: 2026-05-03

**Branch**: `phase-post-merge-research-next`

**Objective**: Add a concrete evidence-closure workflow and a structured alias-removal planning packet while preserving the no-removal-in-this-phase boundary.

### Highlights

1. Added confirmed-clear simulation evidence:
   - `cajas/data_examples/history_alias_external_consumers.confirmed_clear.example.json`
2. Added alias removal plan report and CLI:
   - `cajas/reports/validation_alias_removal_plan.py`
   - `cajas/scripts/build_alias_removal_plan.py`
3. Added simulated confirmed-clear artifact path:
   - `tmp/simulated-confirmed-clear/`
4. Extended release readiness with optional alias-removal-plan input:
   - `--alias-removal-plan`
5. Extended milestone packet with optional alias-removal-plan summary:
   - `--alias-removal-plan`
6. Added tests for real/watch vs simulated/ready-to-schedule transitions.

### Real vs Simulated Outcomes

- Real evidence (`history_alias_external_consumers.json`):
  - alias sunset: `watch`
  - alias removal plan: `not_ready`
  - release readiness: `watch`
- Simulated confirmed-clear evidence (`*.confirmed_clear.example.json`):
  - alias sunset: `ready`
  - alias removal plan: `ready_to_schedule`

### Current Runtime Context

- Fast validation total: `94.03s`
- Runtime budget: `pass`
- Runtime edge: `watch`
- Runtime release-cycle: `watch`
- Runtime variance: `pass`

### Non-Goal

- This phase does not remove `--include-history-update-alias`. It only prepares and validates the removal-plan packet workflow.

### Scope Confirmation

Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2426-2485 Addendum: Real Evidence Closure and Runtime Watch Recovery

**Date**: 2026-05-03

**Branch**: `phase-post-merge-research-next`

**Objective**: Make unresolved consumer evidence fully actionable and add runtime watch triage so readiness can distinguish evidence-watch from runtime-watch.

### Highlights

1. Added real evidence action fields in `history_alias_external_consumers.json`.
2. Added consumer evidence closure report:
   - `cajas/reports/validation_consumer_evidence_closure.py`
   - `cajas/scripts/build_consumer_evidence_closure_report.py`
3. Added runtime watch triage report:
   - `cajas/reports/validation_runtime_watch_triage.py`
   - `cajas/scripts/build_validation_runtime_watch_triage_report.py`
4. Extended release readiness with optional closure/triage summaries.
5. Extended milestone packet with optional closure/triage summaries.

### Real Current Evidence Outcome

- Consumer evidence closure: `incomplete`
- unresolved consumer count: `1`
- next action: `identify_owner`
- evidence completeness ratio: `0.5`

### Runtime Watch Outcome

- Runtime watch triage: `pass`
- likely cause: `runtime_variance`
- recommendation: `monitor`
- Current run recovered edge/release-cycle from prior watch back to `pass`.

### Non-Goal

- No alias fallback removal is performed in this phase.

### Scope Confirmation

Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.

## Phase 2486-2545 Addendum: Owner/Action Closure and Test-Count Observability

**Date**: 2026-05-03

**Branch**: `phase-post-merge-research-next`

**Objective**: Make unresolved consumer evidence explicitly owner/action-driven and add test-count observability into timing + runtime triage reports.

### Highlights

1. Updated unresolved consumer owner/action metadata in real evidence file.
2. Extended consumer evidence closure report with explicit `action_plan` and blocking-owner counts.
3. Added conservative `test_summary` extraction to fast timing JSON.
4. Extended runtime watch triage with `test_count`, `tests_deselected`, and `seconds_per_test`.
5. Extended release readiness and milestone packet to surface evidence action plan and runtime test-count fields.

### Current Outcome

- Real consumer evidence remains `incomplete`; one unresolved blocking consumer still requires owner confirmation.
- Runtime in latest run moved to warn state due higher observed timing (`fast_total=109.788s`).
- Runtime watch triage reports `warn` with recommendation `optimize`.

### Evidence Promotion Path

- Tests validate that simulated promotion to `confirmed_clear` with complete fields can reach closure-complete state without changing real evidence.

### Known Limitation

- `test_summary` extraction is conservative; when pytest output is not captured by the runner, test-count fields remain `null` instead of failing the run.

### Scope Confirmation

Offline Qlib validation automation only. No trading execution, broker routing, live/paper trading, annotation loops, or Qlib core modifications.
