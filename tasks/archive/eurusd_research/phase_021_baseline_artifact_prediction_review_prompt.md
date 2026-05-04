# Phase 21 Prompt: Add Baseline Model Artifact Inspection and Prediction Review Reports

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

Phase 19-20 completed with local commits only. User will push manually.

Phase 19-20 commits:

```text
cf897fc6 docs: add phase 19-20 local baseline training prompt
26f1447d feat: add local run registry
bdc21f9f feat: add controlled local baseline training
8abf2451 docs: document controlled local baseline training
```

Phase 19-20 added:

- `cajas/registry/run_registry.py`
- `cajas/baseline/classification_metrics.py`
- `cajas/baseline/local_baseline_trainer.py`
- `cajas/scripts/train_local_baseline.py`
- local baseline training tests
- docs/config updates

Phase 19-20 real-data baseline summary:

```text
model family requested: LightGBM
model family used: LightGBM
target label: future_direction_8
feature count: 24
train rows: 16512
valid rows: 4225
test rows: 3985
training executed: true
model artifact created: true
prediction artifacts created: true
metrics artifacts created: true
qlib workflow executed: false
trading/backtest/profit outputs: false

valid:
  accuracy: 0.5211834319526627
  macro_f1: 0.3475899458728962
  weighted_f1: 0.5180940457627833

test:
  accuracy: 0.5091593475533249
  macro_f1: 0.3389880322468605
  weighted_f1: 0.50728716148322
```

Baseline artifacts were generated under:

```text
tmp/cajas/baseline_runs/phase20_local_baseline/
```

Registry:

```text
tmp/cajas/run_registry/runs.jsonl
```

These outputs are local and must not be committed.

## Phase 21 Goal

Phase 21 should add post-training inspection and review tooling for the local baseline model artifacts.

Main objectives:

1. Inspect baseline run artifacts without retraining.
2. Summarize model metadata, features, labels, metrics, and prediction artifacts.
3. Build prediction review reports:
   - low-confidence samples
   - high-confidence errors
   - per-class error summary
   - confusion matrix summary
4. Add a CLI that reads an existing baseline run directory and writes inspection/review artifacts under `tmp/`.
5. Add tests/docs/config updates.
6. Keep all trading/backtest/profit logic forbidden.

This phase should not train a model by default.

This phase should not execute Qlib workflow.

This phase should not modify Qlib core.

This phase should not add trading, backtesting, profit analysis, live execution, automatic ordering, or position sizing.

## Absolute Boundaries

Allowed in this phase:

- Reading existing local baseline artifacts under `tmp/`.
- Computing classification-only review summaries from existing prediction CSVs.
- Writing local inspection/review artifacts under `tmp/`.
- Running a smoke test that first creates a baseline run if needed, then inspects it.

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
12. Do not initialize Qlib.
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
- Working tree should be clean or only contain this Phase 21 prompt if already added.

## Task 2: Path Hygiene

Run:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py --json
```

Expected:

- 0 issues.

If any `caixas/` or `cajas/**/init.py` issue appears, fix it before continuing.

## Task 3: Add Baseline Artifact Inspector

Add:

```text
cajas/baseline/baseline_artifact_inspector.py
```

Purpose:

- Inspect an existing local baseline run directory.
- Validate required artifact files.
- Load JSON/CSV summaries.
- Produce a structured inspection report.
- Do not train.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class BaselineArtifactIssue:
    severity: str
    code: str
    message: str
    file: str | None = None

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class BaselineArtifactInspectionReport:
    run_dir: str
    run_name: str
    required_files_present: bool
    artifact_files: list[str]
    model_family_used: str | None
    target_label: str | None
    feature_count: int | None
    train_rows: int | None
    valid_rows: int | None
    test_rows: int | None
    metrics_valid: dict
    metrics_test: dict
    issues: list[BaselineArtifactIssue]
    warnings: list[str]
    training_executed: bool | None
    qlib_workflow_executed: bool

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def inspect_baseline_run_artifacts(run_dir: str | Path) -> BaselineArtifactInspectionReport:
    ...
```

Required files:

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
model.joblib
```

Rules:

- Missing required files should be issues.
- Do not load the model object unless explicitly needed. Prefer metadata inspection only.
- Do not call predict/evaluate.
- Do not compute trading metrics.

## Task 4: Add Prediction Review Module

Add:

```text
cajas/baseline/prediction_review.py
```

Purpose:

- Read baseline prediction CSVs.
- Build classification-only review outputs.
- Identify samples useful for human review.
- Do not treat predictions as trading signals.

Suggested dataclasses:

```python
@dataclass(frozen=True)
class PredictionReviewReport:
    split: str
    total_rows: int
    correct_rows: int
    error_rows: int
    accuracy: float
    low_confidence_count: int
    high_confidence_error_count: int
    per_class_errors: dict[str, int]
    output_files: dict[str, str]
    warnings: list[str]

    def to_dict(self) -> dict: ...
```

Suggested function:

```python
def build_prediction_review(
    *,
    prediction_csv: str | Path,
    output_dir: str | Path,
    split: str,
    low_confidence_threshold: float = 0.45,
    high_confidence_error_threshold: float = 0.70,
) -> PredictionReviewReport:
    ...
```

Behavior:

- Read `predictions_valid.csv` or `predictions_test.csv`.
- Determine correctness by comparing:
  - `label`
  - `predicted_label`
- If probability columns exist:
  - compute max probability as confidence.
  - low confidence samples: `max_proba <= low_confidence_threshold`
  - high confidence errors: wrong prediction and `max_proba >= high_confidence_error_threshold`
- If probability columns do not exist, create empty low/high confidence outputs with warnings.
- Write:
  - `<split>_low_confidence_samples.csv`
  - `<split>_high_confidence_errors.csv`
  - `<split>_error_summary_by_class.csv`
  - `<split>_prediction_review_report.json`
- Do not create trading signals.

Expected columns in review outputs should retain:

```text
datetime
symbol
timeframe
label
encoded_label
predicted_label
predicted_encoded_label
```

plus confidence/probability columns if present.

## Task 5: Add Baseline Run Inspection CLI

Add:

```text
cajas/scripts/inspect_baseline_run.py
```

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/inspect_baseline_run.py \
  --run-dir tmp/cajas/baseline_runs/phase20_local_baseline
```

Optional flags:

```text
--json
--write-review-artifacts
--output-dir tmp/cajas/baseline_reviews
--run-name phase21_baseline_review
--low-confidence-threshold 0.45
--high-confidence-error-threshold 0.70
```

Behavior:

- Text mode prints:
  - run dir
  - model family used
  - target label
  - feature count
  - valid/test metrics
  - required files present yes/no
  - review artifact status if requested
  - explicit note: no trading/backtest/profit analysis performed
- JSON mode prints report dict.
- If `--write-review-artifacts`:
  - inspect artifacts
  - build prediction reviews for valid and test
  - write:
    - `baseline_artifact_inspection_report.json`
    - `valid_prediction_review_report.json`
    - `test_prediction_review_report.json`
    - review CSVs
- Refuse overwrite of existing output directory.
- Do not train.

## Task 6: Add Baseline Run Summary Report

Add if useful:

```text
cajas/baseline/baseline_run_summary.py
```

Purpose:

- Combine artifact inspection + valid/test prediction review into one summary report.

Suggested function:

```python
def build_baseline_run_summary(
    *,
    run_dir: str | Path,
    output_dir: str | Path | None = None,
    write_artifacts: bool = False,
) -> dict:
    ...
```

Keep it small. If redundant, keep logic inside CLI.

## Task 7: Extend YAML Config

Update:

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

Add or update:

```yaml
baseline_artifact_review:
  enabled: true
  phase: phase21
  default_run_dir: tmp/cajas/baseline_runs/phase20_local_baseline
  low_confidence_threshold: 0.45
  high_confidence_error_threshold: 0.70
  output:
    default_output_dir: tmp/cajas/baseline_reviews
    default_run_name: phase21_baseline_review
  artifacts:
    generated_files:
      - baseline_artifact_inspection_report.json
      - valid_prediction_review_report.json
      - test_prediction_review_report.json
      - valid_low_confidence_samples.csv
      - valid_high_confidence_errors.csv
      - valid_error_summary_by_class.csv
      - test_low_confidence_samples.csv
      - test_high_confidence_errors.csv
      - test_error_summary_by_class.csv
  forbidden_outputs:
    - trading_signals
    - backtest_results
    - profit_metrics
    - order_recommendations
```

Clarify:

- Review outputs are classification inspection artifacts only.
- They are not trading signals.

## Task 8: Add Tests

Add:

```text
cajas/tests/test_baseline_artifact_inspector.py
cajas/tests/test_prediction_review.py
```

If adding summary module:

```text
cajas/tests/test_baseline_run_summary.py
```

Tests should use temporary run directories and tiny CSV/JSON fixtures.

Artifact inspector tests:

- complete run directory passes
- missing required file produces issue
- report serializes
- does not load model object

Prediction review tests:

- computes correctness
- low confidence samples output
- high confidence errors output
- per-class error summary output
- handles missing probability columns with warning
- no trading metric keys present

CLI tests may be function-level if easier.

## Task 9: Update Documentation

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
cajas/data_examples/README.md
```

README should add Phase 21:

- Baseline artifact inspector added.
- Prediction review reports added.
- CLI command:
  - `inspect_baseline_run.py`
- Review artifacts under `tmp/`.
- Classification-only review.
- No trading/backtest/profit analysis.

Integration notes should add Phase 21:

- Phase 20 created the first local baseline training.
- Phase 21 inspects and reviews prediction artifacts.
- Prediction review is for human/data QA, not trading.
- Phase 22 recommendation:
  - add baseline comparison across multiple runs; or
  - add feature importance inspection if supported by the model artifact.

Data examples should add:

- Prediction review files are derived local artifacts under `tmp/`.
- They should not be committed.
- Prediction labels are market-recognition classes, not actions.

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
  cajas/baseline/baseline_artifact_inspector.py \
  cajas/baseline/prediction_review.py \
  cajas/scripts/inspect_baseline_run.py
```

If added:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/baseline/baseline_run_summary.py
```

Run path hygiene:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Run unit tests:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_baseline_artifact_inspector.py \
  cajas/tests/test_prediction_review.py
```

If added:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_baseline_run_summary.py
```

Run full test suite if reasonable:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests
```

Ensure a real baseline run exists. If not, create it:

```bash
rm -rf tmp/cajas/baseline_runs/phase20_local_baseline

./.venv-qlib313/bin/python cajas/scripts/train_local_baseline.py \
  --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  --output-dir tmp/cajas/baseline_runs \
  --run-name phase20_local_baseline
```

Run real artifact inspection:

```bash
./.venv-qlib313/bin/python cajas/scripts/inspect_baseline_run.py \
  --run-dir tmp/cajas/baseline_runs/phase20_local_baseline

./.venv-qlib313/bin/python cajas/scripts/inspect_baseline_run.py \
  --run-dir tmp/cajas/baseline_runs/phase20_local_baseline \
  --json
```

Run real review artifact generation:

```bash
rm -rf tmp/cajas/baseline_reviews/phase21_baseline_review

./.venv-qlib313/bin/python cajas/scripts/inspect_baseline_run.py \
  --run-dir tmp/cajas/baseline_runs/phase20_local_baseline \
  --write-review-artifacts \
  --output-dir tmp/cajas/baseline_reviews \
  --run-name phase21_baseline_review

find tmp/cajas/baseline_reviews/phase21_baseline_review -maxdepth 1 -type f -print | sort
```

Confirm:

- no Qlib workflow executed
- no trading/backtest/profit output exists
- `tmp/` artifacts are not staged

Run:

```bash
git diff --check
git diff --stat
git status --short
```

## Suggested Commits

Prefer focused commits.

### Commit 1: Phase 21 prompt

```bash
git add tasks/phase_021_baseline_artifact_prediction_review_prompt.md
git commit -m "docs: add phase 21 baseline review prompt"
```

### Commit 2: artifact inspection and prediction review

```bash
git add cajas/baseline/baseline_artifact_inspector.py \
  cajas/baseline/prediction_review.py \
  cajas/scripts/inspect_baseline_run.py \
  cajas/tests/test_baseline_artifact_inspector.py \
  cajas/tests/test_prediction_review.py \
  cajas/baseline/__init__.py
```

If summary module added:

```bash
git add cajas/baseline/baseline_run_summary.py cajas/tests/test_baseline_run_summary.py
```

Then:

```bash
git commit -m "feat: add baseline artifact and prediction review"
```

### Commit 3: docs/config

```bash
git add cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml \
  cajas/README.md \
  cajas/docs/qlib_integration_notes.md \
  cajas/data_examples/README.md
git commit -m "docs: document baseline prediction review"
```

Do not run `git push`.

Report manual push command:

```bash
git push origin cajas/market-recognition-phase-0
```

## Completion Report Format

Report exactly in English:

```text
Phase 21 completed.

Branch:
- cajas/market-recognition-phase-0

Changed files:
- ...

Artifact inspection:
- path:
- required files present:
- model family:
- target label:
- feature count:
- valid metrics:
- test metrics:

Prediction review:
- path:
- valid low confidence count:
- valid high confidence error count:
- test low confidence count:
- test high confidence error count:
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
- Train new model unless needed only to create a missing smoke-test baseline run.
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
