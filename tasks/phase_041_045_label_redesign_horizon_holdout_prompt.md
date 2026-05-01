# Phase 41-45 Prompt: Label Redesign, Threshold Flat Experiments, Horizon Holdout Training, Binary Baseline, and Label Decision Report

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
- Qlib workflow execution remains disabled.
- Trading/backtest/profit analysis remains forbidden.

## Current Status

Phase 40B completed and fixed the Phase 36-40 regression.

Phase 40B commits:

```text
58104ee4 docs: add phase 40B regression fix prompt
de6c38d9 fix: resolve holdout diagnosis regression failures
```

Phase 40B fixed:

- Full suite failure in:
  - `cajas/tests/test_multi_model_baseline.py::MultiModelBaselineTests::test_runs_sklearn_models`
- Root cause:
  - invalid YAML in `cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml`
- Full suite result:
  - `159 passed`
- Path hygiene:
  - pass
- `cajas/**/init.py`:
  - none

Previous research findings from Phase 35-40:

- External holdout validation was added:
  - train: 2020-2024
  - holdout: 2025
- Real external holdout accuracy:
  - about `0.5056635604113111`
- `flat` class issue:
  - flat support on 2025 h8: `106`
  - model predicted `0` flat rows
  - flat support ratio below 1%
- Horizon preview distributions:
  - train h4: down=61263 flat=1300 up=62245
  - train h8: down=61231 flat=1010 up=62563
  - train h16: down=61590 flat=754 up=62452
  - holdout h4: down=12155 flat=160 up=12577
  - holdout h8: down=12100 flat=106 up=12682
  - holdout h16: down=12081 flat=63 up=12736

Research conclusion so far:

- `future_direction_8` is learnable only at a modest level.
- The exact-zero `flat` class is too rare and weak under current definition.
- Next work should focus on label redesign and horizon-specific external holdout validation, not trading.

## Phase 41-45 Goal

This combined phase should test whether the label definition is the main bottleneck.

### Phase 41: Threshold-Based Flat Label Preview

Add support for threshold-based future direction labels:

```text
up    if future_return > +threshold
down  if future_return < -threshold
flat  otherwise
```

Thresholds should be configurable in price-return units, for example:

```text
0.0
0.00005
0.00010
0.00020
0.00030
```

These are research label thresholds only, not trading thresholds.

### Phase 42: Horizon-Specific External Holdout Training

Train/evaluate external holdout baselines for horizons:

```text
future_direction_4
future_direction_8
future_direction_16
```

Use:

```text
train: 2020-2024
holdout: 2025
```

### Phase 43: Binary Up/Down Baseline

Add binary baseline option that excludes or maps flat rows:

Options:

```text
binary_drop_flat:
  keep only up/down rows

binary_map_flat:
  map flat to nearest side is not allowed in this phase unless clearly documented and justified
```

Default should be:

```text
binary_drop_flat
```

### Phase 44: Label Quality Comparison

Compare:

- exact-zero 3-class labels
- threshold-based 3-class labels
- binary up/down labels
- horizons 4/8/16

Use classification-only metrics and label distributions.

### Phase 45: Label Decision Report

Produce a research decision report recommending the next label direction:

- keep exact h8 3-class
- switch to threshold flat
- switch to binary up/down
- compare horizons further
- add richer K-line structure labels

Do not recommend trading actions.

## Absolute Boundaries

Allowed in this phase:

- Label generation and preview.
- Controlled local classification training.
- External holdout evaluation.
- Classification metrics.
- Label distribution reports.
- Derived local artifacts under `tmp/`.

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
11. Do not describe thresholds as trading thresholds.
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
```

Expected:

- Current branch is `cajas/market-recognition-phase-0`.
- `.gitignore` should not ignore `tasks/`.
- `find cajas -path "*/init.py" -print` must produce no output.
- Working tree should be clean or only contain this Phase 41-45 prompt if already added.

## Task 2: Path Hygiene

Run:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py --json
```

Expected:

- 0 issues.

If any `caixas/` or `cajas/**/init.py` issue appears, fix it before continuing.

## Task 3: Add Threshold Label Generator

Add:

```text
cajas/datasets/threshold_label_generator.py
```

Purpose:

- Generate `future_direction_{horizon}_thr_{threshold}` style labels.
- Support exact-zero threshold and positive thresholds.
- Preserve source prepared CSV unchanged.
- Write derived datasets only under `tmp/`.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class ThresholdLabelSpec:
    horizon: int
    threshold: float
    label_col: str

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class ThresholdLabelGenerationReport:
    input_path: str
    output_path: str | None
    specs: list[dict]
    row_count: int
    label_distributions: dict[str, dict[str, int]]
    warnings: list[str]

    def to_dict(self) -> dict: ...
```

Suggested functions:

```python
def build_threshold_label_col(horizon: int, threshold: float) -> str:
    ...

def generate_threshold_labels(
    *,
    input_path: str | Path,
    horizons: list[int],
    thresholds: list[float],
    output_path: str | Path | None = None,
    close_col: str = "close",
) -> ThresholdLabelGenerationReport:
    ...
```

Label semantics:

```text
future_return = future_close / close - 1

up    if future_return > +threshold
down  if future_return < -threshold
flat  otherwise
```

Rules:

- These thresholds are classification label thresholds only.
- They are not trading thresholds.
- Do not mutate source DataFrame.
- If output_path is provided, write a derived CSV under `tmp/`.

## Task 4: Add Threshold Label Preview CLI

Add:

```text
cajas/scripts/generate_threshold_labels.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/generate_threshold_labels.py \
  --input tmp/cajas/eurusd_15m_2020_2024_phase35_train/prepared_dataset.csv \
  --output tmp/cajas/label_variants/phase41_train_threshold_labels.csv \
  --horizon 4 \
  --horizon 8 \
  --horizon 16 \
  --threshold 0.0 \
  --threshold 0.00005 \
  --threshold 0.00010 \
  --threshold 0.00020 \
  --threshold 0.00030 \
  --json
```

Add artifact mode:

```text
--report-output tmp/cajas/label_variants/phase41_train_threshold_labels_report.json
```

Do the same for 2025 holdout.

## Task 5: Add Label Variant Dataset

Add:

```text
cajas/datasets/label_variant_dataset.py
```

Purpose:

- Load train and holdout derived datasets with a selected label column.
- Reuse external holdout dataset logic.
- Train/evaluate any label variant without duplicating feature logic.

Suggested class:

```python
class LabelVariantExternalHoldoutDataset:
    def __init__(
        self,
        *,
        train_path: str | Path,
        holdout_path: str | Path,
        label_col: str,
        leakage_columns: tuple[str, ...] = ("future_close_8", "future_return_8"),
    ) -> None:
        ...

    def prepare_train(self): ...
    def prepare_holdout(self): ...
    def summary(self) -> dict: ...
```

Important:

- Leakage columns should include all `future_close_*` and `future_return_*` columns, not only h8.
- No label variant column should appear as a feature.
- No future-derived label/return columns should appear as features.

## Task 6: Add Label Variant External Holdout Trainer

Add:

```text
cajas/baseline/label_variant_trainer.py
```

Purpose:

- Train external holdout baselines for selected label variants.
- Use 2020-2024 train / 2025 holdout.
- Use existing sanitizer, metrics, label encoding logic.
- Support 3-class up/down/flat labels and binary up/down labels.

Suggested dataclass:

```python
@dataclass(frozen=True)
class LabelVariantTrainingReport:
    label_col: str
    label_mode: str
    model_family: str
    train_rows: int
    holdout_rows: int
    feature_count: int
    holdout_metrics: dict
    label_distribution_train: dict
    label_distribution_holdout: dict
    output_dir: str
    artifact_files: list[str]
    warnings: list[str]
    blockers: list[str]
    trading_metrics_present: bool

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def train_label_variant_external_holdout(
    *,
    train_path: str | Path,
    holdout_path: str | Path,
    label_col: str,
    output_dir: str | Path,
    run_name: str,
    model_family: str = "LightGBM",
    label_mode: str = "multiclass",
    random_state: int = 42,
) -> LabelVariantTrainingReport:
    ...
```

Label modes:

```text
multiclass
binary_drop_flat
```

For `binary_drop_flat`:

- Remove rows where selected label is `flat`.
- Encode:
  - down: 0
  - up: 1
- Do not map flat to either side.

Artifacts:

```text
run_manifest.json
label_variant_training_report.json
metrics_holdout.json
confusion_matrix_holdout.csv
predictions_holdout.csv
label_distribution_train.json
label_distribution_holdout.json
feature_columns.json
model_metadata.json
model.joblib
```

## Task 7: Add Label Variant Training CLI

Add:

```text
cajas/scripts/train_label_variant_holdout.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/train_label_variant_holdout.py \
  --train tmp/cajas/label_variants/phase41_train_threshold_labels.csv \
  --holdout tmp/cajas/label_variants/phase41_holdout_threshold_labels.csv \
  --label-col future_direction_8_thr_0_00010 \
  --label-mode multiclass \
  --output-dir tmp/cajas/label_variant_runs \
  --run-name phase42_h8_thr_00010_multiclass \
  --model-family LightGBM
```

Binary example:

```bash
./.venv-qlib313/bin/python cajas/scripts/train_label_variant_holdout.py \
  --train tmp/cajas/label_variants/phase41_train_threshold_labels.csv \
  --holdout tmp/cajas/label_variants/phase41_holdout_threshold_labels.csv \
  --label-col future_direction_8_thr_0_00000 \
  --label-mode binary_drop_flat \
  --output-dir tmp/cajas/label_variant_runs \
  --run-name phase43_h8_binary_drop_flat \
  --model-family LightGBM
```

## Task 8: Add Label Variant Comparison

Add:

```text
cajas/reports/label_variant_comparison.py
```

Purpose:

- Compare multiple label variant runs.
- Include:
  - label column
  - label mode
  - horizon
  - threshold
  - train/holdout label distributions
  - holdout metrics
  - flat ratio if present
- Classification-only.

Suggested function:

```python
def compare_label_variant_runs(
    *,
    run_dirs: list[str | Path],
    primary_metric: str = "macro_f1",
) -> dict:
    ...
```

Add CLI:

```text
cajas/scripts/compare_label_variants.py
```

Artifacts:

```text
label_variant_comparison_report.json
label_variant_comparison.csv
```

## Task 9: Add Label Decision Report

Add:

```text
cajas/reports/label_decision_report.py
```

Purpose:

- Build a report recommending next label strategy based on variant results.
- Include:
  - exact h8 baseline
  - threshold-flat variants
  - binary baseline
  - horizon comparison
  - flat-class diagnosis
- No trading recommendations.

Suggested report sections:

- Scope
- Label candidates
- External holdout comparison
- Flat-class findings
- Binary baseline findings
- Recommended next research label
- Risks and caveats
- Explicit forbidden interpretations

Add CLI:

```text
cajas/scripts/build_label_decision_report.py
```

Artifacts:

```text
label_decision_report.md
label_decision_report.json
```

## Task 10: Extend YAML Config

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Add sections:

```yaml
label_redesign:
  enabled: true
  phase: phase41
  horizons:
    - 4
    - 8
    - 16
  thresholds:
    - 0.0
    - 0.00005
    - 0.00010
    - 0.00020
    - 0.00030
  threshold_semantics: classification_label_threshold_only_not_trading

label_variant_external_holdout:
  enabled: true
  phase: phase42
  train_period: 2020_2024
  holdout_period: 2025
  model_family: LightGBM
  label_modes:
    - multiclass
    - binary_drop_flat
  output:
    default_output_dir: tmp/cajas/label_variant_runs

label_variant_comparison:
  enabled: true
  phase: phase44
  primary_metric: macro_f1
  output:
    default_output_dir: tmp/cajas/label_variant_comparisons
    default_run_name: phase44_label_variant_comparison

label_decision_report:
  enabled: true
  phase: phase45
  output:
    default_output_dir: tmp/cajas/label_decision_reports
    default_run_name: phase45_label_decision_report
```

Clarify:

- Label thresholds are not trading thresholds.
- Binary baseline is classification-only.
- No backtest/profit/trading analysis.

## Task 11: Add Tests

Add tests:

```text
cajas/tests/test_threshold_label_generator.py
cajas/tests/test_label_variant_dataset.py
cajas/tests/test_label_variant_trainer.py
cajas/tests/test_label_variant_comparison.py
cajas/tests/test_label_decision_report.py
```

Test coverage:

- threshold label generation distribution
- label column naming stable
- future-derived columns excluded from features
- binary_drop_flat removes flat rows
- variant trainer writes expected artifacts on tiny data
- variant comparison ranks runs
- decision report excludes trading/profit/backtest recommendations

## Task 12: Update Documentation

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should add Phase 41-45:

- threshold-based flat label experiments
- horizon-specific label variants
- binary up/down baseline
- label variant external holdout
- label decision report

Integration notes should add:

- This phase tests whether label design, especially flat definition, is the main bottleneck.
- Thresholds are classification label thresholds only.
- Binary up/down baseline is for comparison only, not a trading signal.

Data examples should add:

- Label variant CSVs are derived artifacts under `tmp/`.
- Raw data remains outside repo.
- Variant labels are not trading actions.

## Task 13: Validation Commands

Run:

```bash
git status --short
git branch --show-current
find cajas -path "*/init.py" -print
```

Compile:

```bash
./.venv-qlib313/bin/python -m py_compile \
  cajas/datasets/threshold_label_generator.py \
  cajas/scripts/generate_threshold_labels.py \
  cajas/datasets/label_variant_dataset.py \
  cajas/baseline/label_variant_trainer.py \
  cajas/scripts/train_label_variant_holdout.py \
  cajas/reports/label_variant_comparison.py \
  cajas/scripts/compare_label_variants.py \
  cajas/reports/label_decision_report.py \
  cajas/scripts/build_label_decision_report.py
```

Run path hygiene:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_threshold_label_generator.py \
  cajas/tests/test_label_variant_dataset.py \
  cajas/tests/test_label_variant_trainer.py \
  cajas/tests/test_label_variant_comparison.py \
  cajas/tests/test_label_decision_report.py
```

Run full suite if reasonable:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests
```

Ensure Phase 35 prepared datasets exist. If not, run Phase 35 preparation commands.

Generate threshold label variants:

```bash
mkdir -p tmp/cajas/label_variants

./.venv-qlib313/bin/python cajas/scripts/generate_threshold_labels.py \
  --input tmp/cajas/eurusd_15m_2020_2024_phase35_train/prepared_dataset.csv \
  --output tmp/cajas/label_variants/phase41_train_threshold_labels.csv \
  --report-output tmp/cajas/label_variants/phase41_train_threshold_labels_report.json \
  --horizon 4 \
  --horizon 8 \
  --horizon 16 \
  --threshold 0.0 \
  --threshold 0.00005 \
  --threshold 0.00010 \
  --threshold 0.00020 \
  --threshold 0.00030 \
  --json

./.venv-qlib313/bin/python cajas/scripts/generate_threshold_labels.py \
  --input tmp/cajas/eurusd_15m_2025_phase35_holdout/prepared_dataset.csv \
  --output tmp/cajas/label_variants/phase41_holdout_threshold_labels.csv \
  --report-output tmp/cajas/label_variants/phase41_holdout_threshold_labels_report.json \
  --horizon 4 \
  --horizon 8 \
  --horizon 16 \
  --threshold 0.0 \
  --threshold 0.00005 \
  --threshold 0.00010 \
  --threshold 0.00020 \
  --threshold 0.00030 \
  --json
```

Run selected variant trainings:

```bash
rm -rf tmp/cajas/label_variant_runs/phase42_h4_exact_multiclass
rm -rf tmp/cajas/label_variant_runs/phase42_h8_thr_00010_multiclass
rm -rf tmp/cajas/label_variant_runs/phase42_h16_thr_00010_multiclass
rm -rf tmp/cajas/label_variant_runs/phase43_h8_binary_drop_flat

./.venv-qlib313/bin/python cajas/scripts/train_label_variant_holdout.py \
  --train tmp/cajas/label_variants/phase41_train_threshold_labels.csv \
  --holdout tmp/cajas/label_variants/phase41_holdout_threshold_labels.csv \
  --label-col future_direction_4_thr_0_00000 \
  --label-mode multiclass \
  --output-dir tmp/cajas/label_variant_runs \
  --run-name phase42_h4_exact_multiclass \
  --model-family LightGBM

./.venv-qlib313/bin/python cajas/scripts/train_label_variant_holdout.py \
  --train tmp/cajas/label_variants/phase41_train_threshold_labels.csv \
  --holdout tmp/cajas/label_variants/phase41_holdout_threshold_labels.csv \
  --label-col future_direction_8_thr_0_00010 \
  --label-mode multiclass \
  --output-dir tmp/cajas/label_variant_runs \
  --run-name phase42_h8_thr_00010_multiclass \
  --model-family LightGBM

./.venv-qlib313/bin/python cajas/scripts/train_label_variant_holdout.py \
  --train tmp/cajas/label_variants/phase41_train_threshold_labels.csv \
  --holdout tmp/cajas/label_variants/phase41_holdout_threshold_labels.csv \
  --label-col future_direction_16_thr_0_00010 \
  --label-mode multiclass \
  --output-dir tmp/cajas/label_variant_runs \
  --run-name phase42_h16_thr_00010_multiclass \
  --model-family LightGBM

./.venv-qlib313/bin/python cajas/scripts/train_label_variant_holdout.py \
  --train tmp/cajas/label_variants/phase41_train_threshold_labels.csv \
  --holdout tmp/cajas/label_variants/phase41_holdout_threshold_labels.csv \
  --label-col future_direction_8_thr_0_00000 \
  --label-mode binary_drop_flat \
  --output-dir tmp/cajas/label_variant_runs \
  --run-name phase43_h8_binary_drop_flat \
  --model-family LightGBM
```

Compare label variants:

```bash
rm -rf tmp/cajas/label_variant_comparisons/phase44_label_variant_comparison

./.venv-qlib313/bin/python cajas/scripts/compare_label_variants.py \
  --run-dir tmp/cajas/label_variant_runs/phase42_h4_exact_multiclass \
  --run-dir tmp/cajas/label_variant_runs/phase42_h8_thr_00010_multiclass \
  --run-dir tmp/cajas/label_variant_runs/phase42_h16_thr_00010_multiclass \
  --run-dir tmp/cajas/label_variant_runs/phase43_h8_binary_drop_flat \
  --output-dir tmp/cajas/label_variant_comparisons \
  --run-name phase44_label_variant_comparison \
  --write-artifacts
```

Build label decision report:

```bash
rm -rf tmp/cajas/label_decision_reports/phase45_label_decision_report

./.venv-qlib313/bin/python cajas/scripts/build_label_decision_report.py \
  --comparison-report tmp/cajas/label_variant_comparisons/phase44_label_variant_comparison/label_variant_comparison_report.json \
  --output-dir tmp/cajas/label_decision_reports \
  --run-name phase45_label_decision_report \
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

### Commit 1: Phase 41-45 prompt

```bash
git add tasks/phase_041_045_label_redesign_horizon_holdout_prompt.md
git commit -m "docs: add phase 41-45 label redesign prompt"
```

### Commit 2: threshold labels and label variant dataset

```bash
git add cajas/datasets/threshold_label_generator.py \
  cajas/scripts/generate_threshold_labels.py \
  cajas/datasets/label_variant_dataset.py \
  cajas/tests/test_threshold_label_generator.py \
  cajas/tests/test_label_variant_dataset.py \
  cajas/datasets/__init__.py
git commit -m "feat: add threshold label variants"
```

### Commit 3: label variant trainer

```bash
git add cajas/baseline/label_variant_trainer.py \
  cajas/scripts/train_label_variant_holdout.py \
  cajas/tests/test_label_variant_trainer.py \
  cajas/baseline/__init__.py
git commit -m "feat: add label variant holdout training"
```

### Commit 4: comparison and decision report

```bash
git add cajas/reports/label_variant_comparison.py \
  cajas/scripts/compare_label_variants.py \
  cajas/reports/label_decision_report.py \
  cajas/scripts/build_label_decision_report.py \
  cajas/tests/test_label_variant_comparison.py \
  cajas/tests/test_label_decision_report.py \
  cajas/reports/__init__.py
git commit -m "feat: add label variant decision reports"
```

### Commit 5: docs/config

```bash
git add cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  cajas/README.md \
  cajas/docs/qlib_integration_notes.md \
  cajas/data_examples/README.md
git commit -m "docs: document label redesign workflow"
```

Do not run `git push`.

Report manual push command:

```bash
git push origin cajas/market-recognition-phase-0
```

## Completion Report Format

Report exactly in English:

```text
Phase 41-45 completed.

Branch:
- cajas/market-recognition-phase-0

Changed files:
- ...

Threshold label generation:
- train variants:
- holdout variants:
- thresholds:
- horizons:

Label variant training:
- runs completed:
- best variant:
- binary baseline:
- trading metrics present:

Label comparison:
- path:
- primary metric:
- top variants:
- flat ratios:

Label decision report:
- path:
- recommendation:
- rationale:
- trading/profit/backtest recommendations present:

Artifacts:
- label variants:
- variant runs:
- comparison output:
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
- Treat thresholds as trading thresholds.
- Commit raw CSV files.
- Commit `tmp/` outputs.
- Commit `.codex/`.
- Add `tasks/` to `.gitignore`.
- Run `git push`.
