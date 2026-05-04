# Phase 15 Prompt: Track Phase 14B Prompt and Add Qlib DatasetH Compatibility Probe

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
- Codex may add this Phase 15 prompt under `tasks/`.
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

Phase 14B completed with local commits only. User will push manually.

Phase 14B commits:

```text
d0c242b4 docs: add phase 14 training input materialization prompt
20092e36 feat: add label encoding and metric plans
262827ca feat: add training input materialization preview
f0a194a9 docs: document training input materialization preview
```

Phase 14B validation:

```text
real-data materialization csv artifact mode: pass
real-data materialization json/no-csv mode: pass
training executed: false
model built: false
predictions generated: false
model metrics calculated: false
pytest: 82 passed
```

Known current git status from Phase 14B report:

```text
?? .agents/
?? tasks/phase_014b_finalize_training_input_materialization_prompt.md
```

Rules:

- `.agents/` must remain untracked and must not be committed.
- `tasks/phase_014b_finalize_training_input_materialization_prompt.md` should be committed as task history.
- This Phase 15 prompt should also be committed.

## Phase 15 Goal

Phase 15 should add a Qlib DatasetH compatibility probe while still avoiding model training.

Main objectives:

1. Commit the untracked Phase 14B prompt.
2. Add a Qlib availability and DatasetH API compatibility probe.
3. Add a Qlib-style adapter/probe layer that checks whether the current `PreparedDataset` can be shaped toward Qlib DatasetH semantics.
4. Add a CLI that runs the compatibility probe and writes local JSON artifacts.
5. Add tests and docs/config updates.
6. Keep all training disabled.

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
6. Do not commit `.agents/`.
7. Do not add `tasks/` to `.gitignore`.
8. Do not create new task prompt directories.
9. Do not describe `future_direction_8` as a buy/sell signal.
10. Do not train LightGBM or any other model.
11. Do not build, fit, predict, evaluate, or serialize any model.
12. Do not create predictions.
13. Do not calculate model metrics from predictions.
14. Do not run backtest/profit/return analysis.
15. Do not add trading strategy, live execution, auto order, or position sizing logic.
16. Do not install new runtime dependencies automatically.
17. Do not enable training in YAML.
18. Do not run `git push`.
19. Do not claim a config is fully Qlib-runnable unless it has actually been run successfully.

## Task 1: Check State

Run:

```bash
git status --short
git branch --show-current
grep -n "tasks" .gitignore || true
git check-ignore -v tasks/phase_014b_finalize_training_input_materialization_prompt.md || true
```

Expected:

- Current branch is `cajas/market-recognition-phase-0`.
- `.gitignore` should not ignore `tasks/`.
- `.agents/` may be untracked. Do not add it.
- `tasks/phase_014b_finalize_training_input_materialization_prompt.md` should be untracked and should be committed.
- This Phase 15 prompt may also be untracked and should be committed.

## Task 2: Path Hygiene

Run:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py --json
```

If it finds active `caixas/` typo paths, fix them.

Do not rewrite old prompt history unless the typo causes current workflow confusion.

## Task 3: Add Qlib Compatibility Package

Add:

```text
cajas/qlib_compat/__init__.py
cajas/qlib_compat/qlib_probe.py
```

Purpose:

- Probe whether Qlib is importable in the current environment.
- Probe whether key Qlib dataset classes are available.
- Do not modify Qlib core.
- Do not require Qlib import for unit tests to pass when Qlib is unavailable.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class QlibImportStatus:
    module: str
    available: bool
    version: str | None
    import_error: str | None

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class QlibDatasetApiStatus:
    qlib_available: bool
    dataset_h_available: bool
    data_handler_available: bool
    data_handler_lp_available: bool
    imports: list[QlibImportStatus]
    notes: list[str]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def probe_qlib_dataset_api() -> QlibDatasetApiStatus:
    ...
```

Probe modules/classes:

```text
qlib
qlib.data.dataset.DatasetH
qlib.data.dataset.handler.DataHandler
qlib.data.dataset.handler.DataHandlerLP
```

Rules:

- Use safe imports inside functions.
- Do not fail if Qlib is unavailable; return structured unavailable status.
- Do not initialize Qlib.
- Do not call `qlib.init()`.
- Do not access providers.
- Do not train.

## Task 4: Add DatasetH Shape Probe

Add:

```text
cajas/qlib_compat/dataset_shape_probe.py
```

Purpose:

- Check whether current `PreparedDataset.prepare(segment)` output has enough structure to map toward a Qlib DatasetH-style workflow.
- Do not subclass Qlib DatasetH yet unless safe and trivial.
- Do not import Qlib unless needed for shape comparison.
- Do not train.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class SegmentShapeProbe:
    segment: str
    feature_rows: int
    feature_cols: int
    label_rows: int
    feature_index_name: str | None
    label_index_name: str | None
    feature_columns: list[str]
    label_name: str
    row_count_match: bool

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class DatasetHShapeProbeReport:
    config_name: str
    label_col: str
    qlib_dataset_api: dict
    feature_count: int
    segments: list[SegmentShapeProbe]
    compatible_shape: bool
    blockers: list[str]
    warnings: list[str]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def run_dataset_h_shape_probe(
    *,
    config_path: str,
    input_override: str | None = None,
) -> DatasetHShapeProbeReport:
    ...
```

Behavior:

1. Load experiment config.
2. Build workflow config.
3. Build `PreparedDataset`.
4. Prepare all configured segments.
5. Collect feature/label shape and index metadata.
6. Run `probe_qlib_dataset_api()`.
7. `compatible_shape` should be true if:
   - all segments are non-empty
   - feature/label row counts match
   - feature count > 0
   - no leakage columns appear in features
8. Add warnings if Qlib is unavailable or DatasetH import is unavailable.
9. Do not initialize Qlib.
10. Do not train.

## Task 5: Add Optional DatasetH-Like Wrapper Class

Add:

```text
cajas/qlib_compat/prepared_dataset_h_like.py
```

Purpose:

- Provide a tiny DatasetH-like wrapper around `PreparedDataset`.
- This is not a true Qlib subclass.
- This helps future work compare API expectations.

Suggested class:

```python
class PreparedDatasetHLike:
    def __init__(self, prepared_dataset: PreparedDataset) -> None: ...

    def prepare(self, segments, col_set=None, data_key=None):
        ...
```

Behavior:

- If `segments` is a string, return `(features, labels)` for that segment.
- If `segments` is a list/tuple of strings, return a dict mapping segment name to `(features, labels)`.
- Accept `col_set` and `data_key` only for signature compatibility; do not implement complex Qlib semantics.
- Do not import Qlib.
- Do not train.
- Add docstring clearly stating this is only a local compatibility shim.

## Task 6: Add Qlib Compatibility CLI

Add:

```text
cajas/scripts/probe_qlib_dataset_compat.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/probe_qlib_dataset_compat.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Optional flags:

```text
--input-override tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv
--json
--write-artifacts
--output-dir tmp/cajas/qlib_compat
--run-name phase15_qlib_dataset_compat
```

Behavior:

- Text mode prints:
  - config name
  - Qlib import status
  - DatasetH availability
  - DataHandler/DataHandlerLP availability
  - compatible shape yes/no
  - feature count
  - segment shapes
  - blockers
  - warnings
  - training executed false
- JSON mode prints `DatasetHShapeProbeReport.to_dict()`.
- If `--write-artifacts`, write:
  - `qlib_dataset_compat_report.json`
  - `qlib_import_status.json`
- Exit zero if shape is compatible even if Qlib import is unavailable, unless Qlib availability is explicitly required.
- Add optional flag:
  - `--require-qlib`
- If `--require-qlib` and Qlib is unavailable, exit non-zero.
- Do not train.

## Task 7: Extend YAML Config

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Add or update:

```yaml
qlib_compatibility:
  enabled: true
  phase: phase15
  require_qlib_import: false
  initialize_qlib: false
  modify_qlib_core: false
  dataset_h_shape_probe:
    enabled: true
    compatible_shape_required: true
  artifacts:
    default_output_dir: tmp/cajas/qlib_compat
    default_run_name: phase15_qlib_dataset_compat
    generated_files:
      - qlib_dataset_compat_report.json
      - qlib_import_status.json
```

Keep:

```yaml
training:
  enabled: false
```

Clarify:

- This is a compatibility probe only.
- It does not initialize Qlib.
- It does not modify Qlib core.
- It does not train.
- It does not produce trading signals.

## Task 8: Add Tests

Add:

```text
cajas/tests/test_qlib_probe.py
cajas/tests/test_dataset_shape_probe.py
cajas/tests/test_prepared_dataset_h_like.py
```

Tests should use temporary CSV/YAML data.

Qlib probe tests:

- report serializes to dict
- unavailable fake imports handled if helper supports injection
- no exception if Qlib is unavailable
- no `qlib.init()` call

Dataset shape probe tests:

- valid temp dataset has compatible shape
- empty segment produces blocker or incompatible shape
- feature/label row mismatch detection if easy to simulate
- report serialization works

PreparedDatasetHLike tests:

- prepare single segment
- prepare multiple segments
- accepts ignored `col_set` and `data_key`
- unknown segment raises clear error

Do not require Qlib to be installed for tests to pass.

## Task 9: Update Documentation

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should add Phase 15:

- Qlib compatibility probe added.
- DatasetH shape probe added.
- PreparedDatasetHLike shim added.
- CLI command:
  - `probe_qlib_dataset_compat.py`
- Training still disabled.
- No Qlib initialization/core changes/no trading.

Integration notes should add Phase 15:

- This phase verifies whether current prepared data shape can move toward Qlib DatasetH semantics.
- It does not subclass Qlib DatasetH yet.
- It does not initialize Qlib.
- Phase 16 recommendation:
  - add a true Qlib DatasetH wrapper if feasible, still no training; or
  - start controlled baseline training only after explicit user approval.

Data examples should add:

- DatasetH compatibility probe uses prepared CSV outputs.
- No raw rows are written to committed files.
- Compatibility artifacts live under `tmp/`.

## Task 10: Validation Commands

Run:

```bash
git status --short
git branch --show-current
```

Compile:

```bash
./.venv-qlib313/bin/python -m py_compile \
  cajas/qlib_compat/qlib_probe.py \
  cajas/qlib_compat/dataset_shape_probe.py \
  cajas/qlib_compat/prepared_dataset_h_like.py \
  cajas/scripts/probe_qlib_dataset_compat.py
```

Run path hygiene:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Run existing materialization command quickly in no-csv mode:

```bash
rm -rf tmp/cajas/training_input_previews/phase15_no_csv_sanity

./.venv-qlib313/bin/python cajas/scripts/materialize_training_inputs_preview.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --output-dir tmp/cajas/training_input_previews \
  --run-name phase15_no_csv_sanity \
  --no-csv
```

Run Qlib compatibility probe:

```bash
./.venv-qlib313/bin/python cajas/scripts/probe_qlib_dataset_compat.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/probe_qlib_dataset_compat.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --json
```

Run artifact probe:

```bash
rm -rf tmp/cajas/qlib_compat/phase15_qlib_dataset_compat

./.venv-qlib313/bin/python cajas/scripts/probe_qlib_dataset_compat.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --write-artifacts \
  --output-dir tmp/cajas/qlib_compat \
  --run-name phase15_qlib_dataset_compat

find tmp/cajas/qlib_compat/phase15_qlib_dataset_compat -maxdepth 1 -type f -print | sort
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
  cajas/tests/test_training_input_materialization.py \
  cajas/tests/test_qlib_probe.py \
  cajas/tests/test_dataset_shape_probe.py \
  cajas/tests/test_prepared_dataset_h_like.py
```

Check Git:

```bash
git status --short
git diff --stat
git diff
```

Confirm:

- `.agents/` is not staged.
- `tmp/` artifacts are not staged.
- raw CSV is not staged.

## Suggested Commits

Prefer focused commits.

### Commit 1: Phase 14B and Phase 15 prompts

```bash
git add tasks/phase_014b_finalize_training_input_materialization_prompt.md \
  tasks/phase_015_qlib_dataset_compatibility_probe_prompt.md
git commit -m "docs: add phase 15 qlib compatibility prompt"
```

### Commit 2: Qlib compatibility probe

```bash
git add cajas/qlib_compat/__init__.py \
  cajas/qlib_compat/qlib_probe.py \
  cajas/qlib_compat/dataset_shape_probe.py \
  cajas/qlib_compat/prepared_dataset_h_like.py \
  cajas/scripts/probe_qlib_dataset_compat.py \
  cajas/tests/test_qlib_probe.py \
  cajas/tests/test_dataset_shape_probe.py \
  cajas/tests/test_prepared_dataset_h_like.py
git commit -m "feat: add qlib dataset compatibility probe"
```

### Commit 3: docs/config

```bash
git add cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  cajas/README.md \
  cajas/docs/qlib_integration_notes.md \
  cajas/data_examples/README.md
git commit -m "docs: document qlib dataset compatibility probe"
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
Phase 15 completed.

Branch:
- cajas/market-recognition-phase-0

Prompt tracking:
- phase 14B prompt committed:
- phase 15 prompt committed:

Changed files:
- ...

Qlib probe:
- path:
- qlib available:
- DatasetH available:
- DataHandler available:
- DataHandlerLP available:
- qlib initialized:

DatasetH shape probe:
- path:
- compatible shape:
- feature count:
- segments:
- blockers:
- warnings:
- training executed:

PreparedDatasetHLike:
- path:
- single segment prepare:
- multi segment prepare:
- qlib subclass:

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

Untracked intentionally left:
- .agents/ if present

Notes:
- ...
```

## Forbidden Work

Do not:

- Modify `qlib/` core.
- Modify official examples.
- Initialize Qlib unless explicitly required by a later phase.
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
- Commit `.agents/`.
- Add `tasks/` to `.gitignore`.
- Create new task prompt directories.
- Treat `future_direction_8` as a buy/sell signal.
- Run `git push`.
