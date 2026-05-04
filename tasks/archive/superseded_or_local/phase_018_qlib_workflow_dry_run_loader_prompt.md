# Phase 18 Prompt: Add Qlib Workflow Dry-Run Loader Without Execution

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

Phase 17D completed with local commit only.

Phase 17D commit:

```text
ffe052af docs: specialize phase runner skill for qlib-cajas
```

Phase 17D added/updated:

- `.agents/skills/phase-runner/SKILL.md`
- `tasks/phase_017d_qlib_cajas_phase_runner_skill_prompt.md`

The repository-local phase-runner skill now requires:

- English-only Codex communication
- local commits allowed after validation
- no `git push`
- `./.venv-qlib313/bin/python`
- no `init.py`, only `__init__.py`
- no training/trading/Qlib core changes unless explicitly approved by a future phase

Phase 17 added:

- Qlib workflow config probe
- workflow config artifact output
- tests and docs/config updates

Phase 17 validation:

```text
qlib available: true
qlib initialized: false
qlib workflow executed: false
training executed: false
model constructed: false
pytest: 102 passed
```

## Phase 18 Goal

Phase 18 should add a Qlib workflow dry-run loader that resolves and validates the workflow config shape without initializing Qlib, executing workflows, constructing models, or training.

Main objectives:

1. Add import/class resolution utilities for config-declared classes.
2. Add a dry-run workflow loader that validates the Phase 17 Qlib-style workflow config.
3. Validate class paths such as dataset adapter, handler, workflow bridge, and future model family metadata.
4. Add a CLI that reports resolved/unresolved classes and config readiness.
5. Add artifact output for the dry-run loader report.
6. Add tests/docs/config updates.
7. Keep all training disabled.

This phase still does not initialize Qlib.

This phase still does not execute Qlib workflow.

This phase still does not train a model.

This phase still does not build, fit, predict, evaluate, or serialize any model.

This phase still does not modify Qlib core.

This phase still does not introduce trading, backtesting, profit analysis, live execution, automatic ordering, or position sizing.

## Absolute Boundaries

Do not:

- Modify `qlib/` core.
- Modify official upstream examples.
- Initialize Qlib.
- Execute Qlib workflow.
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
- Enable `training.enabled` in YAML.
- Run `git push`.

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
- Working tree should be clean or only contain this Phase 18 prompt if already added.

## Task 2: Path Hygiene

Run:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py --json
```

Expected:

- 0 issues.

If any `caixas/` or `cajas/**/init.py` issue appears, fix it before continuing.

## Task 3: Add Class Resolver Utility

Add:

```text
cajas/qlib_compat/class_resolver.py
```

Purpose:

- Resolve dotted class/function paths safely.
- Use it for dry-run config validation.
- Do not instantiate model classes.
- Do not import Qlib modules in ways that initialize Qlib.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class ClassResolutionResult:
    dotted_path: str
    module_path: str
    attribute_name: str
    resolved: bool
    object_type: str | None
    import_error: str | None

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class ClassResolverReport:
    results: list[ClassResolutionResult]

    @property
    def unresolved(self) -> list[ClassResolutionResult]: ...

    def to_dict(self) -> dict: ...
```

Suggested functions:

```python
def resolve_dotted_path(dotted_path: str) -> ClassResolutionResult:
    ...

def resolve_dotted_paths(paths: list[str] | tuple[str, ...]) -> ClassResolverReport:
    ...
```

Rules:

- Use `importlib.import_module`.
- Catch import errors and attribute errors.
- Return structured results, do not crash for optional unresolved paths.
- Do not instantiate resolved objects.
- Do not call `qlib.init()`.
- Do not train.

## Task 4: Add Qlib Workflow Dry-Run Loader

Add:

```text
cajas/qlib_compat/workflow_dry_run_loader.py
```

Purpose:

- Load the experiment config.
- Build the Phase 17 Qlib-style workflow config.
- Resolve declared classes.
- Validate that training/model/workflow execution flags are disabled.
- Return a structured dry-run report.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class WorkflowDryRunIssue:
    severity: str
    code: str
    message: str

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class WorkflowDryRunLoaderReport:
    config_name: str
    workflow_config_built: bool
    class_resolution: dict
    qlib_available: bool
    qlib_initialized: bool
    qlib_workflow_executed: bool
    training_enabled: bool
    training_executed: bool
    model_enabled: bool
    model_constructed: bool
    dataset_adapter_resolved: bool
    workflow_bridge_resolved: bool
    issues: list[WorkflowDryRunIssue]
    blockers: list[str]
    warnings: list[str]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def run_qlib_workflow_dry_run_loader(
    *,
    config_path: str,
    input_override: str | None = None,
) -> WorkflowDryRunLoaderReport:
    ...
```

Validation rules:

- `training.enabled` must be false.
- workflow config `training_executed` must be false.
- workflow config `model.enabled` must be false.
- workflow config `model.constructed` must be false.
- workflow config `workflow.execute_workflow` must be false.
- workflow config `workflow.qlib_initialized` must be false.
- dataset adapter class should resolve.
- workflow bridge class should resolve if present in the config.
- handler/dataset classes should resolve if present.
- LightGBM model family metadata does not require importing LightGBM in this phase.
- Do not instantiate any model or execute workflow.

## Task 5: Add Workflow Dry-Run Loader CLI

Add:

```text
cajas/scripts/run_qlib_workflow_dry_run_loader.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_qlib_workflow_dry_run_loader.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Optional flags:

```text
--input-override tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv
--json
--write-artifacts
--output-dir tmp/cajas/qlib_workflow_dry_run_loader
--run-name phase18_qlib_workflow_dry_run_loader
```

Behavior:

- Text mode prints:
  - config name
  - workflow config built
  - qlib available
  - qlib initialized false
  - qlib workflow executed false
  - training enabled false
  - training executed false
  - model enabled false
  - model constructed false
  - resolved classes
  - blockers/warnings
- JSON mode prints `WorkflowDryRunLoaderReport.to_dict()`.
- If `--write-artifacts`, write:
  - `qlib_workflow_dry_run_loader_report.json`
  - `class_resolution_report.json`
  - `qlib_workflow_config_draft.json`
- Do not execute workflow.
- Do not train.

## Task 6: Extend YAML Config

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Add or update:

```yaml
qlib_workflow_dry_run_loader:
  enabled: true
  phase: phase18
  initialize_qlib: false
  execute_qlib_workflow: false
  training_enabled: false
  training_executed: false
  model_enabled: false
  model_constructed: false
  resolve_classes: true
  instantiate_classes: false
  artifacts:
    default_output_dir: tmp/cajas/qlib_workflow_dry_run_loader
    default_run_name: phase18_qlib_workflow_dry_run_loader
    generated_files:
      - qlib_workflow_dry_run_loader_report.json
      - class_resolution_report.json
      - qlib_workflow_config_draft.json
```

Keep:

```yaml
training:
  enabled: false
```

Clarify:

- This is a dry-run loader only.
- It resolves classes but does not instantiate model classes.
- It does not initialize Qlib.
- It does not execute Qlib workflow.
- It does not train.
- It does not produce trading signals.

## Task 7: Add Tests

Add:

```text
cajas/tests/test_class_resolver.py
cajas/tests/test_workflow_dry_run_loader.py
```

Tests should use temporary configs where practical.

Class resolver tests:

- resolves known standard-library object
- resolves known project object
- handles missing module
- handles missing attribute
- serialization works

Workflow dry-run loader tests:

- valid temporary config produces report
- training false is enforced
- model enabled false is enforced
- workflow execution false is enforced
- class resolution includes dataset adapter
- JSON serialization works
- artifact writing creates expected files if helper is exposed
- no Qlib initialization
- no model construction/training

Do not require actual Qlib workflow execution.

## Task 8: Update Existing Qlib Docs/CLI References

Update if useful:

```text
cajas/scripts/probe_qlib_workflow_config.py
cajas/scripts/probe_qlib_dataset_h_adapter.py
```

Only add short references to the new dry-run loader; do not break existing CLI behavior.

Update docs:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should add Phase 18:

- Qlib workflow dry-run loader added.
- Class resolver added.
- CLI command:
  - `run_qlib_workflow_dry_run_loader.py`
- Qlib is not initialized.
- Qlib workflow is not executed.
- Training still disabled.
- No model construction/no trading.

Integration notes should add Phase 18:

- Phase 17 built a Qlib-style config draft.
- Phase 18 resolves class paths and validates disabled execution flags.
- This is still not workflow execution.
- Phase 19 recommendation:
  - add a Qlib workflow dry-run manifest registry, or
  - prepare an explicitly approved baseline training phase if the user requests training.

Data examples should add:

- Dry-run loader artifacts live under `tmp/`.
- Class resolution reports do not contain raw rows.
- The draft config remains inspection-only.

## Task 9: Validation Commands

Run:

```bash
git status --short
git branch --show-current
find cajas -path "*/init.py" -print
```

Compile:

```bash
./.venv-qlib313/bin/python -m py_compile \
  cajas/qlib_compat/class_resolver.py \
  cajas/qlib_compat/workflow_dry_run_loader.py \
  cajas/scripts/run_qlib_workflow_dry_run_loader.py
```

Run path hygiene:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Run existing workflow config probe:

```bash
./.venv-qlib313/bin/python cajas/scripts/probe_qlib_workflow_config.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Run new dry-run loader:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_qlib_workflow_dry_run_loader.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/run_qlib_workflow_dry_run_loader.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --json
```

Run artifact smoke:

```bash
rm -rf tmp/cajas/qlib_workflow_dry_run_loader/phase18_qlib_workflow_dry_run_loader

./.venv-qlib313/bin/python cajas/scripts/run_qlib_workflow_dry_run_loader.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --write-artifacts \
  --output-dir tmp/cajas/qlib_workflow_dry_run_loader \
  --run-name phase18_qlib_workflow_dry_run_loader

find tmp/cajas/qlib_workflow_dry_run_loader/phase18_qlib_workflow_dry_run_loader -maxdepth 1 -type f -print | sort
```

Run tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_path_hygiene.py \
  cajas/tests/test_qlib_workflow_config_probe.py \
  cajas/tests/test_class_resolver.py \
  cajas/tests/test_workflow_dry_run_loader.py
```

If reasonable, run full suite:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests
```

Check Git:

```bash
git diff --check
git diff --stat
git status --short
```

Confirm:

- no `cajas/**/init.py`
- `.agents/` unrelated files are not staged unless intended
- `tmp/` artifacts are not staged
- raw CSV is not staged

## Suggested Commits

Prefer focused commits.

### Commit 1: Phase 18 prompt

```bash
git add tasks/phase_018_qlib_workflow_dry_run_loader_prompt.md
git commit -m "docs: add phase 18 qlib workflow dry-run loader prompt"
```

### Commit 2: class resolver and dry-run loader

```bash
git add cajas/qlib_compat/class_resolver.py \
  cajas/qlib_compat/workflow_dry_run_loader.py \
  cajas/scripts/run_qlib_workflow_dry_run_loader.py \
  cajas/tests/test_class_resolver.py \
  cajas/tests/test_workflow_dry_run_loader.py \
  cajas/qlib_compat/__init__.py
git commit -m "feat: add qlib workflow dry-run loader"
```

### Commit 3: docs/config

```bash
git add cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  cajas/README.md \
  cajas/docs/qlib_integration_notes.md \
  cajas/data_examples/README.md
git commit -m "docs: document qlib workflow dry-run loader"
```

Do not run `git push`.

Report manual push command:

```bash
git push origin cajas/market-recognition-phase-0
```

## Completion Report Format

Report exactly in English:

```text
Phase 18 completed.

Branch:
- cajas/market-recognition-phase-0

Changed files:
- ...

Class resolver:
- path:
- resolved project classes:
- unresolved classes:
- qlib initialized:

Workflow dry-run loader:
- path:
- workflow config built:
- qlib available:
- qlib initialized:
- qlib workflow executed:
- training enabled:
- training executed:
- model enabled:
- model constructed:
- dataset adapter resolved:
- workflow bridge resolved:
- blockers:
- warnings:

Artifacts:
- write artifacts:
- run directory:
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
- Initialize Qlib.
- Execute Qlib workflow.
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
