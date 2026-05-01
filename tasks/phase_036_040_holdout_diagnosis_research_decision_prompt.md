# Phase 36-40 Prompt: External Holdout Benchmarking, Flat-Class Diagnosis, Horizon Expansion, Feature Ablation, and Research Decision Report

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
- `future_direction_8` is a classification label, not a buy/sell signal.
- Qlib workflow execution remains disabled.
- Trading/backtest/profit analysis remains forbidden.

## Current Status

Phase 35 completed with local commits only. User will push manually.

Phase 35 commits:

```text
8ef24ae0 docs: add phase 35 external holdout validation prompt
c3053a53 feat: add external holdout dataset
3ec4e183 feat: add external holdout baseline training
6dfbc312 docs: document external holdout validation workflow
```

Phase 35 completed:

- Prepared `2020-2024` training dataset.
- Prepared `2025` external holdout dataset.
- Added `ExternalHoldoutDataset`.
- Added external holdout trainer + CLI.
- Added holdout-only classification artifacts.
- Updated inspection/reporting/docs/config to support external holdout runs.
- Real external holdout run completed successfully.

Known Phase 35 real-data result:

```text
run: tmp/cajas/external_holdout_runs/phase35_train_2020_2024_validate_2025
model_family_used: random_forest
holdout_accuracy: 0.5056635604113111
flat support: very low, 106
flat predictions: none in this run
```

Phase 35 validation:

```text
path hygiene: pass
py_compile: pass
focused tests: pass
full tests: pass
real data prepare 2020-2024: pass
real data prepare 2025: pass
external holdout train/evaluate: pass
git status --short: clean
```

## Phase 36-40 Goal

This combined phase should turn the external holdout result into a research decision point.

### Phase 36: External Holdout Benchmarking

- Compare the Phase 35 external holdout run against earlier internal-split baselines.
- Produce classification-only benchmark reports.
- Clearly mark internal split vs external holdout metrics.

### Phase 37: Flat-Class Diagnosis

- Diagnose why `flat` support is low and why the model predicts no `flat`.
- Add label distribution and confusion/error analysis focused on class imbalance.
- Do not make trading conclusions.

### Phase 38: Horizon Expansion Plan and Dataset Preview

- Add support to preview alternative future direction horizons:
  - `future_direction_4`
  - `future_direction_8`
  - `future_direction_16`
- Do not replace the main label yet.
- Generate label distribution comparison across horizons for 2020-2024 and 2025.

### Phase 39: Feature Group Ablation Plan and Optional Light Run

- Define feature groups:
  - price/return
  - range/body
  - volatility
  - rolling statistics
  - time/session if present
- Add feature group audit and optional ablation training on external holdout.
- Keep it classification-only.

### Phase 40: Research Decision Report

- Build a concise report answering:
  - Is the current `future_direction_8` label learnable?
  - Is `flat` class usable as currently defined?
  - Does external holdout performance justify more feature work?
  - Should next work focus on label redesign, feature engineering, or model tuning?
- No trading/backtest/profit conclusions.

## Absolute Boundaries

Allowed in this phase:

- Reading existing local artifacts under `tmp/`.
- Controlled local classification model training for ablation only if needed.
- Label distribution analysis.
- Horizon label preview.
- Classification metrics.
- Derived local reports under `tmp/`.

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
- Working tree should be clean or only contain this Phase 36-40 prompt if already added.

## Task 2: Path Hygiene

Run:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py --json
```

Expected:

- 0 issues.

If any `caixas/` or `cajas/**/init.py` issue appears, fix it before continuing.

## Task 3: Add External Holdout Benchmark Module

Add:

```text
cajas/reports/external_holdout_benchmark.py
```

Purpose:

- Compare external holdout runs with prior local baseline runs.
- Distinguish internal-split metrics from external-holdout metrics.
- Produce classification-only benchmark report.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class BenchmarkRunSummary:
    run_name: str
    run_dir: str
    run_kind: str  # internal_split or external_holdout
    model_family: str | None
    target_label: str | None
    accuracy: float | None
    macro_f1: float | None
    weighted_f1: float | None
    notes: list[str]

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class ExternalHoldoutBenchmarkReport:
    run_count: int
    external_holdout_count: int
    internal_split_count: int
    summaries: list[BenchmarkRunSummary]
    best_external_holdout_by_macro_f1: str | None
    warnings: list[str]
    trading_metrics_present: bool

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def build_external_holdout_benchmark(
    *,
    run_dirs: list[str | Path],
) -> ExternalHoldoutBenchmarkReport:
    ...
```

Rules:

- Detect external holdout runs by presence of `metrics_holdout.json`.
- Detect internal split runs by `metrics_valid.json` / `metrics_test.json`.
- Use holdout metrics for external holdout runs.
- Use test metrics for internal split runs.
- Do not mix the two without labeling them.
- Do not compute trading metrics.

## Task 4: Add External Holdout Benchmark CLI

Add:

```text
cajas/scripts/benchmark_external_holdout.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/benchmark_external_holdout.py \
  --run-dir tmp/cajas/baseline_runs/phase20_local_baseline \
  --run-dir tmp/cajas/external_holdout_runs/phase35_train_2020_2024_validate_2025 \
  --output-dir tmp/cajas/external_holdout_benchmarks \
  --run-name phase36_external_holdout_benchmark \
  --write-artifacts
```

Optional:

```text
--json
```

Artifacts:

```text
external_holdout_benchmark_report.json
external_holdout_benchmark.csv
```

## Task 5: Add Flat-Class Diagnosis Module

Add:

```text
cajas/baseline/flat_class_diagnosis.py
```

Purpose:

- Diagnose the `flat` class for a prediction artifact and label distribution artifacts.
- Identify:
  - support count
  - prediction count
  - recall/precision if available
  - confusion row/column if available
  - imbalance ratio
  - warnings when class is too rare or never predicted

Suggested dataclasses:

```python
@dataclass(frozen=True)
class FlatClassDiagnosisReport:
    run_dir: str
    split: str
    flat_support: int
    flat_predictions: int
    total_rows: int
    flat_support_ratio: float
    flat_prediction_ratio: float
    warnings: list[str]
    recommendations: list[str]
    trading_conclusions_present: bool

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def diagnose_flat_class(
    *,
    prediction_csv: str | Path,
    split: str,
    flat_label: str = "flat",
) -> FlatClassDiagnosisReport:
    ...
```

Recommendations should be research-only, e.g.:

- consider binary up/down label
- consider threshold-based flat definition
- compare horizons
- collect more examples
- inspect feature separability

Do not recommend trading actions.

## Task 6: Add Flat-Class Diagnosis CLI

Add:

```text
cajas/scripts/diagnose_flat_class.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/diagnose_flat_class.py \
  --prediction-csv tmp/cajas/external_holdout_runs/phase35_train_2020_2024_validate_2025/predictions_holdout.csv \
  --split holdout \
  --output-dir tmp/cajas/flat_class_diagnosis \
  --run-name phase37_flat_class_diagnosis \
  --write-artifacts
```

Optional:

```text
--json
```

Artifacts:

```text
flat_class_diagnosis_report.json
flat_class_examples.csv
```

The examples CSV may include rows where true label is flat or predicted label is flat, but do not include raw market data beyond prediction artifact columns.

## Task 7: Add Horizon Label Preview Module

Add:

```text
cajas/datasets/horizon_label_preview.py
```

Purpose:

- Preview alternative `future_direction_N` labels from prepared data or raw close series.
- Compare distributions for horizons 4, 8, 16.
- Do not replace existing `future_direction_8` yet.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class HorizonLabelDistribution:
    horizon: int
    label_col: str
    row_count: int
    distribution: dict[str, int]
    flat_ratio: float

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class HorizonLabelPreviewReport:
    input_path: str
    horizons: list[HorizonLabelDistribution]
    warnings: list[str]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def preview_horizon_labels(
    *,
    input_path: str | Path,
    horizons: list[int],
    close_col: str = "close",
) -> HorizonLabelPreviewReport:
    ...
```

Rules:

- Use prepared dataset close column if available.
- Compute future return by horizon.
- Use same current label semantics:
  - up if future_return > 0
  - down if future_return < 0
  - flat if exactly 0
- Do not commit generated data.
- This is only a distribution preview.

## Task 8: Add Horizon Label Preview CLI

Add:

```text
cajas/scripts/preview_horizon_labels.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/preview_horizon_labels.py \
  --input tmp/cajas/eurusd_15m_2020_2024_phase35_train/prepared_dataset.csv \
  --input-name train_2020_2024 \
  --horizon 4 \
  --horizon 8 \
  --horizon 16 \
  --output-dir tmp/cajas/horizon_label_previews \
  --run-name phase38_horizon_preview_train \
  --write-artifacts
```

Also run for 2025 holdout.

Artifacts:

```text
horizon_label_preview_report.json
horizon_label_distribution.csv
```

## Task 9: Add Feature Group Audit and Optional Ablation

Add:

```text
cajas/baseline/feature_group_audit.py
```

Purpose:

- Categorize feature columns into rough groups.
- Produce group counts.
- Optionally support feature subsets for later ablation.

Suggested groups:

```text
price_return
range_body
volatility
rolling_stats
time_session
other
```

Suggested function:

```python
def classify_feature_groups(feature_columns: list[str]) -> dict[str, list[str]]:
    ...

def build_feature_group_audit(feature_columns: list[str]) -> dict:
    ...
```

Add optional ablation module only if time remains:

```text
cajas/baseline/feature_group_ablation.py
```

Ablation should:

- train external holdout baselines with selected feature groups
- remain classification-only
- write local artifacts under `tmp/`
- be optional and skipped if too large for this phase

Minimum required for Phase 39:

- feature group audit + CLI.

Add CLI:

```text
cajas/scripts/audit_feature_groups.py
```

Example:

```bash
./.venv-qlib313/bin/python cajas/scripts/audit_feature_groups.py \
  --feature-columns-json tmp/cajas/external_holdout_runs/phase35_train_2020_2024_validate_2025/feature_columns.json \
  --output-dir tmp/cajas/feature_group_audits \
  --run-name phase39_feature_group_audit \
  --write-artifacts
```

Artifacts:

```text
feature_group_audit_report.json
feature_group_columns.csv
```

## Task 10: Add Research Decision Report Module

Add:

```text
cajas/reports/research_decision_report.py
```

Purpose:

- Summarize Phase 35-40 research findings into a decision report.
- Include:
  - external holdout metrics
  - internal vs holdout comparison
  - flat-class diagnosis
  - horizon label distributions
  - feature group audit
  - recommended next research direction

Suggested outputs:

```text
research_decision_report.md
research_decision_report.json
```

Suggested recommendations must be research-only:

- label redesign
- threshold-based flat class
- horizon comparison
- feature engineering
- model comparison
- Qlib workflow integration later

Forbidden recommendations:

- buy/sell rules
- trading strategy
- backtest
- profit optimization

Add CLI:

```text
cajas/scripts/build_research_decision_report.py
```

Example:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_research_decision_report.py \
  --external-run-dir tmp/cajas/external_holdout_runs/phase35_train_2020_2024_validate_2025 \
  --output-dir tmp/cajas/research_decision_reports \
  --run-name phase40_research_decision_report \
  --write-artifacts
```

## Task 11: Extend YAML Config

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Add sections:

```yaml
external_holdout_benchmark:
  enabled: true
  phase: phase36
  output:
    default_output_dir: tmp/cajas/external_holdout_benchmarks
    default_run_name: phase36_external_holdout_benchmark

flat_class_diagnosis:
  enabled: true
  phase: phase37
  flat_label: flat
  output:
    default_output_dir: tmp/cajas/flat_class_diagnosis
    default_run_name: phase37_flat_class_diagnosis

horizon_label_preview:
  enabled: true
  phase: phase38
  horizons:
    - 4
    - 8
    - 16
  output:
    default_output_dir: tmp/cajas/horizon_label_previews

feature_group_audit:
  enabled: true
  phase: phase39
  output:
    default_output_dir: tmp/cajas/feature_group_audits
    default_run_name: phase39_feature_group_audit

research_decision_report:
  enabled: true
  phase: phase40
  output:
    default_output_dir: tmp/cajas/research_decision_reports
    default_run_name: phase40_research_decision_report
```

Clarify:

- These are classification research artifacts.
- No trading/backtest/profit analysis.

## Task 12: Add Tests

Add tests:

```text
cajas/tests/test_external_holdout_benchmark.py
cajas/tests/test_flat_class_diagnosis.py
cajas/tests/test_horizon_label_preview.py
cajas/tests/test_feature_group_audit.py
cajas/tests/test_research_decision_report.py
```

Test coverage:

- benchmark distinguishes internal vs external runs
- flat diagnosis detects low support and no predictions
- horizon preview produces distributions for 4/8/16
- feature group audit classifies known columns
- research decision report includes required sections and excludes trading/profit/backtest recommendations

## Task 13: Update Documentation

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should add Phase 36-40:

- external holdout benchmarking
- flat-class diagnosis
- horizon label preview
- feature group audit
- research decision report

Integration notes should add:

- Phase 35 external holdout is a real out-of-sample classification validation.
- Flat-class issue is now explicitly diagnosed.
- Phase 41 recommendation:
  - add threshold-based flat label experiment; or
  - add horizon-specific external holdout training for 4/8/16.

Data examples should add:

- Horizon previews are derived labels under `tmp/`.
- Decision reports are research artifacts, not trading guidance.

## Task 14: Validation Commands

Run:

```bash
git status --short
git branch --show-current
find cajas -path "*/init.py" -print
```

Compile:

```bash
./.venv-qlib313/bin/python -m py_compile \
  cajas/reports/external_holdout_benchmark.py \
  cajas/scripts/benchmark_external_holdout.py \
  cajas/baseline/flat_class_diagnosis.py \
  cajas/scripts/diagnose_flat_class.py \
  cajas/datasets/horizon_label_preview.py \
  cajas/scripts/preview_horizon_labels.py \
  cajas/baseline/feature_group_audit.py \
  cajas/scripts/audit_feature_groups.py \
  cajas/reports/research_decision_report.py \
  cajas/scripts/build_research_decision_report.py
```

Run path hygiene:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_external_holdout_benchmark.py \
  cajas/tests/test_flat_class_diagnosis.py \
  cajas/tests/test_horizon_label_preview.py \
  cajas/tests/test_feature_group_audit.py \
  cajas/tests/test_research_decision_report.py
```

Run full tests if reasonable:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests
```

Ensure Phase 35 run exists. If not, run Phase 35 commands from previous prompt.

Run real benchmark:

```bash
rm -rf tmp/cajas/external_holdout_benchmarks/phase36_external_holdout_benchmark

./.venv-qlib313/bin/python cajas/scripts/benchmark_external_holdout.py \
  --run-dir tmp/cajas/baseline_runs/phase20_local_baseline \
  --run-dir tmp/cajas/external_holdout_runs/phase35_train_2020_2024_validate_2025 \
  --output-dir tmp/cajas/external_holdout_benchmarks \
  --run-name phase36_external_holdout_benchmark \
  --write-artifacts
```

Run flat diagnosis:

```bash
rm -rf tmp/cajas/flat_class_diagnosis/phase37_flat_class_diagnosis

./.venv-qlib313/bin/python cajas/scripts/diagnose_flat_class.py \
  --prediction-csv tmp/cajas/external_holdout_runs/phase35_train_2020_2024_validate_2025/predictions_holdout.csv \
  --split holdout \
  --output-dir tmp/cajas/flat_class_diagnosis \
  --run-name phase37_flat_class_diagnosis \
  --write-artifacts
```

Run horizon previews for train and holdout:

```bash
rm -rf tmp/cajas/horizon_label_previews/phase38_horizon_preview_train
rm -rf tmp/cajas/horizon_label_previews/phase38_horizon_preview_holdout

./.venv-qlib313/bin/python cajas/scripts/preview_horizon_labels.py \
  --input tmp/cajas/eurusd_15m_2020_2024_phase35_train/prepared_dataset.csv \
  --input-name train_2020_2024 \
  --horizon 4 \
  --horizon 8 \
  --horizon 16 \
  --output-dir tmp/cajas/horizon_label_previews \
  --run-name phase38_horizon_preview_train \
  --write-artifacts

./.venv-qlib313/bin/python cajas/scripts/preview_horizon_labels.py \
  --input tmp/cajas/eurusd_15m_2025_phase35_holdout/prepared_dataset.csv \
  --input-name holdout_2025 \
  --horizon 4 \
  --horizon 8 \
  --horizon 16 \
  --output-dir tmp/cajas/horizon_label_previews \
  --run-name phase38_horizon_preview_holdout \
  --write-artifacts
```

Run feature group audit:

```bash
rm -rf tmp/cajas/feature_group_audits/phase39_feature_group_audit

./.venv-qlib313/bin/python cajas/scripts/audit_feature_groups.py \
  --feature-columns-json tmp/cajas/external_holdout_runs/phase35_train_2020_2024_validate_2025/feature_columns.json \
  --output-dir tmp/cajas/feature_group_audits \
  --run-name phase39_feature_group_audit \
  --write-artifacts
```

Run research decision report:

```bash
rm -rf tmp/cajas/research_decision_reports/phase40_research_decision_report

./.venv-qlib313/bin/python cajas/scripts/build_research_decision_report.py \
  --external-run-dir tmp/cajas/external_holdout_runs/phase35_train_2020_2024_validate_2025 \
  --output-dir tmp/cajas/research_decision_reports \
  --run-name phase40_research_decision_report \
  --write-artifacts
```

Run JSON modes for new CLIs where practical.

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

Prefer focused commits.

### Commit 1: Phase 36-40 prompt

```bash
git add tasks/phase_036_040_holdout_diagnosis_research_decision_prompt.md
git commit -m "docs: add phase 36-40 holdout diagnosis prompt"
```

### Commit 2: external holdout benchmark and flat diagnosis

```bash
git add cajas/reports/external_holdout_benchmark.py \
  cajas/scripts/benchmark_external_holdout.py \
  cajas/baseline/flat_class_diagnosis.py \
  cajas/scripts/diagnose_flat_class.py \
  cajas/tests/test_external_holdout_benchmark.py \
  cajas/tests/test_flat_class_diagnosis.py \
  cajas/reports/__init__.py \
  cajas/baseline/__init__.py
git commit -m "feat: add holdout benchmark and flat diagnosis"
```

### Commit 3: horizon and feature group analysis

```bash
git add cajas/datasets/horizon_label_preview.py \
  cajas/scripts/preview_horizon_labels.py \
  cajas/baseline/feature_group_audit.py \
  cajas/scripts/audit_feature_groups.py \
  cajas/tests/test_horizon_label_preview.py \
  cajas/tests/test_feature_group_audit.py \
  cajas/datasets/__init__.py \
  cajas/baseline/__init__.py
git commit -m "feat: add horizon and feature group analysis"
```

### Commit 4: research decision report

```bash
git add cajas/reports/research_decision_report.py \
  cajas/scripts/build_research_decision_report.py \
  cajas/tests/test_research_decision_report.py \
  cajas/reports/__init__.py
git commit -m "feat: add research decision report"
```

### Commit 5: docs/config

```bash
git add cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  cajas/README.md \
  cajas/docs/qlib_integration_notes.md \
  cajas/data_examples/README.md
git commit -m "docs: document holdout diagnosis research workflow"
```

Do not run `git push`.

Report manual push command:

```bash
git push origin cajas/market-recognition-phase-0
```

## Completion Report Format

Report exactly in English:

```text
Phase 36-40 completed.

Branch:
- cajas/market-recognition-phase-0

Changed files:
- ...

External holdout benchmark:
- path:
- internal runs:
- external runs:
- best external holdout:
- trading metrics present:

Flat-class diagnosis:
- path:
- flat support:
- flat predictions:
- warnings:
- research recommendations:

Horizon preview:
- path:
- train distributions:
- holdout distributions:

Feature group audit:
- path:
- groups:
- feature count:

Research decision report:
- path:
- decision summary:
- recommended next phase:
- trading/profit/backtest recommendations present:

Artifacts:
- benchmark output:
- flat diagnosis output:
- horizon preview output:
- feature group output:
- decision report output:

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
- Commit raw CSV files.
- Commit `tmp/` outputs.
- Commit `.codex/`.
- Add `tasks/` to `.gitignore`.
- Run `git push`.
