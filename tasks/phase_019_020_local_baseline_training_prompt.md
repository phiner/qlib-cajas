# Phase 19-20 Prompt: Add Run Manifest Registry and Controlled Local Baseline Training

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

## Current Status

Phase 18 completed with local commits only. User will push manually.

Phase 18 commits:

```text
9e220b1d docs: add phase 18 qlib workflow dry-run loader prompt
df92301f feat: add qlib workflow dry-run loader
df04ed85 docs: document qlib workflow dry-run loader
```

Phase 18 added:

- `cajas/qlib_compat/class_resolver.py`
- `cajas/qlib_compat/workflow_dry_run_loader.py`
- `cajas/scripts/run_qlib_workflow_dry_run_loader.py`
- tests/docs/config updates

Phase 18 validation:

```text
qlib available: true
qlib initialized: false
qlib workflow executed: false
training enabled: false
training executed: false
model enabled: false
model constructed: false
pytest cajas/tests: pass
find cajas -path "*/init.py" -print: no output
```

Existing project state:

- Data preparation is complete.
- Prepared dataset exists at:
  - `tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv`
- Label:
  - `future_direction_8`
- Feature count:
  - 24
- Leakage columns excluded from features:
  - `future_close_8`
  - `future_return_8`
- Train/valid/test segments are stable.
- Label encoding plan is stable:
  - `{"down": 0, "flat": 1, "up": 2}`
- Metric plan exists.
- Training input materialization preview exists.
- Dependency probe reports `lightgbm` and `sklearn` available.
- Qlib import/DatasetH/workflow config probes exist.

## Phase 19-20 Goal

This combined phase intentionally merges:

- Phase 19: local run manifest registry for dry-run/training artifacts.
- Phase 20: controlled local baseline training.

The goal is to create the first real local market-recognition baseline training run while preserving safety boundaries.

This phase **does allow controlled local model training** for market-recognition research only.

This phase still forbids:

- trading
- backtesting
- profit analysis
- live execution
- broker/order logic
- position sizing
- Qlib core changes
- treating `future_direction_8` as a buy/sell signal

The trained model is a classification baseline for market recognition, not a trading strategy.

## Absolute Boundaries

Allowed in this phase:

- Local supervised classification baseline training.
- Local model artifact writing under `tmp/`.
- Local metrics from classification predictions.
- Local predictions for validation/test inspection.
- Local run manifest/registry artifacts under `tmp/`.

Forbidden in this phase:

1. Do not modify `qlib/` core.
2. Do not modify official upstream examples.
3. Do not commit raw EURUSD CSV files.
4. Do not commit `tmp/` generated outputs.
5. Do not commit `.codex/`.
6. Do not add `tasks/` to `.gitignore`.
7. Do not create new task prompt directories.
8. Do not describe `future_direction_8` as a buy/sell signal.
9. Do not run backtest/profit/return analysis.
10. Do not calculate trading metrics such as profit, return, Sharpe, drawdown, PnL, win rate, or trade expectancy.
11. Do not add trading strategy, live execution, broker execution, auto order, or position sizing logic.
12. Do not initialize Qlib unless explicitly required and safe. Prefer not to initialize Qlib in this phase.
13. Do not execute Qlib workflow.
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
- Working tree should be clean or only contain this Phase 19-20 prompt if already added.

## Task 2: Path Hygiene

Run:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py --json
```

Expected:

- 0 issues.

If any `caixas/` or `cajas/**/init.py` issue appears, fix it before continuing.

## Task 3: Add Local Run Manifest Registry

Add:

```text
cajas/registry/__init__.py
cajas/registry/run_registry.py
```

Purpose:

- Maintain a local JSONL run registry under `tmp/`.
- Record dry-run, preview, compatibility, and baseline training runs.
- Do not commit generated registry files.
- Use standard library only.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class RunRegistryRecord:
    run_id: str
    run_name: str
    run_type: str
    phase: str
    status: str
    output_dir: str
    artifact_files: list[str]
    created_by: str
    training_executed: bool
    model_artifact_created: bool
    notes: list[str]

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class RunRegistryAppendResult:
    registry_path: str
    record: dict
    total_records: int

    def to_dict(self) -> dict: ...
```

Suggested functions:

```python
def build_run_id(run_name: str, run_type: str) -> str:
    ...

def append_run_registry_record(
    *,
    registry_path: str | Path,
    record: RunRegistryRecord,
) -> RunRegistryAppendResult:
    ...

def read_run_registry(registry_path: str | Path) -> list[dict]:
    ...
```

Rules:

- Registry file should be JSONL.
- Refuse malformed records.
- Create parent directories if needed.
- Do not deduplicate aggressively; this is a local append-only audit log.
- Do not commit registry output.

Default registry path for this project:

```text
tmp/cajas/run_registry/runs.jsonl
```

## Task 4: Add Controlled Local Baseline Training Module

Add:

```text
cajas/baseline/local_baseline_trainer.py
```

Purpose:

- Train a local supervised classification baseline for `future_direction_8`.
- Use existing prepared dataset and label encoding.
- Write local artifacts under `tmp/`.
- Never create trading/backtest/profit outputs.

Model choice:

- Prefer LightGBM if available.
- If LightGBM import or basic training fails, support a sklearn fallback such as `RandomForestClassifier` or `HistGradientBoostingClassifier`.
- Dependency availability should be reported clearly.
- Do not install dependencies.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class LocalBaselineTrainingConfig:
    config_path: str
    output_dir: str
    run_name: str
    model_family: str
    input_override: str | None = None
    random_state: int = 42

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class LocalBaselineTrainingReport:
    config_name: str
    run_name: str
    model_family_requested: str
    model_family_used: str
    target_label: str
    feature_count: int
    train_rows: int
    valid_rows: int
    test_rows: int
    training_executed: bool
    model_artifact_created: bool
    prediction_artifacts_created: bool
    metrics_artifacts_created: bool
    output_dir: str
    artifact_files: list[str]
    metrics: dict
    label_distribution: dict
    warnings: list[str]
    blockers: list[str]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def train_local_baseline(
    *,
    config_path: str,
    output_dir: str | Path,
    run_name: str,
    input_override: str | None = None,
    model_family: str = "LightGBM",
    random_state: int = 42,
) -> LocalBaselineTrainingReport:
    ...
```

Behavior:

1. Load experiment config.
2. Confirm this phase explicitly allows local baseline training.
3. Confirm training is still local research only.
4. Load prepared dataset segments using existing `PreparedDataset`.
5. Use feature columns from existing handler/dataset.
6. Use existing label encoding:
   - down: 0
   - flat: 1
   - up: 2
7. Train on train segment.
8. Predict on valid/test segments.
9. Compute classification metrics only:
   - accuracy
   - macro_f1
   - weighted_f1
   - per-class precision/recall/f1
   - confusion matrix
   - label distribution
10. Write artifacts under `<output_dir>/<run_name>/`.
11. Append run registry record under `tmp/cajas/run_registry/runs.jsonl`.
12. Do not calculate trading metrics.
13. Do not produce buy/sell signals.
14. Do not run backtests.
15. Do not initialize or execute Qlib workflow.
16. Do not modify source CSV.
17. Refuse to overwrite existing run directory.

Artifact requirements:

```text
run_manifest.json
training_config.json
feature_columns.json
label_encoding.json
label_distribution.json
metrics_valid.json
metrics_test.json
confusion_matrix_valid.csv
confusion_matrix_test.csv
predictions_valid.csv
predictions_test.csv
model_metadata.json
model.joblib or model.pkl
```

Prediction CSV columns:

```text
datetime if available
symbol if available
timeframe if available
label
encoded_label
predicted_label
predicted_encoded_label
```

Optional probability columns if available:

```text
proba_down
proba_flat
proba_up
```

Important:

- Predictions are classification inspection artifacts.
- They are not trading signals.
- Do not name them buy/sell/long/short.

## Task 5: Add Baseline Training CLI

Add:

```text
cajas/scripts/train_local_baseline.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/train_local_baseline.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --output-dir tmp/cajas/baseline_runs \
  --run-name phase20_local_baseline
```

Optional flags:

```text
--input-override tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv
--model-family LightGBM
--random-state 42
--json
```

Behavior:

- Text mode prints:
  - config name
  - run name
  - model family requested/used
  - target label
  - feature count
  - train/valid/test rows
  - training executed true
  - model artifact created true
  - prediction artifacts created true
  - metrics artifact created true
  - artifact files
  - run registry path
  - explicit warning: no trading/backtest/profit analysis performed
- JSON mode prints `LocalBaselineTrainingReport.to_dict()`.
- Exit non-zero on training/data/config failures.
- Refuse overwrite of existing run directory.

## Task 6: Add Classification Metrics Helper

Add:

```text
cajas/baseline/classification_metrics.py
```

Purpose:

- Compute classification-only metrics.
- Avoid trading metrics.

Suggested functions:

```python
def compute_classification_metrics(
    *,
    y_true,
    y_pred,
    labels: list[int],
    label_names: list[str],
) -> dict:
    ...

def confusion_matrix_to_rows(
    *,
    matrix,
    label_names: list[str],
) -> list[dict]:
    ...
```

Use sklearn metrics if available:

- accuracy_score
- f1_score
- precision_recall_fscore_support
- confusion_matrix

Rules:

- No profit/return/Sharpe/drawdown/PnL metrics.
- No trading terminology.

## Task 7: Update YAML Config

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Add or update:

```yaml
local_baseline_training:
  enabled: true
  phase: phase20
  scope: market_recognition_classification_only
  model_family: LightGBM
  fallback_model_family: sklearn_random_forest
  random_state: 42
  output:
    default_output_dir: tmp/cajas/baseline_runs
    default_run_name: phase20_local_baseline
    registry_path: tmp/cajas/run_registry/runs.jsonl
  artifacts:
    generated_files:
      - run_manifest.json
      - training_config.json
      - feature_columns.json
      - label_encoding.json
      - label_distribution.json
      - metrics_valid.json
      - metrics_test.json
      - confusion_matrix_valid.csv
      - confusion_matrix_test.csv
      - predictions_valid.csv
      - predictions_test.csv
      - model_metadata.json
      - model.joblib
  forbidden_outputs:
    - trading_signals
    - backtest_results
    - profit_metrics
    - order_recommendations
```

Training section:

- If current `training.enabled` remains false for Qlib workflow, keep it false.
- Add clear note that `local_baseline_training.enabled: true` is separate from Qlib workflow training and allows only local research baseline training.
- Do not set global Qlib workflow `training.enabled` to true unless the config already has a separate local baseline section.

Clarify:

- This is local baseline training, not Qlib workflow training.
- No trading signal is produced.
- No backtest/profit analysis is performed.

## Task 8: Add Tests

Add:

```text
cajas/tests/test_run_registry.py
cajas/tests/test_classification_metrics.py
cajas/tests/test_local_baseline_trainer.py
```

Tests should use temporary CSV/YAML data.

Run registry tests:

- append record
- read records
- JSONL valid
- total count correct
- malformed record rejected if applicable

Classification metrics tests:

- accuracy/macro_f1/weighted_f1 computed
- confusion matrix rows stable
- no trading metric keys present

Local baseline trainer tests:

- uses temp dataset
- trains a small model or fallback model
- writes expected artifacts
- writes predictions_valid/test
- writes metrics_valid/test
- writes model metadata
- appends run registry
- refuses overwrite
- does not include trading metrics
- report says training_executed true
- report says no backtest/profit/trading output

Tests should not require large real data.

If LightGBM behavior is slow or brittle, tests may force sklearn fallback or use a small sklearn model path.

## Task 9: Update Documentation

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should add Phase 19-20:

- Run manifest registry added.
- Controlled local baseline training added.
- CLI command:
  - `train_local_baseline.py`
- Artifacts written under `tmp/`.
- This is market-recognition classification only.
- No trading/backtest/profit analysis.
- No Qlib core changes.
- No Qlib workflow execution.

Integration notes should add Phase 19-20:

- The first model training is local baseline training, not Qlib workflow training.
- Qlib compatibility work remains useful for later phases.
- Baseline output is classification metrics and predictions for inspection.
- Phase 21 recommendation:
  - add model artifact inspection and prediction review tooling;
  - optionally compare LightGBM vs sklearn fallback;
  - do not add trading logic.

Data examples should add:

- Baseline training uses prepared CSV and existing segments.
- Prediction artifacts are classification inspection outputs, not trading signals.
- Metrics are classification-only.

## Task 10: Validation Commands

Run:

```bash
git status --short
git branch --show-current
find cajas -path "*/init.py" -print
```

Compile:

```bash
./.venv-qlib313/bin/python -m py_compile \
  cajas/registry/run_registry.py \
  cajas/baseline/classification_metrics.py \
  cajas/baseline/local_baseline_trainer.py \
  cajas/scripts/train_local_baseline.py
```

Run path hygiene:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Run unit tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_run_registry.py \
  cajas/tests/test_classification_metrics.py \
  cajas/tests/test_local_baseline_trainer.py
```

Run full test suite if reasonable:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests
```

Run real-data local baseline smoke:

```bash
rm -rf tmp/cajas/baseline_runs/phase20_local_baseline

./.venv-qlib313/bin/python cajas/scripts/train_local_baseline.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --output-dir tmp/cajas/baseline_runs \
  --run-name phase20_local_baseline
```

Run JSON mode with a different run name:

```bash
rm -rf tmp/cajas/baseline_runs/phase20_local_baseline_json

./.venv-qlib313/bin/python cajas/scripts/train_local_baseline.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --output-dir tmp/cajas/baseline_runs \
  --run-name phase20_local_baseline_json \
  --json
```

Inspect artifacts:

```bash
find tmp/cajas/baseline_runs/phase20_local_baseline -maxdepth 1 -type f -print | sort
cat tmp/cajas/baseline_runs/phase20_local_baseline/metrics_valid.json
cat tmp/cajas/baseline_runs/phase20_local_baseline/metrics_test.json
tail -n 5 tmp/cajas/run_registry/runs.jsonl
```

Confirm:

- `training_executed` is true only for local baseline training.
- No Qlib workflow executed.
- No backtest/profit/trading output exists.
- `tmp/` artifacts are not staged.

Run:

```bash
git diff --check
git diff --stat
git status --short
```

Confirm:

- no `cajas/**/init.py`
- no `tmp/` artifacts staged
- raw CSV not staged
- `.codex/` not staged

## Suggested Commits

Prefer focused commits.

### Commit 1: Phase 19-20 prompt

```bash
git add tasks/phase_019_020_local_baseline_training_prompt.md
git commit -m "docs: add phase 19-20 local baseline training prompt"
```

### Commit 2: run registry

```bash
git add cajas/registry/__init__.py \
  cajas/registry/run_registry.py \
  cajas/tests/test_run_registry.py
git commit -m "feat: add local run registry"
```

### Commit 3: local baseline trainer

```bash
git add cajas/baseline/classification_metrics.py \
  cajas/baseline/local_baseline_trainer.py \
  cajas/scripts/train_local_baseline.py \
  cajas/tests/test_classification_metrics.py \
  cajas/tests/test_local_baseline_trainer.py \
  cajas/baseline/__init__.py
git commit -m "feat: add controlled local baseline training"
```

### Commit 4: docs/config

```bash
git add cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  cajas/README.md \
  cajas/docs/qlib_integration_notes.md \
  cajas/data_examples/README.md
git commit -m "docs: document controlled local baseline training"
```

Do not run `git push`.

Report manual push command:

```bash
git push origin cajas/market-recognition-phase-0
```

## Completion Report Format

Report exactly in English:

```text
Phase 19-20 completed.

Branch:
- cajas/market-recognition-phase-0

Changed files:
- ...

Run registry:
- path:
- registry path:
- records appended:
- committed registry output:

Local baseline training:
- path:
- model family requested:
- model family used:
- target label:
- feature count:
- train rows:
- valid rows:
- test rows:
- training executed:
- model artifact created:
- prediction artifacts created:
- metrics artifacts created:
- qlib workflow executed:
- trading/backtest/profit outputs:

Metrics:
- valid:
- test:
- trading metrics present:

Artifacts:
- output directory:
- files written:
- registry updated:

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
