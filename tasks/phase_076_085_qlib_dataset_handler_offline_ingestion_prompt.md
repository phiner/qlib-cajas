# Phase 76–85 — Qlib Dataset/Handler Adapter + Offline Ingestion Smoke

You are working in the `cajas/market-recognition-phase-0` branch.

## Context

Phases 41–55 added label variants, feature-set comparison, calibration, seed stability, rolling-year planning, error slice analysis, leakage/drift audit, Qlib readiness reports, and roadmap reports.

Phases 56–65 added the research decision layer:

- research decision schema/builder
- research decision packet CLI
- candidate promotion manifest CLI
- research report index CLI
- research packet smoke runner

Phases 66–75 added the conservative Qlib handoff layer:

- Qlib adapter contract schema/builder
- Qlib dry-run integration packet
- Qlib compatibility report
- Qlib adapter smoke runner

Current status:

- full test suite passing
- path hygiene clean
- no `init.py` typos
- no Qlib core changes
- no broker/live trading logic
- no model training yet

## Goal

Implement Phase 76–85: a conservative offline Qlib Dataset/Handler ingestion layer.

This phase should make it possible to take the existing cajas feature/label artifacts and generate a Qlib-style offline dataset/handler package that can be inspected, validated, and smoke-tested without training any model.

The purpose is to verify that promoted research outputs can be shaped into a stable Qlib-compatible data interface before Phase 86–95 introduces actual model/experiment training.

## Hard Scope Boundaries

Do **not**:

- modify Qlib core
- import or depend on Qlib internals unless already safely available
- start model training
- add LightGBM training
- add experiment recorder logic
- add trading strategy logic
- add broker/live/paper-trading execution
- change existing label semantics
- change existing feature semantics
- rewrite existing Phase 41–75 workflows
- introduce GPU/CUDA requirements

All work must be CPU-only and offline.

## Desired Additions

### 1. Qlib dataset/handler contract module

Add a module such as:

- `cajas/reports/qlib_dataset_contract.py`
- `cajas/reports/qlib_dataset_contract_builder.py`

The contract should summarize the offline dataset shape expected by a future Qlib Dataset/Handler.

Recommended fields:

- `schema_version`
- `dataset_id`
- `created_at_utc`
- `source_contract_path`
- `source_integration_packet_path`
- `instrument_col`
- `datetime_col`
- `feature_columns`
- `label_columns`
- `required_columns`
- `optional_columns`
- `split_columns` or split metadata
- `time_range`
- `instrument_count`
- `row_count`
- `null_summary`
- `dtype_summary`
- `numeric_feature_count`
- `non_numeric_feature_columns`
- `label_distribution_summary`
- `warnings`
- `blocking_issues`
- `readiness_status`

Use a conservative readiness status, for example:

- `ready_for_handler_smoke`
- `ready_with_warnings`
- `blocked`

### 2. Offline handler input builder

Add a module such as:

- `cajas/reports/qlib_handler_input_builder.py`

This should take an existing feature/label CSV-like artifact and produce a normalized offline handler input directory.

Suggested output files:

```text
<out_dir>/handler_input.csv
<out_dir>/handler_input_manifest.json
<out_dir>/columns.json
<out_dir>/splits.json
<out_dir>/warnings.jsonl
```

Keep the implementation plain Python/pandas-compatible if pandas is already used in the project. Do not introduce heavyweight dependencies.

The builder should:

- preserve source rows
- normalize required column ordering
- identify feature and label columns
- preserve instrument/time columns
- optionally sort by instrument/time
- report missing required columns
- report non-numeric feature columns
- report null-heavy columns
- report duplicate instrument/time rows
- never silently drop rows unless explicitly requested by an existing contract

### 3. Handler smoke validator

Add a module such as:

- `cajas/reports/qlib_handler_smoke_validator.py`

The validator should read the generated handler input package and confirm:

- manifest exists
- handler input CSV exists
- required columns exist
- feature columns exist
- label columns exist
- datetime column parses
- instrument column is non-empty
- feature columns are numeric or explicitly reported
- labels have non-empty distribution
- train/valid/test split metadata is present or explicitly marked unavailable
- no obviously impossible time ranges

Output a JSON report with:

- `schema_version`
- `status`
- `checked_paths`
- `row_count`
- `feature_count`
- `label_count`
- `warnings`
- `blocking_issues`
- `next_phase_recommendation`

Recommended statuses:

- `pass`
- `pass_with_warnings`
- `fail`

### 4. CLI scripts

Add CLIs similar to the existing script style:

- `cajas/scripts/build_qlib_dataset_contract.py`
- `cajas/scripts/build_qlib_handler_input.py`
- `cajas/scripts/validate_qlib_handler_input.py`
- `cajas/scripts/run_qlib_dataset_handler_smoke.py`

The smoke runner should generate a small deterministic fixture or use existing lightweight example data, then run:

1. dataset contract build
2. handler input build
3. handler input validation
4. summary output

Suggested smoke output root:

```text
tmp/qlib-dataset-handler-smoke
```

Suggested generated paths:

```text
tmp/qlib-dataset-handler-smoke/dataset_contract/qlib_dataset_contract.json
tmp/qlib-dataset-handler-smoke/handler_input/handler_input.csv
tmp/qlib-dataset-handler-smoke/handler_input/handler_input_manifest.json
tmp/qlib-dataset-handler-smoke/validation/qlib_handler_smoke_report.json
```

### 5. Tests

Add focused tests for each new module and CLI.

Suggested tests:

- dataset contract schema creation
- dataset contract builder on tiny deterministic fixture
- handler input builder preserves rows and required columns
- handler input builder reports missing required columns
- handler input builder reports non-numeric features
- handler smoke validator pass case
- handler smoke validator fail case
- CLI tests for all new scripts
- end-to-end smoke runner test

Keep tests deterministic and lightweight.

### 6. Exports

Update:

- `cajas/reports/__init__.py`

Only export stable public helpers if that is consistent with the existing style.

### 7. Documentation

Update:

- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`

Add a short section for:

```text
Qlib Dataset/Handler Offline Ingestion Workflow
```

Explain:

- this phase does not train models
- this phase only validates offline dataset/handler readiness
- how to run the smoke command
- how to interpret warnings vs blocking issues
- Phase 86–95 will add model/experiment bridge after this layer is stable

## Validation Commands

Run these before committing:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python -m pytest cajas/tests
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/run_qlib_dataset_handler_smoke.py --out-root tmp/qlib-dataset-handler-smoke
```

If `.venv-qlib313` is not available, use the repository’s current Python environment, but report the exact commands used.

## Commit Guidance

Create local commits only. Do not push.

Suggested split:

1. dataset contract + tests
2. handler input builder/validator + tests
3. smoke runner + docs

Final report should include:

- files changed
- validation results
- smoke output paths
- local commit hashes
- final `git status --short`
- manual push command:

```bash
git push origin cajas/market-recognition-phase-0
```

## Expected Final State

At the end of this phase:

- Phase 76–85 code is implemented
- all tests pass
- handler smoke passes
- git status is clean
- local commits exist
- no model training has been introduced
- the project is ready for Phase 86–95 model/experiment bridge
