# Phase 16 Prompt: Add Real Qlib DatasetH Adapter Probe Without Training

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
- Codex may add this Phase 16 prompt under `tasks/`.
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

Phase 15 completed with local commits only. User will push manually.

Phase 15 commits:

```text
f09a30dd docs: add phase 15 qlib compatibility prompt
997f67f0 feat: add qlib dataset compatibility probe
29cfe1dc docs: document qlib dataset compatibility probe
```

Phase 15 added:

- `cajas/qlib_compat/qlib_probe.py`
- `cajas/qlib_compat/dataset_shape_probe.py`
- `cajas/qlib_compat/prepared_dataset_h_like.py`
- `cajas/scripts/probe_qlib_dataset_compat.py`
- Qlib compatibility tests
- docs/config updates

Phase 15 validation:

```text
qlib available: true
DatasetH available: true
DataHandler available: true
DataHandlerLP available: true
qlib initialized: false
DatasetH shape compatible: true
feature count: 24
pytest: 92 passed
```

Current untracked item:

```text
?? .agents/
```

Rules:

- `.agents/` must remain untracked and must not be committed unless explicitly requested.
- Do not modify `.agents/` in this phase unless the user explicitly asks.

## Phase 16 Goal

Phase 16 should move from a local DatasetH-like shim to a real Qlib DatasetH adapter probe, while still avoiding any training and avoiding Qlib core changes.

Main objectives:

1. Add a real Qlib DatasetH adapter probe that subclasses or wraps Qlib `DatasetH` only when available.
2. Keep this adapter under `cajas/qlib_compat/`, not under `qlib/`.
3. Do not call `qlib.init()`.
4. Do not train any model.
5. Validate that `prepare("train")`, `prepare(["train", "valid"])`, and segment preparation work with Qlib-compatible API shape.
6. Add a CLI that compares:
   - `PreparedDataset`
   - `PreparedDatasetHLike`
   - real Qlib-compatible adapter
7. Add JSON artifact output.
8. Add tests that pass even if Qlib is unavailable, using skips or graceful fallbacks.
9. Update docs/config.

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
19. Do not call `qlib.init()`.
20. Do not claim the adapter is production-ready or fully Qlib workflow-ready unless validated.

## Task 1: Check State

Run:

```bash
git status --short
git branch --show-current
grep -n "tasks" .gitignore || true
git check-ignore -v tasks/phase_015_qlib_dataset_compatibility_probe_prompt.md || true
```

Expected:

- Current branch is `cajas/market-recognition-phase-0`.
- `.gitignore` should not ignore `tasks/`.
- `.agents/` may be untracked. Do not add it.
- Working tree should be clean or only contain this Phase 16 prompt if already added.

## Task 2: Path Hygiene

Run:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py --json
```

If it finds active `caixas/` typo paths, fix them.

Do not rewrite old prompt history unless the typo causes current workflow confusion.

## Task 3: Add Real Qlib DatasetH Adapter

Add:

```text
cajas/qlib_compat/prepared_dataset_h_adapter.py
```

Purpose:

- Provide a Qlib `DatasetH`-compatible adapter around `PreparedDataset`.
- Keep adapter external to Qlib core.
- Only use Qlib imports if available.
- Do not initialize Qlib.
- Do not train.

Implementation guidance:

- Safely import Qlib `DatasetH` inside the module.
- If Qlib is unavailable, expose a clear availability flag or raise a clear error only when constructing the real adapter.
- Avoid breaking import of `cajas.qlib_compat` if Qlib is unavailable.

Suggested structure:

```python
try:
    from qlib.data.dataset import DatasetH as QlibDatasetH
except Exception:
    QlibDatasetH = None

class PreparedQlibDatasetHAdapter(...):
    ...
```

If subclassing `DatasetH` is too invasive because its constructor expects Qlib-specific internals, use composition and a compatibility class with explicit `is_true_qlib_subclass` metadata.

Recommended behavior:

```python
adapter = PreparedQlibDatasetHAdapter(prepared_dataset)

adapter.prepare("train")
adapter.prepare(["train", "valid"])
adapter.prepare(("train", "valid"))
```

Return shape:

- For a single segment:
  - `(features_df, labels_series)`
- For multiple segments:
  - `{segment_name: (features_df, labels_series)}`

Suggested properties/methods:

```python
@property
def is_qlib_available(self) -> bool: ...

@property
def is_true_qlib_subclass(self) -> bool: ...

def prepare(self, segments, col_set=None, data_key=None): ...

def describe(self) -> dict: ...
```

Rules:

- Accept `col_set` and `data_key` for Qlib-style signature compatibility.
- Keep `col_set` and `data_key` ignored or documented if unsupported.
- Do not call Qlib provider/data loader.
- Do not call `qlib.init()`.
- Do not train.

## Task 4: Add Adapter Comparison Probe

Add:

```text
cajas/qlib_compat/adapter_comparison_probe.py
```

Purpose:

- Compare output shape and metadata from:
  - `PreparedDataset`
  - `PreparedDatasetHLike`
  - `PreparedQlibDatasetHAdapter`
- Report whether outputs match.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class AdapterSegmentComparison:
    segment: str
    prepared_rows: int
    h_like_rows: int
    qlib_adapter_rows: int
    prepared_feature_cols: int
    h_like_feature_cols: int
    qlib_adapter_feature_cols: int
    label_rows_match: bool
    feature_shape_match: bool
    label_values_match: bool

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class AdapterComparisonReport:
    config_name: str
    qlib_available: bool
    qlib_adapter_constructed: bool
    qlib_adapter_true_subclass: bool
    segments: list[AdapterSegmentComparison]
    compatible: bool
    blockers: list[str]
    warnings: list[str]
    training_executed: bool

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def run_adapter_comparison_probe(
    *,
    config_path: str,
    input_override: str | None = None,
) -> AdapterComparisonReport:
    ...
```

Behavior:

1. Load experiment config.
2. Build `PreparedDataset`.
3. Build `PreparedDatasetHLike`.
4. Build `PreparedQlibDatasetHAdapter`.
5. Compare train/valid/test outputs.
6. Mark compatible if:
   - row counts match
   - feature column counts match
   - labels match exactly
   - no leakage columns appear
7. Include warning if adapter is not a true Qlib subclass.
8. Include warning if Qlib unavailable.
9. Do not train.

## Task 5: Add Qlib Adapter Probe CLI

Add:

```text
cajas/scripts/probe_qlib_dataset_h_adapter.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/probe_qlib_dataset_h_adapter.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Optional flags:

```text
--input-override tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv
--json
--require-qlib
--require-true-subclass
--write-artifacts
--output-dir tmp/cajas/qlib_adapter
--run-name phase16_qlib_dataset_h_adapter
```

Behavior:

- Text mode prints:
  - config name
  - qlib available
  - adapter constructed
  - true Qlib subclass yes/no
  - compatible yes/no
  - segment comparisons
  - blockers
  - warnings
  - training executed false
- JSON mode prints `AdapterComparisonReport.to_dict()`.
- If `--require-qlib` and Qlib unavailable, exit non-zero.
- If `--require-true-subclass` and adapter is not a true subclass, exit non-zero.
- If `--write-artifacts`, write:
  - `qlib_dataset_h_adapter_report.json`
  - `qlib_dataset_h_adapter_description.json`
- Do not train.

## Task 6: Extend Existing Compatibility CLI

Update if safe:

```text
cajas/scripts/probe_qlib_dataset_compat.py
```

Optional:

- Add a note pointing users to `probe_qlib_dataset_h_adapter.py`.
- Do not break existing behavior.
- Do not force true adapter probe in existing CLI unless simple and safe.

## Task 7: Extend YAML Config

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Add or update:

```yaml
qlib_dataset_h_adapter:
  enabled: true
  phase: phase16
  initialize_qlib: false
  modify_qlib_core: false
  require_qlib_import: false
  require_true_subclass: false
  adapter_class: cajas.qlib_compat.prepared_dataset_h_adapter.PreparedQlibDatasetHAdapter
  compare_against:
    - cajas.datasets.prepared_dataset.PreparedDataset
    - cajas.qlib_compat.prepared_dataset_h_like.PreparedDatasetHLike
  artifacts:
    default_output_dir: tmp/cajas/qlib_adapter
    default_run_name: phase16_qlib_dataset_h_adapter
    generated_files:
      - qlib_dataset_h_adapter_report.json
      - qlib_dataset_h_adapter_description.json
```

Keep:

```yaml
training:
  enabled: false
```

Clarify:

- This is an adapter compatibility probe only.
- It does not initialize Qlib.
- It does not modify Qlib core.
- It does not train.
- It does not produce trading signals.

## Task 8: Add Tests

Add:

```text
cajas/tests/test_prepared_dataset_h_adapter.py
cajas/tests/test_adapter_comparison_probe.py
```

Tests should use temporary CSV/YAML data.

PreparedQlibDatasetHAdapter tests:

- module imports even if Qlib is unavailable
- adapter constructs when possible
- prepare single segment
- prepare multiple segments
- `describe()` returns stable metadata
- `col_set` and `data_key` accepted
- no `qlib.init()` call

Adapter comparison tests:

- compatible outputs for valid temp dataset
- mismatch detection if easy to simulate
- report serialization works
- training_executed false
- warnings handled if not true subclass

If Qlib-specific subclass tests require Qlib installed, skip gracefully when unavailable.

Do not require Qlib initialization.

## Task 9: Update Documentation

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should add Phase 16:

- Real Qlib DatasetH adapter probe added.
- Adapter comparison probe added.
- CLI command:
  - `probe_qlib_dataset_h_adapter.py`
- Qlib import may be available, but `qlib.init()` is not called.
- Training still disabled.
- No Qlib core changes/no trading.

Integration notes should add Phase 16:

- Phase 15 proved DatasetH/DataHandler imports.
- Phase 16 adds an external Qlib DatasetH adapter probe.
- The adapter remains outside Qlib core.
- Phase 17 recommendation:
  - if the adapter is stable, add a controlled no-fit baseline trainer object that only constructs model config metadata; or
  - add a real Qlib workflow config probe without training.

Data examples should add:

- Adapter probe consumes prepared CSV outputs.
- Compatibility artifacts live under `tmp/`.
- No raw rows are committed.
- No model artifacts are produced.

## Task 10: Validation Commands

Run:

```bash
git status --short
git branch --show-current
```

Compile:

```bash
./.venv-qlib313/bin/python -m py_compile \
  cajas/qlib_compat/prepared_dataset_h_adapter.py \
  cajas/qlib_compat/adapter_comparison_probe.py \
  cajas/scripts/probe_qlib_dataset_h_adapter.py
```

Run path hygiene:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Run existing Qlib compat probe:

```bash
./.venv-qlib313/bin/python cajas/scripts/probe_qlib_dataset_compat.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Run new adapter probe:

```bash
./.venv-qlib313/bin/python cajas/scripts/probe_qlib_dataset_h_adapter.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/probe_qlib_dataset_h_adapter.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --json
```

Run artifact probe:

```bash
rm -rf tmp/cajas/qlib_adapter/phase16_qlib_dataset_h_adapter

./.venv-qlib313/bin/python cajas/scripts/probe_qlib_dataset_h_adapter.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --write-artifacts \
  --output-dir tmp/cajas/qlib_adapter \
  --run-name phase16_qlib_dataset_h_adapter

find tmp/cajas/qlib_adapter/phase16_qlib_dataset_h_adapter -maxdepth 1 -type f -print | sort
```

If Qlib is available, optionally run:

```bash
./.venv-qlib313/bin/python cajas/scripts/probe_qlib_dataset_h_adapter.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --require-qlib
```

Do not run `--require-true-subclass` unless the adapter is actually a true subclass.

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
  cajas/tests/test_prepared_dataset_h_like.py \
  cajas/tests/test_prepared_dataset_h_adapter.py \
  cajas/tests/test_adapter_comparison_probe.py
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

### Commit 1: Phase 16 prompt

```bash
git add tasks/phase_016_qlib_dataset_h_adapter_probe_prompt.md
git commit -m "docs: add phase 16 qlib dataset adapter prompt"
```

### Commit 2: Qlib DatasetH adapter probe

```bash
git add cajas/qlib_compat/prepared_dataset_h_adapter.py \
  cajas/qlib_compat/adapter_comparison_probe.py \
  cajas/scripts/probe_qlib_dataset_h_adapter.py \
  cajas/tests/test_prepared_dataset_h_adapter.py \
  cajas/tests/test_adapter_comparison_probe.py \
  cajas/qlib_compat/__init__.py
git commit -m "feat: add qlib DatasetH adapter probe"
```

### Commit 3: docs/config

```bash
git add cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  cajas/README.md \
  cajas/docs/qlib_integration_notes.md \
  cajas/data_examples/README.md
git commit -m "docs: document qlib DatasetH adapter probe"
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
Phase 16 completed.

Branch:
- cajas/market-recognition-phase-0

Changed files:
- ...

Qlib DatasetH adapter:
- path:
- qlib available:
- true Qlib subclass:
- qlib initialized:
- single segment prepare:
- multi segment prepare:
- training executed:

Adapter comparison:
- path:
- compatible:
- feature count:
- segments:
- blockers:
- warnings:

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
