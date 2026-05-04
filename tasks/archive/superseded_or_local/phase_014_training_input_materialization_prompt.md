# Phase 14 Prompt: Add Baseline Training Readiness Materialization Without Training

## Codex Communication Rules

- Communicate with the user in English only.
- All progress updates, questions, command summaries, and completion reports must be written in English.
- Do not use Chinese in Codex-facing interaction unless the user explicitly asks.
- Do not run `git push`.
- Stop after local commits and report the exact `git push` command for the user to run manually.

## Task Prompt Location

Task prompts are stored inside this repository:

```text
tasks/
```

Rules:

- `tasks/` is tracked by Git as project task history.
- Do not add `tasks/` to `.gitignore`.
- Codex may read files under `tasks/`.
- Codex may add this Phase 14 prompt under `tasks/`.
- Codex must not silently rewrite previous phase prompt files unless explicitly asked.
- Do not create new task prompt directories.

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

Phase 13 completed with local commits only. User will push manually.

Phase 13 commits:

```text
701a4031 docs: add phase 13 future training skeleton prompt
b48c0859 feat: add explicit training enable contract
bf31b705 feat: add future baseline training skeleton
f96691c9 docs: document future training skeleton gates
```

Phase 13 added:

- `cajas/baseline/training_enable_contract.py`
- `cajas/baseline/future_training_skeleton.py`
- `cajas/scripts/build_future_training_skeleton.py`
- `cajas/baseline/baseline_artifacts.py`
- tests for training enable contract, future training skeleton, baseline artifacts
- docs/config updates

Phase 13 validation:

```text
can_enable_training: false
can_train_now: false
training executed: false
model built: false
fit executed: false
prediction executed: false
evaluation executed: false
serialization executed: false
pytest: 70 passed
git status --short: clean
```

## Phase 14 Goal

Phase 14 should add the missing materialization and metric planning layer required before a future approved baseline training phase.

This phase creates data/label/metric artifacts for inspection only.

Main objectives:

1. Add label encoding preview/materialization logic that does not mutate the source CSV.
2. Add dataset materialization preview that exports local feature/label arrays or CSVs only when requested.
3. Add classification metric plan/spec for a future multiclass baseline.
4. Add training input audit report combining features, labels, segments, label encoding, and metric plan.
5. Add a CLI that writes preview artifacts under `tmp/`.
6. Add tests and docs.

This phase still does not train a model.

This phase still does not build, fit, predict, evaluate, or serialize any model.

This phase still does not modify Qlib core.

This phase still does not introduce trading, backtesting, profit analysis, live execution, automatic ordering, or position sizing.

## Absolute Boundaries

Must follow:

1. Do not modify `qlib/` core.
2. Do not modify official upstream examples.
3. Do not commit raw EURUSD CSV files.
4. Do not commit `tmp/` generated outputs.
5. Do not commit `.codex/`.
6. Do not add `tasks/` to `.gitignore`.
7. Do not create new task prompt directories.
8. Do not describe `future_direction_8` as a buy/sell signal.
9. Do not train LightGBM or any other model.
10. Do not build, fit, predict, evaluate, or serialize any model.
11. Do not create predictions.
12. Do not calculate model metrics from predictions.
13. Do not run backtest/profit/return analysis.
14. Do not add trading strategy, live execution, auto order, or position sizing logic.
15. Do not install new runtime dependencies automatically.
16. Do not enable training in YAML.
17. Do not run `git push`.
18. Do not claim a config is fully Qlib-runnable unless it has actually been run successfully.

## Task 1: Check State

Run:

```bash
git status --short
git branch --show-current
grep -n "tasks" .gitignore || true
git check-ignore -v tasks/phase_013_future_training_skeleton_prompt.md || true
```

Expected:

- Current branch is `cajas/market-recognition-phase-0`.
- `.gitignore` should not ignore `tasks/`.
- Working tree should be clean or only contain this Phase 14 prompt if already added.

## Task 2: Add Label Encoding Preview Module

Add:

```text
cajas/baseline/label_encoding.py
```

Purpose:

- Define and validate a future label encoding plan.
- Encode labels only in memory or preview artifacts.
- Do not mutate the prepared source CSV.
- Do not train.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class LabelEncodingPlan:
    label_col: str
    mapping: dict[str, int]
    unknown_label_policy: str = "error"

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class LabelEncodingPreview:
    label_col: str
    mapping: dict[str, int]
    encoded_count: int
    class_counts: dict[str, int]
    encoded_class_counts: dict[int, int]
    unknown_labels: list[str]
    missing_count: int
    issues: list[dict]

    def to_dict(self) -> dict: ...
```

Suggested functions:

```python
def default_future_direction_8_encoding(label_col: str = "future_direction_8") -> LabelEncodingPlan:
    ...

def preview_label_encoding(labels, plan: LabelEncodingPlan) -> LabelEncodingPreview:
    ...

def encode_labels_for_preview(labels, plan: LabelEncodingPlan):
    ...
```

Expected default mapping:

```python
{"down": 0, "flat": 1, "up": 2}
```

Rules:

- Unknown labels are errors.
- Missing labels are errors.
- Keep original labels unchanged.
- Return encoded series/array only for preview/materialization.
- Do not write encoded labels unless a CLI explicitly writes preview artifacts under `tmp/`.

## Task 3: Add Metric Plan Module

Add:

```text
cajas/baseline/metric_plan.py
```

Purpose:

- Define future metrics for multiclass market recognition.
- Do not compute model metrics because there are no predictions.
- Provide a clear spec for a later training phase.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class MetricSpec:
    name: str
    enabled: bool
    reason: str

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class BaselineMetricPlan:
    task_type: str
    target_label: str
    metrics: list[MetricSpec]
    primary_metric: str
    notes: list[str]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def build_multiclass_metric_plan(target_label: str = "future_direction_8") -> BaselineMetricPlan:
    ...
```

Suggested metrics:

```text
accuracy
macro_f1
weighted_f1
per_class_precision
per_class_recall
confusion_matrix
class_distribution
```

Rules:

- Do not calculate these metrics in Phase 14.
- Do not use profit, returns, Sharpe, drawdown, or trading metrics.
- Explain that these are classification metrics only.

## Task 4: Add Training Input Materialization Module

Add:

```text
cajas/baseline/training_input_materialization.py
```

Purpose:

- Prepare future baseline training inputs for inspection only.
- Materialize features and labels by segment only when requested.
- Write local preview files under `tmp/`.
- Do not train.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class SegmentMaterializationSummary:
    segment: str
    feature_rows: int
    feature_cols: int
    label_rows: int
    encoded_label_rows: int
    output_files: dict[str, str]

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class TrainingInputMaterializationReport:
    config_name: str
    label_col: str
    feature_count: int
    label_encoding: dict
    metric_plan: dict
    segments: list[SegmentMaterializationSummary]
    training_enabled: bool
    training_executed: bool
    model_built: bool

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def materialize_training_inputs_preview(
    *,
    config_path: str,
    output_dir: str | Path,
    run_name: str,
    input_override: str | None = None,
    write_csv: bool = True,
) -> TrainingInputMaterializationReport:
    ...
```

Behavior:

1. Load config.
2. Build workflow config.
3. Use `PreparedDataset` to prepare train/valid/test features and labels.
4. Build default label encoding plan.
5. Preview/encode labels in memory.
6. Build metric plan.
7. Create local output directory `<output_dir>/<run_name>/`.
8. If `write_csv`, write:
   - `<segment>_features.csv`
   - `<segment>_labels.csv`
   - `<segment>_encoded_labels.csv`
9. Always write:
   - `training_input_materialization_report.json`
   - `label_encoding_preview.json`
   - `metric_plan.json`
10. Do not write raw source CSV.
11. Do not train.
12. Do not build model.

Allowed local preview artifacts under `tmp/`:

```text
train_features.csv
train_labels.csv
train_encoded_labels.csv
valid_features.csv
valid_labels.csv
valid_encoded_labels.csv
test_features.csv
test_labels.csv
test_encoded_labels.csv
training_input_materialization_report.json
label_encoding_preview.json
metric_plan.json
```

Feature CSVs are derived preview artifacts, not raw source data. They must remain under `tmp/` and must not be committed.

## Task 5: Add Materialization CLI

Add:

```text
cajas/scripts/materialize_training_inputs_preview.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/materialize_training_inputs_preview.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --output-dir tmp/cajas/training_input_previews \
  --run-name phase14_training_inputs_preview
```

Optional flags:

```text
--input-override tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv
--no-csv
--json
```

Behavior:

- Text mode prints:
  - config name
  - label column
  - feature count
  - label encoding mapping
  - metric plan primary metric
  - segment rows
  - files written
  - training enabled false
  - training executed false
  - model built false
- JSON mode prints `TrainingInputMaterializationReport.to_dict()`.
- `--no-csv` writes only JSON report artifacts, no segment CSVs.
- Refuse to overwrite existing run directory.
- Exit non-zero for config/data/encoding errors.
- Do not train.

## Task 6: Extend YAML Config

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Add or update:

```yaml
training_input_preview:
  enabled: true
  phase: phase14
  label_encoding:
    future_direction_8:
      down: 0
      flat: 1
      up: 2
  metrics:
    task_type: multiclass_classification
    primary_metric: macro_f1
    enabled_metrics:
      - accuracy
      - macro_f1
      - weighted_f1
      - per_class_precision
      - per_class_recall
      - confusion_matrix
      - class_distribution
    forbidden_metrics:
      - profit
      - return
      - sharpe
      - drawdown
  artifacts:
    default_output_dir: tmp/cajas/training_input_previews
    default_run_name: phase14_training_inputs_preview
    generated_files:
      - training_input_materialization_report.json
      - label_encoding_preview.json
      - metric_plan.json
```

Keep:

```yaml
training:
  enabled: false
```

Clarify:

- This is input preview/materialization only.
- No model is built.
- No training is executed.
- No predictions or evaluation metrics are computed.
- No trading signal is produced.

## Task 7: Add Tests

Add:

```text
cajas/tests/test_label_encoding.py
cajas/tests/test_metric_plan.py
cajas/tests/test_training_input_materialization.py
```

Tests should use temporary CSV/YAML data.

Label encoding tests:

- default mapping is down=0, flat=1, up=2
- preview counts classes
- unknown label produces issue/error
- missing label produces issue/error
- encoded output does not mutate original labels

Metric plan tests:

- primary metric is classification metric
- forbidden trading metrics absent
- all specs serialize

Materialization tests:

- writes JSON reports
- writes train/valid/test feature/label CSVs when enabled
- `--no-csv` or function equivalent avoids segment CSVs
- report has training_executed false
- report has model_built false
- source CSV is not modified
- refuses overwrite

## Task 8: Update Future Skeleton Integration

Update if useful:

```text
cajas/baseline/future_training_skeleton.py
cajas/scripts/build_future_training_skeleton.py
```

Add references to:

- label encoding plan
- metric plan
- training input materialization preview

Do not make the future skeleton run materialization by default unless simple and safe.

Keep no training.

## Task 9: Update Documentation

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should add Phase 14:

- Label encoding preview added.
- Metric plan added.
- Training input materialization preview added.
- CLI command:
  - `materialize_training_inputs_preview.py`
- Artifacts under `tmp/`.
- Training still disabled.
- No model construction/no fit/no predict/no evaluate/no serialize.
- No Qlib core changes/no trading.

Integration notes should add Phase 14:

- Training inputs can now be previewed/materialized for inspection.
- Label encoding and metrics are planned but not used for training yet.
- Phase 15 recommendation:
  - if user explicitly approves, add a controlled baseline training implementation using these inputs;
  - otherwise add a Qlib DatasetH compatibility probe.

Data examples should add:

- Preview feature CSVs are derived artifacts under `tmp/`.
- Encoded labels are preview artifacts only.
- Source prepared CSV remains unchanged.
- Metrics are classification metrics, not trading metrics.

## Task 10: Path Hygiene

Run:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py --json
```

If it finds `caixas/` typo paths, fix them in active docs/tasks if appropriate.

Do not rewrite old prompt history unless the typo causes current workflow confusion.

## Task 11: Validation Commands

Run:

```bash
git status --short
git branch --show-current
```

Compile:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/baseline/label_encoding.py
./.venv-qlib313/bin/python -m py_compile cajas/baseline/metric_plan.py
./.venv-qlib313/bin/python -m py_compile cajas/baseline/training_input_materialization.py
./.venv-qlib313/bin/python -m py_compile cajas/scripts/materialize_training_inputs_preview.py
```

Run existing commands:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_future_training_skeleton.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/run_baseline_disabled.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Run new materialization preview command:

```bash
rm -rf tmp/cajas/training_input_previews/phase14_training_inputs_preview

./.venv-qlib313/bin/python cajas/scripts/materialize_training_inputs_preview.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --output-dir tmp/cajas/training_input_previews \
  --run-name phase14_training_inputs_preview

find tmp/cajas/training_input_previews/phase14_training_inputs_preview -maxdepth 1 -type f -print | sort
```

Run JSON/no-csv mode:

```bash
rm -rf tmp/cajas/training_input_previews/phase14_training_inputs_preview_json

./.venv-qlib313/bin/python cajas/scripts/materialize_training_inputs_preview.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --output-dir tmp/cajas/training_input_previews \
  --run-name phase14_training_inputs_preview_json \
  --json \
  --no-csv
```

Run tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_prepared_csv_handler.py \
  cajas/tests/test_prepared_dataset.py \
  cajas/tests/test_prepared_workflow.py \
  cajas/tests/test_experiment_config.py \
  cajas/tests/test_experiment_plan_dry_run.py \
  cajas/tests/test_dry_run_recorder.py \
  cajas/tests/test_experiment_plan_artifacts.py \
  cajas/tests/test_feature_audit.py \
  cajas/tests/test_label_audit.py \
  cajas/tests/test_baseline_readiness.py \
  cajas/tests/test_dependency_probe.py \
  cajas/tests/test_baseline_plan.py \
  cajas/tests/test_training_guard.py \
  cajas/tests/test_baseline_scaffold.py \
  cajas/tests/test_path_hygiene.py \
  cajas/tests/test_execution_contract.py \
  cajas/tests/test_baseline_preflight.py \
  cajas/tests/test_run_contract.py \
  cajas/tests/test_baseline_runner.py \
  cajas/tests/test_training_enable_contract.py \
  cajas/tests/test_future_training_skeleton.py \
  cajas/tests/test_baseline_artifacts.py \
  cajas/tests/test_label_encoding.py \
  cajas/tests/test_metric_plan.py \
  cajas/tests/test_training_input_materialization.py
```

Check Git:

```bash
git status --short
git diff --stat
git diff
```

Confirm no raw CSV or `tmp/` generated outputs are staged.

## Suggested Commits

Prefer focused commits.

### Commit 1: Phase 14 prompt

```bash
git add tasks/phase_014_training_input_materialization_prompt.md
git commit -m "docs: add phase 14 training input materialization prompt"
```

### Commit 2: label encoding and metric plan

```bash
git add cajas/baseline/label_encoding.py \
  cajas/baseline/metric_plan.py \
  cajas/tests/test_label_encoding.py \
  cajas/tests/test_metric_plan.py \
  cajas/baseline/__init__.py
git commit -m "feat: add label encoding and metric plans"
```

### Commit 3: training input materialization

```bash
git add cajas/baseline/training_input_materialization.py \
  cajas/scripts/materialize_training_inputs_preview.py \
  cajas/tests/test_training_input_materialization.py
git commit -m "feat: add training input materialization preview"
```

### Commit 4: docs/config

```bash
git add cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  cajas/README.md \
  cajas/docs/qlib_integration_notes.md \
  cajas/data_examples/README.md
git commit -m "docs: document training input materialization preview"
```

Do not run `git push`.

Report the manual push command:

```bash
git push origin cajas/market-recognition-phase-0
```

If a commit has no changes, skip it.

## Completion Report Format

Report exactly in English:

```text
Phase 14 completed.

Branch:
- cajas/market-recognition-phase-0

Changed files:
- ...

Label encoding:
- path:
- mapping:
- unknown label policy:
- source labels mutated:

Metric plan:
- path:
- task type:
- primary metric:
- enabled metrics:
- forbidden trading metrics present:

Training input materialization:
- path:
- feature count:
- segments:
- training enabled:
- training executed:
- model built:
- csv artifacts:
- json artifacts:

Artifacts:
- write artifacts:
- run directory:
- files written:

Validation commands run:
- ...

Tests:
- total:
- result:

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
- Train any model.
- Build/fit/predict/evaluate/serialize any model.
- Create predictions.
- Calculate model metrics from predictions.
- Run backtest/profit analysis.
- Add trading strategy.
- Add live trading/order execution.
- Commit raw CSV files.
- Commit `tmp/` outputs.
- Commit `.codex/`.
- Add `tasks/` to `.gitignore`.
- Create new task prompt directories.
- Treat `future_direction_8` as a buy/sell signal.
- Run `git push`.
