# Phase 23-26 Prompt: Add Baseline Report Pack, Model Comparison, Feature Importance Summary, and Registry Reports

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

The project is now allowed to train controlled local market-recognition classification baselines.

Important:

- This is market-recognition research only.
- This is not a trading strategy.
- `future_direction_8` is a classification label, not a buy/sell signal.
- Qlib workflow execution remains disabled.
- Trading/backtest/profit analysis remains forbidden.

## Prerequisite Context

Expected previous phases:

- Phase 19-20 added controlled local baseline training.
- Phase 21 added baseline artifact inspection and prediction review.
- Phase 22 may have added baseline run comparison and feature importance inspection.

If Phase 22 is already implemented, build on it.

If Phase 22 is not implemented yet, include its scope in this combined implementation instead of skipping it:

- baseline run comparison
- feature importance inspection
- comparison CLI
- feature importance CLI
- tests/docs/config

Do not duplicate files or behavior if Phase 22 is already present.

## Phase 23-26 Goal

This combined phase should rapidly advance the local baseline research workflow by adding:

### Phase 23: Baseline Report Pack

- Generate a single report pack from a baseline run:
  - artifact inspection
  - metrics summary
  - prediction review summary
  - feature importance summary
  - config snapshot
  - run registry metadata if available

### Phase 24: Controlled Multi-Model Baseline Comparison

- Train multiple local classification baselines under strict research-only boundaries.
- Compare their classification metrics.
- Supported model families:
  - LightGBM if available
  - sklearn RandomForest
  - sklearn HistGradientBoosting or GradientBoosting if practical
- No trading, no backtest, no profit analysis.

### Phase 25: Feature Importance Summary Across Runs

- Aggregate feature importance across multiple baseline runs.
- Produce ranked feature summary.
- Do not interpret as trading rules.

### Phase 26: Registry and Experiment Summary Reports

- Read local run registry JSONL.
- Summarize runs by type, model family, metrics, artifact status.
- Produce local registry summary artifacts.

The combined result should make it easy to answer:

- What runs exist?
- Which model performed best by classification metrics?
- Which features were important across runs?
- Which samples need human review?
- What artifacts were produced?

## Absolute Boundaries

Allowed in this phase:

- Local supervised classification model training.
- Local model comparison.
- Local classification metrics.
- Local prediction review.
- Local feature importance inspection.
- Local report/artifact generation under `tmp/`.

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
10. Do not describe `future_direction_8` as a buy/sell signal.
11. Do not run backtest/profit/return analysis.
12. Do not calculate trading metrics such as profit, return, Sharpe, drawdown, PnL, win rate, or trade expectancy.
13. Do not add trading strategy, live execution, broker execution, auto order, or position sizing logic.
14. Do not install new runtime dependencies automatically.
15. Do not run `git push`.

## Task 1: Check State

Run:

```bash
git status --short
git branch --show-current
grep -n "tasks" .gitignore || true
find cajas -path "*/init.py" -print
```

Expected:

- Current branch is `cajas/market-recognition-phase-0`.
- `.gitignore` should not ignore `tasks/`.
- `find cajas -path "*/init.py" -print` must produce no output.
- Working tree should be clean or only contain this Phase 23-26 prompt if already added.

## Task 2: Path Hygiene

Run:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py --json
```

Expected:

- 0 issues.

If any `caixas/` or `cajas/**/init.py` issue appears, fix it before continuing.

## Task 3: Ensure Phase 22 Capabilities Exist

Check whether these files exist:

```text
cajas/baseline/baseline_run_comparison.py
cajas/baseline/feature_importance_inspector.py
cajas/scripts/compare_baseline_runs.py
cajas/scripts/inspect_feature_importance.py
cajas/tests/test_baseline_run_comparison.py
cajas/tests/test_feature_importance_inspector.py
```

If they exist:

- Reuse them.
- Do not reimplement duplicate modules.

If they do not exist:

- Implement Phase 22 scope first as part of this combined phase:
  - baseline run comparison
  - feature importance inspection
  - CLIs
  - tests
  - docs/config

Keep behavior classification-only.

## Task 4: Add Baseline Report Pack Module

Add:

```text
cajas/reports/__init__.py
cajas/reports/baseline_report_pack.py
```

Purpose:

- Build a single report pack from one baseline run directory.
- Combine existing artifact inspection, prediction review, feature importance, and metrics into one summary.
- Write local artifacts under `tmp/`.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class BaselineReportPack:
    run_dir: str
    run_name: str
    model_family: str | None
    target_label: str | None
    feature_count: int | None
    valid_metrics: dict
    test_metrics: dict
    prediction_review: dict
    feature_importance: dict
    artifact_inspection: dict
    trading_metrics_present: bool
    warnings: list[str]
    blockers: list[str]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def build_baseline_report_pack(
    *,
    run_dir: str | Path,
    output_dir: str | Path,
    run_name: str,
    write_artifacts: bool = True,
    top_k_features: int = 30,
) -> BaselineReportPack:
    ...
```

Expected report artifacts:

```text
baseline_report_pack.json
metrics_summary.json
feature_importance_summary.json
prediction_review_summary.json
artifact_inspection_summary.json
```

Optional CSV artifact:

```text
top_feature_importance.csv
```

Rules:

- Do not train.
- Do not predict.
- Do not calculate trading metrics.
- Do not load model except for feature importance if needed and already supported by existing inspector.

## Task 5: Add Baseline Report Pack CLI

Add:

```text
cajas/scripts/build_baseline_report_pack.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_baseline_report_pack.py \
  --run-dir tmp/cajas/baseline_runs/phase20_local_baseline \
  --output-dir tmp/cajas/baseline_report_packs \
  --run-name phase23_baseline_report_pack
```

Optional flags:

```text
--top-k-features 30
--json
```

Behavior:

- Text mode prints:
  - run name
  - model family
  - target label
  - valid/test metrics
  - top feature count
  - review summary
  - artifact output directory
  - explicit note: no trading/backtest/profit analysis performed
- JSON mode prints `BaselineReportPack.to_dict()`.
- Refuse overwrite of existing output directory.
- Do not train.

## Task 6: Add Multi-Model Baseline Runner

Add:

```text
cajas/baseline/multi_model_baseline.py
```

Purpose:

- Train several controlled local classification baselines.
- Reuse existing `train_local_baseline`.
- Write each model run under its own subdirectory.
- Compare runs using classification metrics.
- Append registry records through existing local run registry.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class MultiModelBaselineReport:
    config_path: str
    output_dir: str
    run_name: str
    model_families_requested: list[str]
    model_runs: list[dict]
    comparison: dict
    best_model_by_primary_metric: str | None
    primary_metric: str
    training_executed: bool
    qlib_workflow_executed: bool
    trading_metrics_present: bool
    warnings: list[str]
    blockers: list[str]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def run_multi_model_baseline(
    *,
    config_path: str,
    output_dir: str | Path,
    run_name: str,
    model_families: list[str],
    primary_metric: str = "test_macro_f1",
    input_override: str | None = None,
    random_state: int = 42,
) -> MultiModelBaselineReport:
    ...
```

Supported model families:

```text
LightGBM
RandomForest
HistGradientBoosting
```

Implementation notes:

- If `LightGBM` is not available or fails, report warning and continue with available sklearn models.
- If a model family is unsupported, skip with warning.
- Each model sub-run should use stable run names, for example:
  - `<run_name>_lightgbm`
  - `<run_name>_random_forest`
  - `<run_name>_hist_gradient_boosting`
- Do not overwrite existing output directory.
- Do not compute trading metrics.

If `train_local_baseline` currently only supports LightGBM/fallback, extend it cleanly to support explicit sklearn model families.

## Task 7: Add Multi-Model Baseline CLI

Add:

```text
cajas/scripts/train_multi_model_baselines.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/train_multi_model_baselines.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --output-dir tmp/cajas/multi_model_baselines \
  --run-name phase24_multi_model_baseline \
  --model-family LightGBM \
  --model-family RandomForest \
  --model-family HistGradientBoosting
```

Optional flags:

```text
--primary-metric test_macro_f1
--input-override tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv
--random-state 42
--json
```

Behavior:

- Text mode prints:
  - model families requested
  - runs completed/skipped
  - best model by primary metric
  - metrics table summary
  - output directory
  - explicit no trading/backtest/profit note
- JSON mode prints report dict.
- Refuse overwrite of existing output directory.
- Do not run Qlib workflow.

## Task 8: Add Feature Importance Aggregation

Add:

```text
cajas/baseline/feature_importance_summary.py
```

Purpose:

- Aggregate feature importance reports across multiple baseline run directories.
- Produce average rank/importance where available.
- Produce a stable top feature list.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class AggregatedFeatureImportanceItem:
    feature: str
    run_count: int
    mean_importance: float
    mean_rank: float
    max_importance: float

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class FeatureImportanceSummaryReport:
    run_count: int
    features: list[AggregatedFeatureImportanceItem]
    warnings: list[str]
    blockers: list[str]
    trading_logic_present: bool

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def summarize_feature_importance_across_runs(
    *,
    run_dirs: list[str | Path],
    top_k: int = 50,
) -> FeatureImportanceSummaryReport:
    ...
```

Rules:

- Use existing `inspect_feature_importance`.
- Skip runs without importance and report warnings.
- Do not infer trading rules.
- Do not produce buy/sell recommendations.

## Task 9: Add Feature Importance Summary CLI

Add:

```text
cajas/scripts/summarize_feature_importance.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/summarize_feature_importance.py \
  --run-dir tmp/cajas/baseline_runs/phase20_local_baseline \
  --output-dir tmp/cajas/feature_importance_summaries \
  --run-name phase25_feature_importance_summary
```

Support multiple `--run-dir`.

Optional flags:

```text
--top-k 50
--json
--write-artifacts
```

Artifacts:

```text
feature_importance_summary_report.json
feature_importance_summary.csv
```

## Task 10: Add Registry Summary Reports

Add:

```text
cajas/registry/registry_reports.py
```

Purpose:

- Read local registry JSONL.
- Summarize run counts by type/status/model family.
- Link run names to artifact directories.
- Optionally include metric snapshots if run artifacts exist.

Suggested dataclass:

```python
@dataclass(frozen=True)
class RunRegistrySummaryReport:
    registry_path: str
    total_records: int
    run_types: dict[str, int]
    statuses: dict[str, int]
    training_runs: list[dict]
    artifact_dirs: list[str]
    warnings: list[str]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def build_run_registry_summary(
    *,
    registry_path: str | Path,
) -> RunRegistrySummaryReport:
    ...
```

Rules:

- Do not fail if registry missing; return warning.
- Do not commit registry.
- Do not compute trading metrics.

## Task 11: Add Registry Summary CLI

Add:

```text
cajas/scripts/summarize_run_registry.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/summarize_run_registry.py \
  --registry tmp/cajas/run_registry/runs.jsonl \
  --output-dir tmp/cajas/registry_reports \
  --run-name phase26_registry_summary \
  --write-artifacts
```

Optional flags:

```text
--json
```

Artifacts:

```text
run_registry_summary_report.json
run_registry_summary.csv
```

## Task 12: Extend YAML Config

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Add or update sections:

```yaml
baseline_report_pack:
  enabled: true
  phase: phase23
  default_run_dir: tmp/cajas/baseline_runs/phase20_local_baseline
  output:
    default_output_dir: tmp/cajas/baseline_report_packs
    default_run_name: phase23_baseline_report_pack

multi_model_baseline:
  enabled: true
  phase: phase24
  model_families:
    - LightGBM
    - RandomForest
    - HistGradientBoosting
  primary_metric: test_macro_f1
  output:
    default_output_dir: tmp/cajas/multi_model_baselines
    default_run_name: phase24_multi_model_baseline

feature_importance_summary:
  enabled: true
  phase: phase25
  top_k: 50
  output:
    default_output_dir: tmp/cajas/feature_importance_summaries
    default_run_name: phase25_feature_importance_summary

run_registry_summary:
  enabled: true
  phase: phase26
  registry_path: tmp/cajas/run_registry/runs.jsonl
  output:
    default_output_dir: tmp/cajas/registry_reports
    default_run_name: phase26_registry_summary
```

Clarify:

- All outputs are local artifacts under `tmp/`.
- No trading/backtest/profit metrics are generated.
- Multi-model training is controlled local classification training only.

## Task 13: Add Tests

Add tests as appropriate:

```text
cajas/tests/test_baseline_report_pack.py
cajas/tests/test_multi_model_baseline.py
cajas/tests/test_feature_importance_summary.py
cajas/tests/test_registry_reports.py
```

Tests should use temporary directories and small fixtures.

Test coverage:

- report pack builds from fixture baseline run
- multi-model baseline can run at least sklearn models on tiny data
- feature importance summary aggregates fixture runs
- registry summary handles present and missing registry
- no trading metric keys present
- serialization works
- overwrite refusal works where applicable

Avoid long-running tests.

## Task 14: Update Documentation

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should add Phase 23-26:

- Baseline report pack
- Multi-model baseline training
- Feature importance summary
- Registry summary reports
- CLI commands:
  - `build_baseline_report_pack.py`
  - `train_multi_model_baselines.py`
  - `summarize_feature_importance.py`
  - `summarize_run_registry.py`
- No trading/backtest/profit analysis.

Integration notes should add Phase 23-26:

- These phases expand local baseline research workflow.
- Qlib compatibility remains separate.
- Training is still local classification baseline training, not Qlib workflow training.
- Phase 27 recommendation:
  - add model comparison dashboard data export; or
  - add baseline report pack markdown summary.

Data examples should add:

- Generated report packs and summaries are derived local artifacts under `tmp/`.
- They should not be committed.
- Metrics remain classification-only.

## Task 15: Validation Commands

Run:

```bash
git status --short
git branch --show-current
find cajas -path "*/init.py" -print
```

Compile all new modules/scripts:

```bash
./.venv-qlib313/bin/python -m py_compile \
  cajas/reports/baseline_report_pack.py \
  cajas/scripts/build_baseline_report_pack.py \
  cajas/baseline/multi_model_baseline.py \
  cajas/scripts/train_multi_model_baselines.py \
  cajas/baseline/feature_importance_summary.py \
  cajas/scripts/summarize_feature_importance.py \
  cajas/registry/registry_reports.py \
  cajas/scripts/summarize_run_registry.py
```

Run path hygiene:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_baseline_report_pack.py \
  cajas/tests/test_multi_model_baseline.py \
  cajas/tests/test_feature_importance_summary.py \
  cajas/tests/test_registry_reports.py
```

Run full tests if reasonable:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests
```

Ensure a baseline run exists:

```bash
if [ ! -d tmp/cajas/baseline_runs/phase20_local_baseline ]; then
  ./.venv-qlib313/bin/python cajas/scripts/train_local_baseline.py \
    --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
    --output-dir tmp/cajas/baseline_runs \
    --run-name phase20_local_baseline
fi
```

Run real baseline report pack:

```bash
rm -rf tmp/cajas/baseline_report_packs/phase23_baseline_report_pack

./.venv-qlib313/bin/python cajas/scripts/build_baseline_report_pack.py \
  --run-dir tmp/cajas/baseline_runs/phase20_local_baseline \
  --output-dir tmp/cajas/baseline_report_packs \
  --run-name phase23_baseline_report_pack

find tmp/cajas/baseline_report_packs/phase23_baseline_report_pack -maxdepth 1 -type f -print | sort
```

Run real multi-model baseline:

```bash
rm -rf tmp/cajas/multi_model_baselines/phase24_multi_model_baseline

./.venv-qlib313/bin/python cajas/scripts/train_multi_model_baselines.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --output-dir tmp/cajas/multi_model_baselines \
  --run-name phase24_multi_model_baseline \
  --model-family LightGBM \
  --model-family RandomForest \
  --model-family HistGradientBoosting \
  --primary-metric test_macro_f1

find tmp/cajas/multi_model_baselines/phase24_multi_model_baseline -maxdepth 2 -type f -print | sort | head -80
```

Run feature importance summary:

```bash
rm -rf tmp/cajas/feature_importance_summaries/phase25_feature_importance_summary

./.venv-qlib313/bin/python cajas/scripts/summarize_feature_importance.py \
  --run-dir tmp/cajas/baseline_runs/phase20_local_baseline \
  --output-dir tmp/cajas/feature_importance_summaries \
  --run-name phase25_feature_importance_summary \
  --write-artifacts

find tmp/cajas/feature_importance_summaries/phase25_feature_importance_summary -maxdepth 1 -type f -print | sort
```

Run registry summary:

```bash
rm -rf tmp/cajas/registry_reports/phase26_registry_summary

./.venv-qlib313/bin/python cajas/scripts/summarize_run_registry.py \
  --registry tmp/cajas/run_registry/runs.jsonl \
  --output-dir tmp/cajas/registry_reports \
  --run-name phase26_registry_summary \
  --write-artifacts

find tmp/cajas/registry_reports/phase26_registry_summary -maxdepth 1 -type f -print | sort
```

Run JSON modes for the main CLIs where practical.

Confirm:

- No Qlib workflow executed.
- No trading/backtest/profit outputs exist.
- `tmp/` artifacts are not staged.

Run:

```bash
git diff --check
git diff --stat
git status --short
```

## Suggested Commits

Prefer focused commits.

### Commit 1: Phase 23-26 prompt

```bash
git add tasks/phase_023_026_baseline_reporting_and_comparison_prompt.md
git commit -m "docs: add phase 23-26 baseline reporting prompt"
```

### Commit 2: baseline report pack

```bash
git add cajas/reports/__init__.py \
  cajas/reports/baseline_report_pack.py \
  cajas/scripts/build_baseline_report_pack.py \
  cajas/tests/test_baseline_report_pack.py
git commit -m "feat: add baseline report pack"
```

### Commit 3: multi-model baseline

```bash
git add cajas/baseline/multi_model_baseline.py \
  cajas/scripts/train_multi_model_baselines.py \
  cajas/tests/test_multi_model_baseline.py \
  cajas/baseline/local_baseline_trainer.py \
  cajas/baseline/__init__.py
git commit -m "feat: add multi-model baseline comparison"
```

### Commit 4: feature importance summary

```bash
git add cajas/baseline/feature_importance_summary.py \
  cajas/scripts/summarize_feature_importance.py \
  cajas/tests/test_feature_importance_summary.py \
  cajas/baseline/__init__.py
git commit -m "feat: add feature importance summary"
```

### Commit 5: registry reports

```bash
git add cajas/registry/registry_reports.py \
  cajas/scripts/summarize_run_registry.py \
  cajas/tests/test_registry_reports.py \
  cajas/registry/__init__.py
git commit -m "feat: add run registry summary reports"
```

### Commit 6: docs/config

```bash
git add cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  cajas/README.md \
  cajas/docs/qlib_integration_notes.md \
  cajas/data_examples/README.md
git commit -m "docs: document baseline reporting and comparison workflow"
```

Do not run `git push`.

Report manual push command:

```bash
git push origin cajas/market-recognition-phase-0
```

## Completion Report Format

Report exactly in English:

```text
Phase 23-26 completed.

Branch:
- cajas/market-recognition-phase-0

Changed files:
- ...

Baseline report pack:
- path:
- run dir:
- files written:

Multi-model baseline:
- path:
- model families requested:
- model runs completed:
- best model:
- primary metric:
- trading metrics present:

Feature importance summary:
- path:
- run count:
- top features:
- trading logic present:

Registry summary:
- path:
- registry path:
- total records:
- training runs:

Artifacts:
- report pack output:
- multi-model output:
- feature summary output:
- registry summary output:

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
- Treat `future_direction_8` as a buy/sell signal.
- Commit raw CSV files.
- Commit `tmp/` outputs.
- Commit `.codex/`.
- Add `tasks/` to `.gitignore`.
- Run `git push`.
