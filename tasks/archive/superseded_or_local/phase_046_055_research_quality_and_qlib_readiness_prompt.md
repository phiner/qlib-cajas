# Phase 46-55 Prompt: Feature Engineering, Calibration, Stability, Cross-Year Validation, and Qlib Integration Readiness

## Codex Communication Rules

- Communicate with the user in English only.
- All progress updates, questions, command summaries, and completion reports must be written in English.
- Do not use Chinese in Codex-facing interaction unless the user explicitly asks.
- Do not run `git push`.
- Stop after local commits and report the exact `git push` command for the user to run manually.

## Repository

Repository working directory:

```text
/home/phiner/projects/research/qlib-cajas/
```

Current branch:

```text
cajas/market-recognition-phase-0
```

## Current Project Direction

The project supports controlled local market-recognition classification baseline training.

Important:

- This is market-recognition research only.
- This is not a trading strategy.
- `future_direction_*` labels are classification labels, not buy/sell signals.
- Label thresholds are classification label thresholds only, not trading thresholds.
- Qlib workflow execution remains disabled unless explicitly approved in a future phase.
- Trading/backtest/profit analysis remains forbidden.

## Expected Prior State

Phase 41-45 is expected to add:

- threshold label variants
- horizon-specific label experiments
- binary drop-flat baseline
- label variant comparison
- label decision report

If Phase 41-45 is not fully complete yet, do not skip it silently. First inspect the repository and only build on completed files. If a dependency is missing, implement a safe bounded subset and report what was deferred.

## Phase 46-55 Goal

This combined phase should move from label redesign into research-quality model improvement and integration readiness.

### Phase 46: K-Line Structure Feature Expansion

Add richer K-line and rolling structure features for prepared datasets:

- candle body ratio
- upper/lower wick ratio
- close location in bar
- rolling high-low range position
- rolling return mean/std for additional windows
- rolling efficiency ratio
- simple trend slope features
- volatility-normalized movement features

These are market-recognition features only, not trading rules.

### Phase 47: Feature Set Versioning

Add feature set manifests and versioning:

- `minimal_v1`
- `structure_v1`
- `structure_plus_rolling_v1`

Allow local baseline training to choose feature set.

### Phase 48: Feature Set External Holdout Comparison

Train/evaluate selected label variant with multiple feature sets using:

- train: 2020-2024
- holdout: 2025

Classification-only metrics.

### Phase 49: Probability Calibration Analysis

Analyze probability calibration for holdout predictions:

- confidence buckets
- expected calibration error style summary
- reliability table
- optional sklearn calibration only if safe and local

No trading thresholds.

### Phase 50: Model Stability Across Seeds

Run selected model/label/feature set across multiple random seeds:

- e.g. 7, 21, 42, 84, 168
- summarize mean/std of classification metrics
- identify unstable configurations

### Phase 51: Rolling Year Validation Preview

Create a rolling-year validation plan using available 2020-2025 data:

- train 2020-2021, validate 2022
- train 2020-2022, validate 2023
- train 2020-2023, validate 2024
- train 2020-2024, validate 2025

Run only if efficient; otherwise generate plan and dataset previews.

### Phase 52: Error Slice Analysis

Slice holdout errors by:

- hour of day if datetime available
- day of week if datetime available
- volatility bucket
- range/body bucket
- confidence bucket

Classification QA only.

### Phase 53: Data Quality and Leakage Audit v2

Add stricter audit:

- no future-return columns in features
- no selected label columns in features
- no future close columns in features
- no train/holdout datetime overlap
- feature distribution drift summary between train and holdout

### Phase 54: Qlib Integration Readiness Report v2

Create a readiness report for whether the current research layer is ready for controlled Qlib workflow integration.

Do not initialize or execute Qlib.

### Phase 55: Research Roadmap Report

Generate a concise roadmap report:

- what is solid
- what is weak
- recommended next experiments
- what still blocks trading/backtest discussion

No trading strategy recommendations.

## Absolute Boundaries

Allowed in this phase:

- Local feature engineering.
- Local classification model training.
- Local holdout evaluation.
- Local calibration/stability/error-slice analysis.
- Local report generation under `tmp/`.

Forbidden in this phase:

1. Do not modify `qlib/` core.
2. Do not modify official upstream examples.
3. Do not initialize Qlib.
4. Do not execute Qlib workflow.
5. Do not commit raw EURUSD CSV files.
6. Do not commit `tmp/` generated outputs.
7. Do not commit `.codex/`.
8. Do not add `tasks/` to `.gitignore`.
9. Do not create new task prompt directories.
10. Do not describe any `future_direction_*` label as a buy/sell signal.
11. Do not describe thresholds or probabilities as trading thresholds.
12. Do not run backtest/profit/return analysis.
13. Do not calculate trading metrics such as profit, return, Sharpe, drawdown, PnL, win rate, or trade expectancy.
14. Do not add trading strategy, live execution, broker execution, auto order, or position sizing logic.
15. Do not install new runtime dependencies automatically.
16. Do not run `git push`.

## Task 1: Check State

Run:

```bash
git status --short
git branch --show-current
grep -n "tasks" .gitignore || true
find cajas -path "*/init.py" -print
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py --json
```

Expected:

- Current branch is `cajas/market-recognition-phase-0`.
- `.gitignore` should not ignore `tasks/`.
- `find cajas -path "*/init.py" -print` must produce no output.
- path hygiene should return 0 issues.

## Task 2: Inspect Phase 41-45 Availability

Check whether these files exist:

```text
cajas/datasets/threshold_label_generator.py
cajas/datasets/label_variant_dataset.py
cajas/baseline/label_variant_trainer.py
cajas/reports/label_variant_comparison.py
cajas/reports/label_decision_report.py
```

If they exist, build on them.

If they do not exist, do not reimplement all Phase 41-45 here unless necessary. Report dependency missing and implement only parts that do not depend on them, but still commit useful infrastructure.

## Task 3: Add K-Line Structure Feature Builder

Add:

```text
cajas/features/__init__.py
cajas/features/kline_structure_features.py
```

Purpose:

- Generate additional K-line structure features from prepared dataset rows.
- Preserve source prepared CSV unchanged.
- Write derived feature datasets under `tmp/`.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class KlineFeatureBuildReport:
    input_path: str
    output_path: str | None
    input_rows: int
    output_rows: int
    added_features: list[str]
    warnings: list[str]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def add_kline_structure_features(
    *,
    input_path: str | Path,
    output_path: str | Path | None = None,
    windows: list[int] | None = None,
) -> tuple:
    # Return (features_df, report).
    ...
```

Default windows:

```text
4, 8, 16, 32
```

Feature examples:

```text
body_abs
body_ratio
upper_wick
lower_wick
upper_wick_ratio
lower_wick_ratio
close_location
range_over_close
return_1
return_mean_4
return_mean_8
return_mean_16
return_std_4
return_std_8
return_std_16
rolling_range_pos_8
rolling_range_pos_16
rolling_range_width_8
rolling_range_width_16
efficiency_ratio_8
efficiency_ratio_16
slope_8
slope_16
atr_like_8
atr_like_16
```

Rules:

- Avoid future-looking features.
- Rolling features must use current/past rows only.
- Do not create trading signals.
- Do not calculate profit/returns as trading metrics. Basic historical returns as features are allowed.

## Task 4: Add Feature Builder CLI

Add:

```text
cajas/scripts/build_kline_features.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_kline_features.py   --input tmp/cajas/eurusd_15m_2020_2024_phase35_train/prepared_dataset.csv   --output tmp/cajas/feature_sets/phase46_train_structure_features.csv   --window 4   --window 8   --window 16   --window 32   --report-output tmp/cajas/feature_sets/phase46_train_structure_features_report.json   --json
```

Also run for 2025 holdout.

## Task 5: Add Feature Set Registry

Add:

```text
cajas/features/feature_set_registry.py
```

Purpose:

- Define feature set names and included column patterns.
- Allow trainers to select a feature set.

Suggested feature sets:

```text
minimal_v1:
  existing 24 baseline features

structure_v1:
  baseline + body/wick/close-location/range-position features

structure_plus_rolling_v1:
  structure_v1 + rolling mean/std/slope/efficiency/atr-like features
```

Suggested functions:

```python
def list_feature_sets() -> dict:
    ...

def resolve_feature_columns_for_set(
    *,
    all_columns: list[str],
    feature_set: str,
    label_col: str,
) -> list[str]:
    ...
```

Rules:

- Never include label columns.
- Never include future-derived columns:
  - `future_close_*`
  - `future_return_*`
  - `future_direction_*`
- Never include non-numeric metadata columns unless explicitly allowed.

## Task 6: Add Feature Set Comparison Trainer

Add:

```text
cajas/baseline/feature_set_comparison.py
```

Purpose:

- Train external holdout baselines using different feature sets.
- Use a selected label column from previous label decision if available; otherwise default to `future_direction_8`.
- Keep classification-only metrics.

Suggested function:

```python
def run_feature_set_comparison(
    *,
    train_path: str | Path,
    holdout_path: str | Path,
    label_col: str,
    feature_sets: list[str],
    output_dir: str | Path,
    run_name: str,
    model_family: str = "LightGBM",
    random_state: int = 42,
) -> dict:
    ...
```

Artifacts:

```text
feature_set_comparison_report.json
feature_set_comparison.csv
```

Add CLI:

```text
cajas/scripts/compare_feature_sets.py
```

## Task 7: Add Calibration Analysis

Add:

```text
cajas/baseline/calibration_analysis.py
```

Purpose:

- Analyze probability calibration from existing prediction files.
- Classification-only.

Suggested metrics:

- confidence bucket accuracy
- mean confidence by bucket
- absolute gap by bucket
- ECE-like weighted average gap

Suggested function:

```python
def analyze_calibration(
    *,
    prediction_csv: str | Path,
    split: str,
    bucket_count: int = 10,
) -> dict:
    ...
```

Artifacts:

```text
calibration_report.json
calibration_buckets.csv
```

Add CLI:

```text
cajas/scripts/analyze_calibration.py
```

Rules:

- Do not convert calibration into trading thresholds.
- Do not recommend actions.

## Task 8: Add Seed Stability Runner

Add:

```text
cajas/baseline/seed_stability.py
```

Purpose:

- Run selected external holdout training across multiple random seeds.
- Summarize mean/std classification metrics.

Suggested seeds:

```text
7, 21, 42, 84, 168
```

Suggested function:

```python
def run_seed_stability_experiment(
    *,
    train_path: str | Path,
    holdout_path: str | Path,
    label_col: str,
    output_dir: str | Path,
    run_name: str,
    seeds: list[int],
    model_family: str = "LightGBM",
) -> dict:
    ...
```

Artifacts:

```text
seed_stability_report.json
seed_stability_metrics.csv
```

Add CLI:

```text
cajas/scripts/run_seed_stability.py
```

## Task 9: Add Rolling Year Validation Plan

Add:

```text
cajas/validation/__init__.py
cajas/validation/rolling_year_plan.py
```

Purpose:

- Build a rolling year validation plan for 2020-2025 data.
- Generate plan JSON and optional prepared split references.
- Do not run all heavy training unless explicitly requested.

Suggested plan:

```text
train_2020_2021_validate_2022
train_2020_2022_validate_2023
train_2020_2023_validate_2024
train_2020_2024_validate_2025
```

Add CLI:

```text
cajas/scripts/build_rolling_year_validation_plan.py
```

Artifacts:

```text
rolling_year_validation_plan.json
rolling_year_validation_plan.csv
```

## Task 10: Add Error Slice Analysis

Add:

```text
cajas/baseline/error_slice_analysis.py
```

Purpose:

- Analyze classification errors by metadata and feature buckets.
- Use prediction artifact and, if needed, corresponding feature artifact.

Slices:

- hour of day
- day of week
- confidence bucket
- range/body bucket if columns available
- volatility bucket if columns available

Artifacts:

```text
error_slice_report.json
error_slices.csv
```

Add CLI:

```text
cajas/scripts/analyze_error_slices.py
```

Rules:

- Classification QA only.
- No trading sessions/rules recommendations.

## Task 11: Add Leakage/Drift Audit v2

Add:

```text
cajas/audits/leakage_drift_audit.py
```

Purpose:

- Audit feature lists and train/holdout distributions.
- Detect future-derived columns in features.
- Detect train/holdout overlap.
- Summarize simple distribution drift between train and holdout.

Artifacts:

```text
leakage_drift_audit_report.json
feature_drift_summary.csv
```

Add CLI:

```text
cajas/scripts/audit_leakage_and_drift.py
```

## Task 12: Add Qlib Readiness Report v2

Add:

```text
cajas/reports/qlib_readiness_report.py
```

Purpose:

- Summarize whether the current research layer is ready for controlled Qlib workflow integration.
- Do not initialize or execute Qlib.

Sections:

- data readiness
- label readiness
- feature readiness
- model baseline readiness
- artifact/report readiness
- unresolved blockers
- recommended integration path

Add CLI:

```text
cajas/scripts/build_qlib_readiness_report.py
```

## Task 13: Add Research Roadmap Report

Add:

```text
cajas/reports/research_roadmap_report.py
```

Purpose:

- Summarize current research status and next experiments.
- Keep explicit boundary that trading/backtest discussion remains blocked until label/model quality improves.

Add CLI:

```text
cajas/scripts/build_research_roadmap_report.py
```

## Task 14: Extend YAML Config

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Add sections:

```yaml
feature_engineering:
  enabled: true
  phase: phase46
  windows: [4, 8, 16, 32]
  output:
    default_output_dir: tmp/cajas/feature_sets

feature_set_comparison:
  enabled: true
  phase: phase48
  feature_sets:
    - minimal_v1
    - structure_v1
    - structure_plus_rolling_v1
  output:
    default_output_dir: tmp/cajas/feature_set_comparisons
    default_run_name: phase48_feature_set_comparison

calibration_analysis:
  enabled: true
  phase: phase49
  bucket_count: 10
  output:
    default_output_dir: tmp/cajas/calibration_analysis
    default_run_name: phase49_calibration_analysis

seed_stability:
  enabled: true
  phase: phase50
  seeds: [7, 21, 42, 84, 168]
  output:
    default_output_dir: tmp/cajas/seed_stability
    default_run_name: phase50_seed_stability

rolling_year_validation:
  enabled: true
  phase: phase51
  output:
    default_output_dir: tmp/cajas/rolling_year_validation
    default_run_name: phase51_rolling_year_plan

error_slice_analysis:
  enabled: true
  phase: phase52
  output:
    default_output_dir: tmp/cajas/error_slice_analysis
    default_run_name: phase52_error_slice_analysis

leakage_drift_audit:
  enabled: true
  phase: phase53
  output:
    default_output_dir: tmp/cajas/leakage_drift_audits
    default_run_name: phase53_leakage_drift_audit

qlib_readiness_report:
  enabled: true
  phase: phase54
  output:
    default_output_dir: tmp/cajas/qlib_readiness_reports
    default_run_name: phase54_qlib_readiness_report

research_roadmap_report:
  enabled: true
  phase: phase55
  output:
    default_output_dir: tmp/cajas/research_roadmap_reports
    default_run_name: phase55_research_roadmap_report
```

## Task 15: Add Tests

Add focused tests for new modules:

```text
cajas/tests/test_kline_structure_features.py
cajas/tests/test_feature_set_registry.py
cajas/tests/test_feature_set_comparison.py
cajas/tests/test_calibration_analysis.py
cajas/tests/test_seed_stability.py
cajas/tests/test_rolling_year_plan.py
cajas/tests/test_error_slice_analysis.py
cajas/tests/test_leakage_drift_audit.py
cajas/tests/test_qlib_readiness_report.py
cajas/tests/test_research_roadmap_report.py
```

Tests should use small fixtures and avoid long runs.

## Task 16: Update Documentation

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

Document Phase 46-55:

- feature engineering
- feature set comparison
- calibration analysis
- seed stability
- rolling-year validation plan
- error slice analysis
- leakage/drift audit
- Qlib readiness report
- research roadmap

## Task 17: Validation Commands

Run:

```bash
git status --short
git branch --show-current
find cajas -path "*/init.py" -print
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Compile all new modules/scripts.

Run focused tests for new modules.

Run full tests if reasonable:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests
```

Run real artifact smoke commands where feasible:

1. build kline features for train and holdout
2. run feature set comparison with at least minimal and structure set
3. run calibration analysis on an existing holdout prediction file
4. run seed stability with a reduced seed list if full list is too slow
5. build rolling year validation plan
6. run error slice analysis
7. run leakage/drift audit
8. build Qlib readiness report
9. build research roadmap report

Confirm:

- no Qlib workflow executed
- no trading/backtest/profit outputs exist
- `tmp/` artifacts are not staged

Run:

```bash
git diff --check
git diff --stat
git status --short
```

## Suggested Commits

Prefer focused commits:

1. `docs: add phase 46-55 research quality prompt`
2. `feat: add kline structure feature sets`
3. `feat: add feature set comparison`
4. `feat: add calibration and seed stability analysis`
5. `feat: add rolling validation and error slice analysis`
6. `feat: add leakage drift and qlib readiness reports`
7. `feat: add research roadmap report`
8. `docs: document research quality workflow`

Do not run `git push`.

Report manual push command:

```bash
git push origin cajas/market-recognition-phase-0
```

## Completion Report Format

Report exactly in English:

```text
Phase 46-55 completed.

Branch:
- cajas/market-recognition-phase-0

Changed files:
- ...

Feature engineering:
- added features:
- train output:
- holdout output:

Feature set comparison:
- feature sets:
- best set:
- metrics:

Calibration:
- ECE-like metric:
- bucket count:
- trading thresholds created:

Seed stability:
- seeds:
- metric mean/std:

Rolling validation:
- planned splits:

Error slice analysis:
- slices:
- main error slices:

Leakage/drift audit:
- leakage found:
- drift summary:

Qlib readiness:
- ready:
- blockers:

Roadmap:
- recommendation:
- trading/backtest discussion status:

Validation commands run:
- ...

Tests:
- focused:
- full:

Git:
- local commit(s):
- push: not run by Codex
- manual push command: git push origin cajas/market-recognition-phase-0

Notes:
- ...
```

## Forbidden Work

Do not:

- Modify `qlib/` core.
- Modify official examples.
- Execute Qlib workflow.
- Run backtest/profit analysis.
- Calculate trading metrics.
- Add trading strategy.
- Add live trading/order execution.
- Treat `future_direction_*` as buy/sell signals.
- Treat thresholds/probabilities as trading thresholds.
- Commit raw CSV files.
- Commit `tmp/` outputs.
- Commit `.codex/`.
- Add `tasks/` to `.gitignore`.
- Run `git push`.
