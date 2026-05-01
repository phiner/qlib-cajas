# Resume Phase 41–55: Final Smoke, Commit Split, and Push Instructions

You are continuing work on branch:

- `cajas/market-recognition-phase-0`

The previous implementation pass already completed Phase 41–45 and Phase 46–55 code, tests, docs, configs, and prompt files. The only known blocker was the environment usage limiter, which prevented final runtime-heavy smoke commands and all git commit actions.

## Current known completed work

Phase 41–45 modules were added:

- `cajas/datasets/threshold_label_generator.py`
- `cajas/datasets/label_variant_dataset.py`
- `cajas/baseline/label_variant_trainer.py`
- `cajas/reports/label_variant_comparison.py`
- `cajas/reports/label_decision_report.py`

Phase 41–45 CLIs were added:

- `cajas/scripts/generate_threshold_labels.py`
- `cajas/scripts/train_label_variant_holdout.py`
- `cajas/scripts/compare_label_variants.py`
- `cajas/scripts/build_label_decision_report.py`

Phase 46–55 modules were added:

- `cajas/features/__init__.py`
- `cajas/features/kline_structure_features.py`
- `cajas/features/feature_set_registry.py`
- `cajas/baseline/feature_set_comparison.py`
- `cajas/baseline/calibration_analysis.py`
- `cajas/baseline/seed_stability.py`
- `cajas/validation/__init__.py`
- `cajas/validation/rolling_year_plan.py`
- `cajas/baseline/error_slice_analysis.py`
- `cajas/audits/__init__.py`
- `cajas/audits/leakage_drift_audit.py`
- `cajas/reports/qlib_readiness_report.py`
- `cajas/reports/research_roadmap_report.py`

Phase 46–55 CLIs were added:

- `cajas/scripts/build_kline_features.py`
- `cajas/scripts/compare_feature_sets.py`
- `cajas/scripts/analyze_calibration.py`
- `cajas/scripts/run_seed_stability.py`
- `cajas/scripts/build_rolling_year_validation_plan.py`
- `cajas/scripts/analyze_error_slices.py`
- `cajas/scripts/audit_leakage_and_drift.py`
- `cajas/scripts/build_qlib_readiness_report.py`
- `cajas/scripts/build_research_roadmap_report.py`

Updated exports:

- `cajas/datasets/__init__.py`
- `cajas/baseline/__init__.py`
- `cajas/reports/__init__.py`

Updated config/docs:

- `cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml`
- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`
- `cajas/data_examples/README.md`

Added prompt files:

- `tasks/phase_041_045_label_redesign_horizon_holdout_prompt.md`
- `tasks/phase_046_055_research_quality_and_qlib_readiness_prompt.md`

Already validated before the limiter:

- `py_compile` for all new modules/scripts: pass
- Focused new tests: 15 passed
- Full suite: 174 passed
- Path hygiene: pass, `issues: 0`
- `find cajas -path "*/init.py" -print`: no output
- Threshold label generation for train and holdout full datasets completed

## Goal of this continuation

Do **not** introduce new features.

Only finish the interrupted Phase 41–55 closure:

1. Inspect current git state.
2. Re-run lightweight validations.
3. Run remaining smoke commands that were blocked by the limiter.
4. Commit the finished work in clean local commits.
5. Report commit hashes and the final manual push command.

## Hard constraints

- Stay on branch `cajas/market-recognition-phase-0`.
- Do not rename packages.
- Do not create incorrect `init.py` files; Python package files must be `__init__.py`.
- Do not remove existing functionality.
- Do not add trading strategy logic.
- Do not add live trading behavior.
- Do not perform Qlib integration beyond readiness/reporting scaffolding already implemented.
- Do not run excessive long loops. Use small smoke datasets or bounded sample sizes where the CLI supports it.
- If runtime-heavy commands are still blocked by the environment limiter, stop and report exactly which commands remain.

## Step 1 — Inspect state

Run:

```bash
git branch --show-current
git status --short
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Expected:

- Branch is `cajas/market-recognition-phase-0`
- No incorrect `init.py`
- Path hygiene passes

If path hygiene fails, fix only path/import hygiene issues.

## Step 2 — Re-run compile and tests

Run:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python -m pytest cajas/tests
```

Expected:

- Compile passes
- Full test suite passes

If a test fails due to the known YAML issue, inspect:

```bash
./.venv-qlib313/bin/python - <<'PY'
from pathlib import Path
import yaml
path = Path("cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml")
print(yaml.safe_load(path.read_text()))
PY
```

Ensure the YAML is valid and does not contain a stray list item under `research_decision_report.output`.

## Step 3 — Finish remaining smoke commands

First inspect the two prompt files and README for exact intended commands:

```bash
sed -n '1,240p' tasks/phase_041_045_label_redesign_horizon_holdout_prompt.md
sed -n '1,280p' tasks/phase_046_055_research_quality_and_qlib_readiness_prompt.md
grep -R "train_label_variant_holdout\|compare_feature_sets\|run_seed_stability\|build_qlib_readiness_report\|build_research_roadmap_report" -n cajas/README.md tasks cajas/docs | head -80
```

Then run the remaining smoke commands using the smallest valid bounded inputs available in the repository.

At minimum, complete smoke coverage for:

### Phase 41–45

- label variant holdout training
- label variant comparison
- label decision report

Candidate command pattern:

```bash
./.venv-qlib313/bin/python cajas/scripts/train_label_variant_holdout.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/compare_label_variants.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/build_label_decision_report.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

If these CLIs require explicit input/output paths, inspect `--help` and use the documented paths from the config/prompt files.

### Phase 46–55

- kline feature build
- feature set comparison
- calibration analysis
- seed stability with a bounded/small seed set if supported
- rolling-year validation plan generation
- error slice analysis
- leakage/drift audit
- Qlib readiness report
- research roadmap report

Candidate command pattern:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_kline_features.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/compare_feature_sets.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/analyze_calibration.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/run_seed_stability.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/build_rolling_year_validation_plan.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/analyze_error_slices.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/audit_leakage_and_drift.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/build_qlib_readiness_report.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

./.venv-qlib313/bin/python cajas/scripts/build_research_roadmap_report.py   --config cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

If exact flags differ, use each script's `--help` and run the equivalent minimal smoke.

Important: capture the final list of commands that passed.

## Step 4 — Re-run final validation after smoke

Run:

```bash
git status --short
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
./.venv-qlib313/bin/python -m pytest cajas/tests
```

If smoke commands generated temporary outputs under ignored directories, do not commit them.

If smoke commands generated intended tracked docs/reports, inspect them before committing.

## Step 5 — Create local commits

Use clean commit splits. Suggested order:

### Commit 1 — Prompt files

```bash
git add tasks/phase_041_045_label_redesign_horizon_holdout_prompt.md         tasks/phase_046_055_research_quality_and_qlib_readiness_prompt.md

git commit -m "Add phase 41-55 research pipeline prompts"
```

### Commit 2 — Phase 41–45 label redesign and holdout workflow

Include:

- threshold label generator
- label variant dataset/trainer
- label variant comparison report
- label decision report
- Phase 41–45 CLIs
- related tests if present

Example:

```bash
git add cajas/datasets/threshold_label_generator.py         cajas/datasets/label_variant_dataset.py         cajas/baseline/label_variant_trainer.py         cajas/reports/label_variant_comparison.py         cajas/reports/label_decision_report.py         cajas/scripts/generate_threshold_labels.py         cajas/scripts/train_label_variant_holdout.py         cajas/scripts/compare_label_variants.py         cajas/scripts/build_label_decision_report.py         cajas/datasets/__init__.py         cajas/baseline/__init__.py         cajas/reports/__init__.py         cajas/tests

git commit -m "Add label variant holdout research workflow"
```

Adjust file list based on actual `git status --short`.

### Commit 3 — Phase 46–55 research quality and readiness workflow

Include:

- kline structure features
- feature set registry/comparison
- calibration analysis
- seed stability
- rolling-year validation plan
- error slice analysis
- leakage/drift audit
- Qlib readiness report
- research roadmap report
- Phase 46–55 CLIs
- related tests if present

Example:

```bash
git add cajas/features         cajas/validation         cajas/audits         cajas/baseline/feature_set_comparison.py         cajas/baseline/calibration_analysis.py         cajas/baseline/seed_stability.py         cajas/baseline/error_slice_analysis.py         cajas/reports/qlib_readiness_report.py         cajas/reports/research_roadmap_report.py         cajas/scripts/build_kline_features.py         cajas/scripts/compare_feature_sets.py         cajas/scripts/analyze_calibration.py         cajas/scripts/run_seed_stability.py         cajas/scripts/build_rolling_year_validation_plan.py         cajas/scripts/analyze_error_slices.py         cajas/scripts/audit_leakage_and_drift.py         cajas/scripts/build_qlib_readiness_report.py         cajas/scripts/build_research_roadmap_report.py         cajas/baseline/__init__.py         cajas/reports/__init__.py         cajas/tests

git commit -m "Add research quality and Qlib readiness workflow"
```

Adjust file list based on actual `git status --short`.

### Commit 4 — Docs and config updates

Include:

- config YAML
- README
- Qlib integration notes
- data examples docs
- any related documentation updates

Example:

```bash
git add cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml         cajas/README.md         cajas/docs/qlib_integration_notes.md         cajas/data_examples/README.md

git commit -m "Document phase 41-55 research workflows"
```

If a file was already committed in an earlier split, do not add it again.

## Step 6 — Final report

After commits, run:

```bash
git status --short
git log --oneline -5
```

Final response must include:

1. Branch name
2. Smoke commands that passed
3. Full test result
4. Path hygiene result
5. Commit hashes and messages
6. Any commands skipped because of environment limiter, if any
7. Final manual push command:

```bash
git push origin cajas/market-recognition-phase-0
```

## Completion criteria

This continuation is complete only when:

- remaining smoke commands are run or explicitly reported blocked
- full tests pass
- path hygiene passes
- commits are created locally
- commit hashes are reported
- final manual push command is provided
