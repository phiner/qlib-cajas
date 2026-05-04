# Phase 35 Prompt: Add Multi-Year Train Dataset and 2025 External Holdout Validation

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

## New Data Direction

The user has now provided two local EURUSD 15m files:

```text
~/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv
~/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv
```

New experiment split policy:

```text
Train:      2020-01-01 through 2024-12-31 data
Validation: 2025-01-01 through 2025-12-31 data
```

Use 2025 as an external holdout validation year.

Do not treat the 2025 result as a trading/backtest/profit result. It is an out-of-sample market-recognition classification validation only.

## Current Status

Previous phases completed:

- local baseline training
- multi-model baseline comparison
- numeric sanitation
- prediction review
- feature importance
- reports/registry/health checks
- Qlib compatibility probes

Current issue:

- Existing baseline training used the 2025 prepared dataset split into train/valid/test internally.
- That is useful for scaffolding, but not ideal for real validation.
- We now need a proper multi-year training dataset and a true 2025 external holdout validation.

## Phase 35 Goal

Add support for multi-file, multi-period experiments:

1. Prepare 2020-2024 train data.
2. Prepare 2025 holdout data.
3. Combine them into a canonical experiment dataset layout.
4. Train using 2020-2024 only.
5. Validate/evaluate on 2025 only.
6. Write separate artifacts clearly labeled:
   - train period
   - holdout period
   - holdout metrics
7. Keep all outputs under `tmp/`.
8. Keep all trading/backtest/profit logic forbidden.

This phase should produce the first real external-holdout model validation.

## Absolute Boundaries

Allowed in this phase:

- Preparing local CSV data from 2020-2024 and 2025.
- Controlled local classification model training.
- External holdout classification evaluation on 2025.
- Classification metrics and prediction artifacts.
- Feature importance and review artifacts.
- Local report artifacts under `tmp/`.

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
- Working tree should be clean or only contain this Phase 35 prompt if already added.

## Task 2: Path Hygiene

Run:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py --json
```

Expected:

- 0 issues.

If any `caixas/` or `cajas/**/init.py` issue appears, fix it before continuing.

## Task 3: Prepare 2020-2024 and 2025 Datasets

Use existing preparation script if possible:

```text
cajas/scripts/prepare_fx_dataset.py
```

Run:

```bash
rm -rf tmp/cajas/eurusd_15m_2020_2024_phase35_train
rm -rf tmp/cajas/eurusd_15m_2025_phase35_holdout

./.venv-qlib313/bin/python cajas/scripts/prepare_fx_dataset.py \
  --input "$HOME/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv" \
  --output-dir tmp/cajas/eurusd_15m_2020_2024_phase35_train \
  --symbol EURUSD \
  --timeframe 15m

./.venv-qlib313/bin/python cajas/scripts/prepare_fx_dataset.py \
  --input "$HOME/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv" \
  --output-dir tmp/cajas/eurusd_15m_2025_phase35_holdout \
  --symbol EURUSD \
  --timeframe 15m
```

Validate both outputs:

```bash
find tmp/cajas/eurusd_15m_2020_2024_phase35_train -maxdepth 1 -type f -print | sort
find tmp/cajas/eurusd_15m_2025_phase35_holdout -maxdepth 1 -type f -print | sort
```

Expected outputs:

```text
prepared_dataset.csv
dataset_manifest.json
```

Do not commit generated files.

## Task 4: Add External Holdout Dataset Builder

Add:

```text
cajas/datasets/external_holdout_dataset.py
```

Purpose:

- Load one prepared dataset as train source.
- Load another prepared dataset as holdout source.
- Expose train/valid/test-like API where:
  - train = 2020-2024
  - holdout = 2025
- Avoid accidental mixing between train and holdout.
- Preserve label and feature column semantics.
- Exclude leakage columns.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class ExternalHoldoutDatasetSummary:
    train_path: str
    holdout_path: str
    label_col: str
    feature_count: int
    train_rows: int
    holdout_rows: int
    train_time_range: dict
    holdout_time_range: dict
    leakage_columns_in_features: list[str]
    label_distribution_train: dict
    label_distribution_holdout: dict

    def to_dict(self) -> dict: ...
```

Suggested class:

```python
class ExternalHoldoutDataset:
    def __init__(
        self,
        *,
        train_path: str | Path,
        holdout_path: str | Path,
        label_col: str = "future_direction_8",
        leakage_columns: tuple[str, ...] = ("future_close_8", "future_return_8"),
    ) -> None:
        ...

    @property
    def feature_columns(self) -> list[str]:
        ...

    def prepare_train(self):
        # Return train_features, train_labels.
        ...

    def prepare_holdout(self):
        # Return holdout_features, holdout_labels.
        ...

    def summary(self) -> ExternalHoldoutDatasetSummary:
        ...
```

Rules:

- Use existing prepared dataset feature selection logic if possible.
- Do not include `future_close_8` or `future_return_8` in features.
- Do not allow overlap between train and holdout datetime ranges.
- If overlap exists, report blocker/error.
- Do not mutate prepared CSVs.

## Task 5: Add External Holdout Validation Trainer

Add:

```text
cajas/baseline/external_holdout_trainer.py
```

Purpose:

- Train on 2020-2024 prepared data.
- Evaluate on 2025 prepared data.
- Use existing label encoding, numeric sanitizer, feature audit, classification metrics, and model saving where possible.
- Write local artifacts under `tmp/`.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class ExternalHoldoutTrainingReport:
    run_name: str
    model_family_requested: str
    model_family_used: str
    target_label: str
    feature_count: int
    train_rows: int
    holdout_rows: int
    train_time_range: dict
    holdout_time_range: dict
    training_executed: bool
    holdout_evaluation_executed: bool
    model_artifact_created: bool
    prediction_artifacts_created: bool
    metrics_artifacts_created: bool
    output_dir: str
    artifact_files: list[str]
    holdout_metrics: dict
    label_distribution_train: dict
    label_distribution_holdout: dict
    warnings: list[str]
    blockers: list[str]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def train_external_holdout_baseline(
    *,
    train_path: str | Path,
    holdout_path: str | Path,
    output_dir: str | Path,
    run_name: str,
    model_family: str = "LightGBM",
    random_state: int = 42,
) -> ExternalHoldoutTrainingReport:
    ...
```

Artifact requirements:

```text
run_manifest.json
training_config.json
external_holdout_dataset_summary.json
feature_columns.json
label_encoding.json
label_distribution_train.json
label_distribution_holdout.json
metrics_holdout.json
confusion_matrix_holdout.csv
predictions_holdout.csv
feature_value_audit_train.json
feature_value_audit_holdout.json
numeric_sanitization_train.json
numeric_sanitization_holdout.json
model_metadata.json
model.joblib
```

Prediction CSV columns:

```text
datetime
symbol
timeframe
label
encoded_label
predicted_label
predicted_encoded_label
```

Optional probability columns:

```text
proba_down
proba_flat
proba_up
```

Rules:

- Train only on 2020-2024.
- Evaluate only on 2025 holdout.
- Do not use 2025 labels during training.
- Do not create buy/sell/long/short outputs.
- Do not compute trading metrics.
- Append a run registry record.

## Task 6: Add External Holdout CLI

Add:

```text
cajas/scripts/train_external_holdout_baseline.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/train_external_holdout_baseline.py \
  --train tmp/cajas/eurusd_15m_2020_2024_phase35_train/prepared_dataset.csv \
  --holdout tmp/cajas/eurusd_15m_2025_phase35_holdout/prepared_dataset.csv \
  --output-dir tmp/cajas/external_holdout_runs \
  --run-name phase35_train_2020_2024_validate_2025 \
  --model-family LightGBM
```

Optional:

```text
--random-state 42
--json
```

Behavior:

- Text mode prints:
  - run name
  - model family requested/used
  - train period and rows
  - holdout period and rows
  - feature count
  - holdout metrics
  - artifacts written
  - explicit note: no trading/backtest/profit analysis performed
- JSON mode prints report dict.
- Refuse overwrite of existing output directory.
- Do not run Qlib workflow.

## Task 7: Add External Holdout Review / Report Integration

Update or add if useful:

```text
cajas/scripts/inspect_baseline_run.py
cajas/reports/baseline_report_pack.py
cajas/reports/research_report_pack.py
```

Need to support `predictions_holdout.csv` and `metrics_holdout.json`.

Minimum requirement:

- `inspect_baseline_run.py` should not fail on an external holdout run that has `metrics_holdout.json` instead of `metrics_valid.json`/`metrics_test.json`.
- `baseline_report_pack` should include holdout metrics if present.
- Research report pack should mention external holdout validation if present.

Do not over-engineer.

## Task 8: Add Config Section

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Add:

```yaml
external_holdout_validation:
  enabled: true
  phase: phase35
  train_period:
    name: train_2020_2024
    raw_input: ~/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv
    prepared_dir: tmp/cajas/eurusd_15m_2020_2024_phase35_train
  holdout_period:
    name: holdout_2025
    raw_input: ~/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv
    prepared_dir: tmp/cajas/eurusd_15m_2025_phase35_holdout
  model_family: LightGBM
  random_state: 42
  output:
    default_output_dir: tmp/cajas/external_holdout_runs
    default_run_name: phase35_train_2020_2024_validate_2025
  artifacts:
    generated_files:
      - run_manifest.json
      - training_config.json
      - external_holdout_dataset_summary.json
      - feature_columns.json
      - label_encoding.json
      - label_distribution_train.json
      - label_distribution_holdout.json
      - metrics_holdout.json
      - confusion_matrix_holdout.csv
      - predictions_holdout.csv
      - feature_value_audit_train.json
      - feature_value_audit_holdout.json
      - numeric_sanitization_train.json
      - numeric_sanitization_holdout.json
      - model_metadata.json
      - model.joblib
  forbidden_outputs:
    - trading_signals
    - backtest_results
    - profit_metrics
    - order_recommendations
```

Clarify:

- This is external holdout classification validation.
- 2025 is validation/holdout only.
- No trading/backtest/profit analysis.

## Task 9: Add Tests

Add:

```text
cajas/tests/test_external_holdout_dataset.py
cajas/tests/test_external_holdout_trainer.py
```

Tests should use temporary prepared CSV fixtures.

ExternalHoldoutDataset tests:

- train and holdout load separately
- feature columns exclude leakage
- train/holdout row counts correct
- label distributions correct
- time ranges do not overlap
- overlap detection works
- summary serializes

ExternalHoldoutTrainer tests:

- trains on tiny temp train dataset
- evaluates on tiny holdout dataset
- writes expected holdout artifacts
- predictions_holdout exists
- metrics_holdout exists
- source CSVs unchanged
- no trading metrics present
- refuses overwrite

Keep tests small and fast.

## Task 10: Update Documentation

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should add Phase 35:

- External holdout validation added.
- Train on 2020-2024.
- Validate on 2025.
- CLI:
  - `train_external_holdout_baseline.py`
- This is classification validation only.
- No trading/backtest/profit analysis.

Integration notes should add Phase 35:

- This is a major experimental-quality improvement over single-year internal split.
- The 2025 holdout should be interpreted as out-of-sample classification validation.
- It is still not a backtest and not a trading strategy.

Data examples should add:

- Raw data files remain outside repo.
- Prepared outputs stay under `tmp/`.
- 2020-2024 and 2025 are separated by design.

## Task 11: Validation Commands

Run:

```bash
git status --short
git branch --show-current
find cajas -path "*/init.py" -print
```

Compile:

```bash
./.venv-qlib313/bin/python -m py_compile \
  cajas/datasets/external_holdout_dataset.py \
  cajas/baseline/external_holdout_trainer.py \
  cajas/scripts/train_external_holdout_baseline.py
```

Run path hygiene:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_external_holdout_dataset.py \
  cajas/tests/test_external_holdout_trainer.py
```

Run full tests if reasonable:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests
```

Prepare real datasets:

```bash
rm -rf tmp/cajas/eurusd_15m_2020_2024_phase35_train
rm -rf tmp/cajas/eurusd_15m_2025_phase35_holdout

./.venv-qlib313/bin/python cajas/scripts/prepare_fx_dataset.py \
  --input "$HOME/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv" \
  --output-dir tmp/cajas/eurusd_15m_2020_2024_phase35_train \
  --symbol EURUSD \
  --timeframe 15m

./.venv-qlib313/bin/python cajas/scripts/prepare_fx_dataset.py \
  --input "$HOME/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv" \
  --output-dir tmp/cajas/eurusd_15m_2025_phase35_holdout \
  --symbol EURUSD \
  --timeframe 15m
```

Run external holdout training:

```bash
rm -rf tmp/cajas/external_holdout_runs/phase35_train_2020_2024_validate_2025

./.venv-qlib313/bin/python cajas/scripts/train_external_holdout_baseline.py \
  --train tmp/cajas/eurusd_15m_2020_2024_phase35_train/prepared_dataset.csv \
  --holdout tmp/cajas/eurusd_15m_2025_phase35_holdout/prepared_dataset.csv \
  --output-dir tmp/cajas/external_holdout_runs \
  --run-name phase35_train_2020_2024_validate_2025 \
  --model-family LightGBM
```

Run JSON mode with a different run name:

```bash
rm -rf tmp/cajas/external_holdout_runs/phase35_train_2020_2024_validate_2025_json

./.venv-qlib313/bin/python cajas/scripts/train_external_holdout_baseline.py \
  --train tmp/cajas/eurusd_15m_2020_2024_phase35_train/prepared_dataset.csv \
  --holdout tmp/cajas/eurusd_15m_2025_phase35_holdout/prepared_dataset.csv \
  --output-dir tmp/cajas/external_holdout_runs \
  --run-name phase35_train_2020_2024_validate_2025_json \
  --model-family LightGBM \
  --json
```

Inspect artifacts:

```bash
find tmp/cajas/external_holdout_runs/phase35_train_2020_2024_validate_2025 -maxdepth 1 -type f -print | sort
cat tmp/cajas/external_holdout_runs/phase35_train_2020_2024_validate_2025/metrics_holdout.json
cat tmp/cajas/external_holdout_runs/phase35_train_2020_2024_validate_2025/external_holdout_dataset_summary.json
```

Confirm:

- Train rows come from 2020-2024 only.
- Holdout rows come from 2025 only.
- No overlapping datetime ranges.
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

### Commit 1: Phase 35 prompt

```bash
git add tasks/phase_035_external_holdout_validation_prompt.md
git commit -m "docs: add phase 35 external holdout validation prompt"
```

### Commit 2: external holdout dataset

```bash
git add cajas/datasets/external_holdout_dataset.py \
  cajas/tests/test_external_holdout_dataset.py \
  cajas/datasets/__init__.py
git commit -m "feat: add external holdout dataset"
```

### Commit 3: external holdout trainer

```bash
git add cajas/baseline/external_holdout_trainer.py \
  cajas/scripts/train_external_holdout_baseline.py \
  cajas/tests/test_external_holdout_trainer.py \
  cajas/baseline/__init__.py
git commit -m "feat: add external holdout baseline training"
```

### Commit 4: report integration and docs/config

```bash
git add cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  cajas/README.md \
  cajas/docs/qlib_integration_notes.md \
  cajas/data_examples/README.md \
  cajas/scripts/inspect_baseline_run.py \
  cajas/reports/baseline_report_pack.py \
  cajas/reports/research_report_pack.py
git commit -m "docs: document external holdout validation workflow"
```

Only include report integration files if changed.

Do not run `git push`.

Report manual push command:

```bash
git push origin cajas/market-recognition-phase-0
```

## Completion Report Format

Report exactly in English:

```text
Phase 35 completed.

Branch:
- cajas/market-recognition-phase-0

Changed files:
- ...

Prepared datasets:
- train raw input:
- holdout raw input:
- train prepared path:
- holdout prepared path:
- train rows:
- holdout rows:
- train time range:
- holdout time range:

External holdout dataset:
- path:
- feature count:
- leakage columns in features:
- overlap detected:

External holdout training:
- path:
- model family:
- train rows:
- holdout rows:
- training executed:
- holdout evaluation executed:
- holdout metrics:
- trading metrics present:

Artifacts:
- output directory:
- files written:

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
