# Phase 27-30 Prompt: Add Numeric Sanitation, Robust Model Comparison, Report Exports, and Run Health Checks

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

## Current Status

Phase 23-26 completed with local commits only. User will push manually.

Phase 23-26 commits:

```text
7189eb5c docs: add phase 23-26 baseline reporting prompt
f8ef254c feat: add baseline report pack
679aa665 feat: add multi-model baseline comparison
d774265a feat: add feature importance summary
3cdfaee8 feat: add run registry summary reports
c66539d6 docs: document baseline reporting and comparison workflow
```

Phase 23-26 added:

- baseline report pack
- multi-model baseline comparison
- feature importance summary
- run registry summary reports
- Phase 22 capability files as part of the combined phase:
  - baseline run comparison
  - feature importance inspection

Phase 23-26 validation:

```text
focused tests: 7 passed
full tests: 135 passed
```

Important observed issue:

```text
RandomForest failed during real multi-model run with:
Input X contains infinity or a value too large for dtype('float32')
```

The multi-model run continued and completed with other model families.

This issue should be fixed in this phase by adding safe numeric sanitation and feature-value auditing before sklearn model training.

## Phase 27-30 Goal

This combined phase should stabilize the local baseline workflow after the first multi-model experiments.

### Phase 27: Numeric Sanitation and Feature Value Audit

- Detect NaN, infinity, and extremely large feature values.
- Add a safe numeric transformer/sanitizer for model training inputs.
- Preserve source CSV unchanged.
- Write audit reports under `tmp/`.

### Phase 28: Robust Multi-Model Training

- Update local baseline trainer so sklearn model families can safely handle finite numeric inputs.
- Retry or skip models with clear error reports.
- Add robust per-model status artifacts.

### Phase 29: Markdown/CSV Report Export

- Export human-readable Markdown summaries for baseline runs, comparisons, feature importance, and registry summaries.
- Keep them local under `tmp/`.

### Phase 30: Run Health Check

- Add a health check over baseline artifacts and registry records.
- Detect failed/skipped runs, missing artifacts, suspicious metrics, unavailable feature importance, and training output completeness.

## Absolute Boundaries

Allowed in this phase:

- Local supervised classification model training.
- Local model comparison.
- Local classification metrics.
- Numeric sanitation for training inputs.
- Local report/export generation under `tmp/`.
- Local run health checks.

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
- Working tree should be clean or only contain this Phase 27-30 prompt if already added.

## Task 2: Path Hygiene

Run:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py --json
```

Expected:

- 0 issues.

If any `caixas/` or `cajas/**/init.py` issue appears, fix it before continuing.

## Task 3: Add Feature Value Audit

Add:

```text
cajas/baseline/feature_value_audit.py
```

Purpose:

- Inspect model feature matrices for values that can break sklearn/LightGBM training.
- Detect:
  - NaN
  - positive/negative infinity
  - extremely large absolute values
  - columns with too many non-finite values
- Produce classification-training input audit reports.
- Do not mutate source data.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class FeatureValueIssue:
    severity: str
    code: str
    message: str
    column: str | None = None
    count: int | None = None

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class FeatureValueAuditReport:
    row_count: int
    feature_count: int
    nan_count: int
    pos_inf_count: int
    neg_inf_count: int
    large_value_count: int
    max_abs_value: float | None
    columns_with_issues: list[str]
    issues: list[FeatureValueIssue]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def audit_feature_values(
    features_df,
    *,
    large_value_threshold: float = 1e12,
) -> FeatureValueAuditReport:
    ...
```

Rules:

- NaN should be warning unless widespread.
- Infinity should be error.
- Extremely large values should be warning or error depending on count.
- Do not mutate input DataFrame.
- Use pandas/numpy available in venv.

## Task 4: Add Numeric Sanitizer

Add:

```text
cajas/baseline/numeric_sanitizer.py
```

Purpose:

- Convert features into finite model-safe numeric matrices.
- Preserve column order.
- Preserve source CSV unchanged.
- Produce sanitation report.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class NumericSanitizationReport:
    row_count: int
    feature_count: int
    nan_replaced: int
    pos_inf_replaced: int
    neg_inf_replaced: int
    clipped_values: int
    clip_abs_value: float
    fill_value: float
    warnings: list[str]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def sanitize_features_for_model(
    features_df,
    *,
    clip_abs_value: float = 1e6,
    fill_value: float = 0.0,
):
    # Return (sanitized_df, report).
    ...
```

Behavior:

- Convert to numeric where possible.
- Replace `+inf` with `clip_abs_value`.
- Replace `-inf` with `-clip_abs_value`.
- Clip absolute values above `clip_abs_value`.
- Replace NaN with `fill_value`.
- Preserve index and columns.
- Return sanitized copy, not mutate original.
- Add tests proving original is unchanged.

## Task 5: Integrate Sanitizer Into Local Baseline Trainer

Update:

```text
cajas/baseline/local_baseline_trainer.py
```

Required behavior:

- Audit raw feature values before training.
- Sanitize train/valid/test features for model fitting and prediction.
- Write sanitation reports:
  - `feature_value_audit_train.json`
  - `feature_value_audit_valid.json`
  - `feature_value_audit_test.json`
  - `numeric_sanitization_train.json`
  - `numeric_sanitization_valid.json`
  - `numeric_sanitization_test.json`
- Include sanitation summary in:
  - `run_manifest.json`
  - `model_metadata.json`
  - training report dict
- Keep source prepared CSV unchanged.
- Ensure RandomForest no longer fails on inf/large values during real multi-model run.

Important:

- Sanitization is for model input only.
- Do not hide this transformation; report it clearly.
- Do not use sanitized values to generate trading logic.

## Task 6: Improve Multi-Model Baseline Robustness

Update:

```text
cajas/baseline/multi_model_baseline.py
cajas/scripts/train_multi_model_baselines.py
```

Required behavior:

- Each model family should produce a per-model status:
  - completed
  - skipped
  - failed
- Failures should be recorded in the multi-model report, not crash the whole multi-model run unless all models fail.
- RandomForest should run successfully after numeric sanitation.
- If a model still fails, include clear error string.
- Write:
  - `multi_model_baseline_report.json`
  - `multi_model_metrics.csv`
  - `model_run_status.csv`
- Keep classification-only metrics.
- No trading metrics.

## Task 7: Add Markdown Report Exporter

Add:

```text
cajas/reports/markdown_report_exporter.py
```

Purpose:

- Export human-readable markdown summaries from existing report dicts.
- Keep generated reports under `tmp/`.
- Do not include raw data rows.

Suggested functions:

```python
def write_markdown_report(
    *,
    output_path: str | Path,
    title: str,
    sections: list[tuple[str, str]],
) -> str:
    ...

def render_baseline_report_pack_markdown(report: dict) -> str:
    ...

def render_multi_model_comparison_markdown(report: dict) -> str:
    ...

def render_registry_summary_markdown(report: dict) -> str:
    ...
```

Rules:

- Markdown should summarize classification metrics and artifacts.
- Do not include trading language.
- Do not include raw predictions or raw data rows.

## Task 8: Add Report Export CLI

Add:

```text
cajas/scripts/export_baseline_reports.py
```

Purpose:

- Convert existing JSON reports into Markdown/CSV summary packs.

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/export_baseline_reports.py   --report-json tmp/cajas/baseline_report_packs/phase23_baseline_report_pack/baseline_report_pack.json   --output-dir tmp/cajas/exported_reports   --run-name phase29_exported_reports
```

Optional flags:

```text
--title "EURUSD 15m Baseline Report"
--json
```

Artifacts:

```text
baseline_report.md
export_manifest.json
```

If multiple report JSON files are supported, keep it simple and documented.

## Task 9: Add Run Health Check Module

Add:

```text
cajas/registry/run_health_check.py
```

Purpose:

- Check local run registry and artifact directories for health.
- Detect:
  - missing registry
  - missing artifact directory
  - missing required files
  - failed/skipped model runs
  - missing metrics
  - missing model artifact for completed training runs
  - suspicious metric values outside [0, 1]
  - trading metric keys if any appear
- Produce structured health report.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class RunHealthIssue:
    severity: str
    code: str
    message: str
    run_name: str | None = None

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class RunHealthReport:
    registry_path: str
    total_records: int
    checked_runs: int
    healthy_runs: int
    warning_count: int
    error_count: int
    issues: list[RunHealthIssue]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def check_run_registry_health(
    *,
    registry_path: str | Path,
) -> RunHealthReport:
    ...
```

Rules:

- Do not fail if registry missing; return warning/error in report.
- Do not compute trading metrics.
- Do not load model unless needed.
- Use artifact metadata and required file existence.

## Task 10: Add Run Health CLI

Add:

```text
cajas/scripts/check_run_health.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_run_health.py   --registry tmp/cajas/run_registry/runs.jsonl   --output-dir tmp/cajas/run_health   --run-name phase30_run_health   --write-artifacts
```

Optional flags:

```text
--json
```

Artifacts:

```text
run_health_report.json
run_health_issues.csv
```

## Task 11: Extend YAML Config

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Add or update sections:

```yaml
numeric_sanitation:
  enabled: true
  phase: phase27
  clip_abs_value: 1000000.0
  fill_value: 0.0
  large_value_threshold: 1000000000000.0
  artifacts:
    generated_files:
      - feature_value_audit_train.json
      - feature_value_audit_valid.json
      - feature_value_audit_test.json
      - numeric_sanitization_train.json
      - numeric_sanitization_valid.json
      - numeric_sanitization_test.json

robust_multi_model_baseline:
  enabled: true
  phase: phase28
  continue_on_model_failure: true
  require_at_least_one_completed_model: true
  status_artifacts:
    - multi_model_baseline_report.json
    - multi_model_metrics.csv
    - model_run_status.csv

baseline_report_exports:
  enabled: true
  phase: phase29
  output:
    default_output_dir: tmp/cajas/exported_reports
    default_run_name: phase29_exported_reports
  artifacts:
    generated_files:
      - baseline_report.md
      - export_manifest.json

run_health_check:
  enabled: true
  phase: phase30
  registry_path: tmp/cajas/run_registry/runs.jsonl
  output:
    default_output_dir: tmp/cajas/run_health
    default_run_name: phase30_run_health
  artifacts:
    generated_files:
      - run_health_report.json
      - run_health_issues.csv
```

Clarify:

- Numeric sanitation applies only to model input matrices.
- Source CSV remains unchanged.
- Reports remain classification-only.
- No trading metrics are generated.

## Task 12: Add Tests

Add tests:

```text
cajas/tests/test_feature_value_audit.py
cajas/tests/test_numeric_sanitizer.py
cajas/tests/test_markdown_report_exporter.py
cajas/tests/test_run_health_check.py
```

Update existing tests:

```text
cajas/tests/test_local_baseline_trainer.py
cajas/tests/test_multi_model_baseline.py
```

Test coverage:

Feature value audit:

- detects NaN
- detects +inf/-inf
- detects large values
- serializes report

Numeric sanitizer:

- replaces NaN
- replaces infinities
- clips large values
- preserves columns/index
- does not mutate original

Local baseline trainer:

- writes audit/sanitization reports
- training succeeds with inf-containing temp fixture after sanitation
- no trading metrics present

Multi-model baseline:

- RandomForest succeeds or records clear status after sanitation
- failures do not crash all runs
- model_run_status.csv exists

Markdown exporter:

- writes markdown
- does not include raw rows
- no trading terms beyond explicit forbidden note if present

Run health:

- missing registry handled
- healthy run detected
- missing artifact detected
- suspicious metric detected
- trading metric key detected as issue if injected in fixture

## Task 13: Update Documentation

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should add Phase 27-30:

- Numeric sanitation
- Robust multi-model baseline
- Markdown report exports
- Run health checks
- CLI commands:
  - `export_baseline_reports.py`
  - `check_run_health.py`
- No trading/backtest/profit analysis.

Integration notes should add Phase 27-30:

- RandomForest issue was caused by non-finite/large feature values and is addressed by model-input sanitation.
- Sanitization does not mutate source CSV.
- Multi-model comparison remains classification-only.
- Phase 31 recommendation:
  - add prediction review dashboard data export; or
  - add model calibration/threshold analysis for classification confidence only, not trading.

Data examples should add:

- Sanitized matrices are model-input transformations only.
- Generated reports live under `tmp/`.
- Source prepared CSV remains unchanged.

## Task 14: Validation Commands

Run:

```bash
git status --short
git branch --show-current
find cajas -path "*/init.py" -print
```

Compile all new/changed modules/scripts:

```bash
./.venv-qlib313/bin/python -m py_compile   cajas/baseline/feature_value_audit.py   cajas/baseline/numeric_sanitizer.py   cajas/baseline/local_baseline_trainer.py   cajas/baseline/multi_model_baseline.py   cajas/reports/markdown_report_exporter.py   cajas/scripts/export_baseline_reports.py   cajas/registry/run_health_check.py   cajas/scripts/check_run_health.py
```

Run path hygiene:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest   cajas/tests/test_feature_value_audit.py   cajas/tests/test_numeric_sanitizer.py   cajas/tests/test_local_baseline_trainer.py   cajas/tests/test_multi_model_baseline.py   cajas/tests/test_markdown_report_exporter.py   cajas/tests/test_run_health_check.py
```

Run full tests if reasonable:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests
```

Run real local baseline with sanitation:

```bash
rm -rf tmp/cajas/baseline_runs/phase27_sanitized_lightgbm

./.venv-qlib313/bin/python cajas/scripts/train_local_baseline.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml   --output-dir tmp/cajas/baseline_runs   --run-name phase27_sanitized_lightgbm   --model-family LightGBM

find tmp/cajas/baseline_runs/phase27_sanitized_lightgbm -maxdepth 1 -type f -print | sort
```

Run robust multi-model baseline:

```bash
rm -rf tmp/cajas/multi_model_baselines/phase28_robust_multi_model

./.venv-qlib313/bin/python cajas/scripts/train_multi_model_baselines.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml   --output-dir tmp/cajas/multi_model_baselines   --run-name phase28_robust_multi_model   --model-family LightGBM   --model-family RandomForest   --model-family HistGradientBoosting   --primary-metric test_macro_f1

find tmp/cajas/multi_model_baselines/phase28_robust_multi_model -maxdepth 2 -type f -print | sort | head -100
cat tmp/cajas/multi_model_baselines/phase28_robust_multi_model/model_run_status.csv
```

Confirm RandomForest no longer fails due inf/large values. If it still fails, the run must record a clear failure status and at least one other model must complete.

Run report export:

```bash
if [ ! -f tmp/cajas/baseline_report_packs/phase23_baseline_report_pack/baseline_report_pack.json ]; then
  ./.venv-qlib313/bin/python cajas/scripts/build_baseline_report_pack.py     --run-dir tmp/cajas/baseline_runs/phase20_local_baseline     --output-dir tmp/cajas/baseline_report_packs     --run-name phase23_baseline_report_pack
fi

rm -rf tmp/cajas/exported_reports/phase29_exported_reports

./.venv-qlib313/bin/python cajas/scripts/export_baseline_reports.py   --report-json tmp/cajas/baseline_report_packs/phase23_baseline_report_pack/baseline_report_pack.json   --output-dir tmp/cajas/exported_reports   --run-name phase29_exported_reports   --title "EURUSD 15m Baseline Report"

find tmp/cajas/exported_reports/phase29_exported_reports -maxdepth 1 -type f -print | sort
```

Run health check:

```bash
rm -rf tmp/cajas/run_health/phase30_run_health

./.venv-qlib313/bin/python cajas/scripts/check_run_health.py   --registry tmp/cajas/run_registry/runs.jsonl   --output-dir tmp/cajas/run_health   --run-name phase30_run_health   --write-artifacts

find tmp/cajas/run_health/phase30_run_health -maxdepth 1 -type f -print | sort
```

Run JSON modes for new CLIs where practical.

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

### Commit 1: Phase 27-30 prompt

```bash
git add tasks/phase_027_030_numeric_sanitation_reporting_health_prompt.md
git commit -m "docs: add phase 27-30 sanitation and reporting prompt"
```

### Commit 2: numeric sanitation

```bash
git add cajas/baseline/feature_value_audit.py   cajas/baseline/numeric_sanitizer.py   cajas/tests/test_feature_value_audit.py   cajas/tests/test_numeric_sanitizer.py   cajas/baseline/local_baseline_trainer.py   cajas/tests/test_local_baseline_trainer.py   cajas/baseline/__init__.py
git commit -m "feat: add numeric sanitation for baseline training"
```

### Commit 3: robust multi-model

```bash
git add cajas/baseline/multi_model_baseline.py   cajas/tests/test_multi_model_baseline.py   cajas/scripts/train_multi_model_baselines.py
git commit -m "feat: harden multi-model baseline runs"
```

### Commit 4: markdown report exports

```bash
git add cajas/reports/markdown_report_exporter.py   cajas/scripts/export_baseline_reports.py   cajas/tests/test_markdown_report_exporter.py   cajas/reports/__init__.py
git commit -m "feat: add baseline markdown report exports"
```

### Commit 5: run health checks

```bash
git add cajas/registry/run_health_check.py   cajas/scripts/check_run_health.py   cajas/tests/test_run_health_check.py   cajas/registry/__init__.py
git commit -m "feat: add run registry health checks"
```

### Commit 6: docs/config

```bash
git add cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml   cajas/README.md   cajas/docs/qlib_integration_notes.md   cajas/data_examples/README.md
git commit -m "docs: document sanitation reporting and run health workflow"
```

Do not run `git push`.

Report manual push command:

```bash
git push origin cajas/market-recognition-phase-0
```

## Completion Report Format

Report exactly in English:

```text
Phase 27-30 completed.

Branch:
- cajas/market-recognition-phase-0

Changed files:
- ...

Numeric sanitation:
- path:
- source CSV mutated:
- train audit:
- valid audit:
- test audit:
- sanitizer reports written:

Robust multi-model:
- path:
- model families requested:
- model runs completed:
- model runs failed/skipped:
- RandomForest status:
- best model:
- trading metrics present:

Report exports:
- path:
- markdown report:
- export manifest:

Run health:
- path:
- total records:
- checked runs:
- warning count:
- error count:

Artifacts:
- sanitized baseline output:
- robust multi-model output:
- exported report output:
- run health output:

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
