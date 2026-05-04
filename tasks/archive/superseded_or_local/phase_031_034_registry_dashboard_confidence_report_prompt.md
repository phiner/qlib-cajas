# Phase 31-34 Prompt: Add Registry Cleanup, Dashboard Exports, Confidence Analysis, and Research Report Pack

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

Phase 27-30 completed with local commits only. User will push manually.

Phase 27-30 commits:

```text
b4767acb docs: add phase 27-30 sanitation and reporting prompt
8bebf336 feat: add numeric sanitation for baseline training
0235623a feat: harden multi-model baseline runs
8d414ba2 feat: add baseline markdown report exports
dbb52b12 feat: add run registry health checks
faab4384 docs: document sanitation reporting and run health workflow
```

Phase 27-30 completed:

- feature value audit
- numeric sanitizer
- robust multi-model baseline
- markdown report export
- run health checks

Validation summary:

```text
focused tests: 12 passed
full tests: 144 passed
RandomForest now completes successfully
No Qlib workflow execution
No trading/backtest/profit metrics
```

Important observed issue:

```text
Run health:
- total records: 29
- checked runs: 29
- warning count: 0
- error count: 20
```

Notes from Phase 27-30:

```text
Run-health errors are from historical temp test run paths already cleaned up (/tmp/tmp... missing directories), which is expected for this checker behavior.
```

Phase 31-34 should make these registry/health findings manageable rather than leaving them as noisy errors.

## Phase 31-34 Goal

This combined phase should improve research workflow usability after baseline training and reporting.

### Phase 31: Registry Cleanup and Health Classification

- Add tools to classify run registry records as active, stale, missing-artifact, or test-temp.
- Add safe registry cleanup/reporting workflow.
- Do not delete registry records by default.
- Optionally write a filtered clean registry copy under `tmp/`.

### Phase 32: Dashboard Data Export

- Export compact JSON/CSV files suitable for a future UI/dashboard:
  - run list
  - metrics comparison
  - feature importance summary
  - prediction review summary
  - health summary
- Keep outputs under `tmp/`.

### Phase 33: Confidence and Calibration Analysis

- Analyze prediction confidence from existing prediction artifacts.
- Compute classification-only confidence buckets:
  - confidence bucket counts
  - accuracy by confidence bucket
  - error rate by confidence bucket
  - class distribution by confidence bucket
- Do not turn confidence into trading thresholds.

### Phase 34: Research Report Pack

- Build a consolidated Markdown/JSON research report pack that references:
  - best local baseline
  - multi-model comparison
  - feature importance summary
  - prediction review
  - confidence analysis
  - registry health summary
- No trading/backtest/profit sections.

## Absolute Boundaries

Allowed in this phase:

- Reading existing local artifacts under `tmp/`.
- Writing local derived report/dashboard/confidence artifacts under `tmp/`.
- Classification-only analysis of predictions.
- Registry health classification and filtered copy generation.

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
- Working tree should be clean or only contain this Phase 31-34 prompt if already added.

## Task 2: Path Hygiene

Run:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py --json
```

Expected:

- 0 issues.

If any `caixas/` or `cajas/**/init.py` issue appears, fix it before continuing.

## Task 3: Add Registry Cleanup and Classification

Add:

```text
cajas/registry/registry_cleanup.py
```

Purpose:

- Classify registry records without deleting anything by default.
- Reduce noise from historical temporary `/tmp/tmp...` run paths.
- Produce cleanup recommendations and optional filtered registry copy under `tmp/`.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class RegistryRecordClassification:
    run_name: str
    run_id: str | None
    output_dir: str | None
    classification: str
    reason: str
    keep_by_default: bool

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class RegistryCleanupReport:
    registry_path: str
    total_records: int
    active_records: int
    stale_records: int
    missing_artifact_records: int
    temp_test_records: int
    classifications: list[RegistryRecordClassification]
    recommendations: list[str]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def classify_run_registry_records(
    *,
    registry_path: str | Path,
) -> RegistryCleanupReport:
    ...
```

Classification rules:

- `active`: output dir exists and required artifacts are present or partially present.
- `missing_artifact`: output dir expected but missing.
- `temp_test`: output dir starts with `/tmp/tmp` or another obvious pytest temp path.
- `stale`: older local artifact references that are missing but not temp.
- `unknown`: malformed or incomplete record.

Do not mutate the registry.

Optional helper:

```python
def write_filtered_registry_copy(
    *,
    registry_path: str | Path,
    output_path: str | Path,
    exclude_temp_test: bool = True,
) -> dict:
    ...
```

This writes a new filtered JSONL under `tmp/`, not in-place.

## Task 4: Add Registry Cleanup CLI

Add:

```text
cajas/scripts/classify_run_registry.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/classify_run_registry.py \
  --registry tmp/cajas/run_registry/runs.jsonl \
  --output-dir tmp/cajas/registry_cleanup \
  --run-name phase31_registry_cleanup \
  --write-artifacts
```

Optional flags:

```text
--json
--write-filtered-copy
```

Artifacts:

```text
registry_cleanup_report.json
registry_record_classifications.csv
runs_filtered.jsonl  # only if --write-filtered-copy
```

Do not modify original registry.

## Task 5: Add Dashboard Data Export Module

Add:

```text
cajas/reports/dashboard_export.py
```

Purpose:

- Build compact dashboard-ready artifacts from local reports.
- No web app required yet.
- Output JSON/CSV files under `tmp/`.

Suggested dataclass:

```python
@dataclass(frozen=True)
class DashboardExportReport:
    output_dir: str
    run_count: int
    files_written: list[str]
    warnings: list[str]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def export_dashboard_data(
    *,
    registry_path: str | Path,
    output_dir: str | Path,
    run_name: str,
    baseline_run_dirs: list[str | Path] | None = None,
) -> DashboardExportReport:
    ...
```

Expected artifacts:

```text
dashboard_manifest.json
dashboard_runs.json
dashboard_runs.csv
dashboard_metrics.csv
dashboard_feature_importance.csv
dashboard_health_summary.json
```

Rules:

- Use existing registry reports, run comparison, feature importance summary, health checks where possible.
- If inputs are missing, write warnings but keep partial export.
- Do not include raw prediction rows.
- Do not include raw data rows.
- Do not compute trading metrics.

## Task 6: Add Dashboard Export CLI

Add:

```text
cajas/scripts/export_dashboard_data.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/export_dashboard_data.py \
  --registry tmp/cajas/run_registry/runs.jsonl \
  --output-dir tmp/cajas/dashboard_exports \
  --run-name phase32_dashboard_export
```

Optional:

```text
--baseline-run-dir tmp/cajas/baseline_runs/phase20_local_baseline
--json
```

## Task 7: Add Confidence Analysis Module

Add:

```text
cajas/baseline/confidence_analysis.py
```

Purpose:

- Analyze confidence from existing prediction artifacts.
- Classification-only confidence QA.
- No trading threshold logic.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class ConfidenceBucketSummary:
    bucket: str
    row_count: int
    accuracy: float | None
    error_rate: float | None
    class_distribution: dict[str, int]

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class ConfidenceAnalysisReport:
    split: str
    total_rows: int
    probability_columns: list[str]
    buckets: list[ConfidenceBucketSummary]
    warnings: list[str]
    trading_thresholds_created: bool

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def analyze_prediction_confidence(
    *,
    prediction_csv: str | Path,
    split: str,
    bucket_edges: list[float] | None = None,
) -> ConfidenceAnalysisReport:
    ...
```

Default buckets:

```text
[0.0, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
```

Rules:

- Use max probability across `proba_*` columns as confidence.
- Compare `label` and `predicted_label` for accuracy.
- If no probability columns exist, report warning.
- Do not create trading thresholds.
- Do not recommend actions.

## Task 8: Add Confidence Analysis CLI

Add:

```text
cajas/scripts/analyze_prediction_confidence.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/analyze_prediction_confidence.py \
  --prediction-csv tmp/cajas/baseline_runs/phase20_local_baseline/predictions_test.csv \
  --split test \
  --output-dir tmp/cajas/confidence_analysis \
  --run-name phase33_confidence_analysis \
  --write-artifacts
```

Optional:

```text
--json
```

Artifacts:

```text
confidence_analysis_report.json
confidence_buckets.csv
```

## Task 9: Add Research Report Pack Module

Add:

```text
cajas/reports/research_report_pack.py
```

Purpose:

- Build a consolidated research report pack from existing artifacts.
- Use Markdown + JSON.
- No trading/backtest/profit sections.

Suggested dataclass:

```python
@dataclass(frozen=True)
class ResearchReportPack:
    output_dir: str
    title: str
    sections: list[str]
    files_written: list[str]
    warnings: list[str]
    trading_sections_present: bool

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def build_research_report_pack(
    *,
    output_dir: str | Path,
    run_name: str,
    title: str,
    registry_path: str | Path,
    baseline_run_dir: str | Path,
    include_dashboard_export: bool = True,
) -> ResearchReportPack:
    ...
```

Expected artifacts:

```text
research_report.md
research_report_pack.json
research_report_manifest.json
```

Report sections:

- Project scope
- Dataset summary
- Baseline model summary
- Classification metrics
- Multi-model comparison summary if available
- Feature importance summary
- Prediction review summary
- Confidence analysis summary
- Registry health summary
- Boundaries and forbidden interpretations

Explicitly state:

- No trading strategy.
- No backtest.
- No profit analysis.
- Predictions are classification outputs only.

## Task 10: Add Research Report Pack CLI

Add:

```text
cajas/scripts/build_research_report_pack.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_research_report_pack.py \
  --registry tmp/cajas/run_registry/runs.jsonl \
  --baseline-run-dir tmp/cajas/baseline_runs/phase20_local_baseline \
  --output-dir tmp/cajas/research_report_packs \
  --run-name phase34_research_report_pack \
  --title "EURUSD 15m Market Recognition Baseline Research"
```

Optional:

```text
--json
```

## Task 11: Extend YAML Config

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Add sections:

```yaml
registry_cleanup:
  enabled: true
  phase: phase31
  registry_path: tmp/cajas/run_registry/runs.jsonl
  output:
    default_output_dir: tmp/cajas/registry_cleanup
    default_run_name: phase31_registry_cleanup

dashboard_export:
  enabled: true
  phase: phase32
  registry_path: tmp/cajas/run_registry/runs.jsonl
  output:
    default_output_dir: tmp/cajas/dashboard_exports
    default_run_name: phase32_dashboard_export

confidence_analysis:
  enabled: true
  phase: phase33
  default_prediction_csv: tmp/cajas/baseline_runs/phase20_local_baseline/predictions_test.csv
  bucket_edges:
    - 0.0
    - 0.4
    - 0.5
    - 0.6
    - 0.7
    - 0.8
    - 0.9
    - 1.0
  output:
    default_output_dir: tmp/cajas/confidence_analysis
    default_run_name: phase33_confidence_analysis

research_report_pack:
  enabled: true
  phase: phase34
  title: EURUSD 15m Market Recognition Baseline Research
  output:
    default_output_dir: tmp/cajas/research_report_packs
    default_run_name: phase34_research_report_pack
```

Clarify:

- These are local research/reporting artifacts.
- No trading/backtest/profit analysis.

## Task 12: Add Tests

Add:

```text
cajas/tests/test_registry_cleanup.py
cajas/tests/test_dashboard_export.py
cajas/tests/test_confidence_analysis.py
cajas/tests/test_research_report_pack.py
```

Test coverage:

Registry cleanup:

- classifies active record
- classifies temp test record
- writes filtered copy without mutating original

Dashboard export:

- writes manifest/runs/metrics files
- handles missing inputs with warnings
- no raw prediction rows

Confidence analysis:

- computes confidence buckets
- computes accuracy by bucket
- handles missing proba columns
- does not create trading thresholds

Research report pack:

- writes markdown/json/manifest
- includes required sections
- no trading/profit/backtest sections except explicit forbidden-boundary note

## Task 13: Update Documentation

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should add Phase 31-34:

- registry cleanup
- dashboard data export
- confidence analysis
- research report pack
- CLI commands:
  - `classify_run_registry.py`
  - `export_dashboard_data.py`
  - `analyze_prediction_confidence.py`
  - `build_research_report_pack.py`

Integration notes should add Phase 31-34:

- Historical temp registry records are now classified rather than treated as unexplained failures.
- Dashboard export prepares data for a future UI without building a UI.
- Confidence analysis is classification QA only, not trading threshold design.
- Phase 35 recommendation:
  - add dashboard UI/static HTML from dashboard JSON; or
  - add model calibration methods for classification confidence only.

Data examples should add:

- Dashboard and research reports are derived artifacts under `tmp/`.
- Confidence buckets are QA summaries, not trading thresholds.

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
  cajas/registry/registry_cleanup.py \
  cajas/scripts/classify_run_registry.py \
  cajas/reports/dashboard_export.py \
  cajas/scripts/export_dashboard_data.py \
  cajas/baseline/confidence_analysis.py \
  cajas/scripts/analyze_prediction_confidence.py \
  cajas/reports/research_report_pack.py \
  cajas/scripts/build_research_report_pack.py
```

Run path hygiene:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_registry_cleanup.py \
  cajas/tests/test_dashboard_export.py \
  cajas/tests/test_confidence_analysis.py \
  cajas/tests/test_research_report_pack.py
```

Run full tests if reasonable:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests
```

Ensure baseline run exists:

```bash
if [ ! -d tmp/cajas/baseline_runs/phase20_local_baseline ]; then
  ./.venv-qlib313/bin/python cajas/scripts/train_local_baseline.py \
    --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
    --output-dir tmp/cajas/baseline_runs \
    --run-name phase20_local_baseline
fi
```

Run real registry cleanup:

```bash
rm -rf tmp/cajas/registry_cleanup/phase31_registry_cleanup

./.venv-qlib313/bin/python cajas/scripts/classify_run_registry.py \
  --registry tmp/cajas/run_registry/runs.jsonl \
  --output-dir tmp/cajas/registry_cleanup \
  --run-name phase31_registry_cleanup \
  --write-artifacts \
  --write-filtered-copy

find tmp/cajas/registry_cleanup/phase31_registry_cleanup -maxdepth 1 -type f -print | sort
```

Run dashboard export:

```bash
rm -rf tmp/cajas/dashboard_exports/phase32_dashboard_export

./.venv-qlib313/bin/python cajas/scripts/export_dashboard_data.py \
  --registry tmp/cajas/run_registry/runs.jsonl \
  --baseline-run-dir tmp/cajas/baseline_runs/phase20_local_baseline \
  --output-dir tmp/cajas/dashboard_exports \
  --run-name phase32_dashboard_export

find tmp/cajas/dashboard_exports/phase32_dashboard_export -maxdepth 1 -type f -print | sort
```

Run confidence analysis:

```bash
rm -rf tmp/cajas/confidence_analysis/phase33_confidence_analysis

./.venv-qlib313/bin/python cajas/scripts/analyze_prediction_confidence.py \
  --prediction-csv tmp/cajas/baseline_runs/phase20_local_baseline/predictions_test.csv \
  --split test \
  --output-dir tmp/cajas/confidence_analysis \
  --run-name phase33_confidence_analysis \
  --write-artifacts

find tmp/cajas/confidence_analysis/phase33_confidence_analysis -maxdepth 1 -type f -print | sort
```

Run research report pack:

```bash
rm -rf tmp/cajas/research_report_packs/phase34_research_report_pack

./.venv-qlib313/bin/python cajas/scripts/build_research_report_pack.py \
  --registry tmp/cajas/run_registry/runs.jsonl \
  --baseline-run-dir tmp/cajas/baseline_runs/phase20_local_baseline \
  --output-dir tmp/cajas/research_report_packs \
  --run-name phase34_research_report_pack \
  --title "EURUSD 15m Market Recognition Baseline Research"

find tmp/cajas/research_report_packs/phase34_research_report_pack -maxdepth 1 -type f -print | sort
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

### Commit 1: Phase 31-34 prompt

```bash
git add tasks/phase_031_034_registry_dashboard_confidence_report_prompt.md
git commit -m "docs: add phase 31-34 reporting workflow prompt"
```

### Commit 2: registry cleanup

```bash
git add cajas/registry/registry_cleanup.py \
  cajas/scripts/classify_run_registry.py \
  cajas/tests/test_registry_cleanup.py \
  cajas/registry/__init__.py
git commit -m "feat: add registry cleanup classification"
```

### Commit 3: dashboard export

```bash
git add cajas/reports/dashboard_export.py \
  cajas/scripts/export_dashboard_data.py \
  cajas/tests/test_dashboard_export.py \
  cajas/reports/__init__.py
git commit -m "feat: add dashboard data export"
```

### Commit 4: confidence analysis

```bash
git add cajas/baseline/confidence_analysis.py \
  cajas/scripts/analyze_prediction_confidence.py \
  cajas/tests/test_confidence_analysis.py \
  cajas/baseline/__init__.py
git commit -m "feat: add prediction confidence analysis"
```

### Commit 5: research report pack

```bash
git add cajas/reports/research_report_pack.py \
  cajas/scripts/build_research_report_pack.py \
  cajas/tests/test_research_report_pack.py \
  cajas/reports/__init__.py
git commit -m "feat: add research report pack"
```

### Commit 6: docs/config

```bash
git add cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  cajas/README.md \
  cajas/docs/qlib_integration_notes.md \
  cajas/data_examples/README.md
git commit -m "docs: document registry dashboard confidence reporting"
```

Do not run `git push`.

Report manual push command:

```bash
git push origin cajas/market-recognition-phase-0
```

## Completion Report Format

Report exactly in English:

```text
Phase 31-34 completed.

Branch:
- cajas/market-recognition-phase-0

Changed files:
- ...

Registry cleanup:
- path:
- total records:
- active:
- temp test:
- stale/missing:
- filtered copy written:

Dashboard export:
- path:
- files written:
- raw rows included:

Confidence analysis:
- path:
- split:
- total rows:
- buckets:
- trading thresholds created:

Research report pack:
- path:
- sections:
- markdown report:
- trading/profit/backtest sections present:

Artifacts:
- registry cleanup output:
- dashboard output:
- confidence output:
- research report output:

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
