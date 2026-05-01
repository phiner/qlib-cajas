# Phase 086–095 — Qlib Model / Experiment Bridge + Metrics / Artifact Registry

## Context

You are working in the `cajas/market-recognition-phase-0` branch.

Recent completed phases:

- Phase 56–65 added a research decision layer:
  - decision schema/builder
  - research decision packet CLI
  - candidate promotion manifest CLI
  - research report index CLI
  - research packet smoke runner
- Phase 66–75 added a conservative Qlib handoff layer:
  - Qlib adapter contract schema/builder
  - dry-run integration packet
  - compatibility report
  - adapter smoke runner
- Phase 76–85 added a conservative offline dataset/handler ingestion layer:
  - Qlib dataset contract
  - handler input builder
  - handler smoke validator
  - dataset/handler smoke runner

Current status from prior handoff:

- Full tests passed: `201 passed`
- Path hygiene passed
- `find cajas -path "*/init.py" -print` produced no output
- Git status was clean
- No Qlib core changes
- No model training yet
- No trading/broker/live execution logic

This phase is the first controlled model-training bridge phase.

## Phase Goal

Implement a conservative, CPU-first Qlib-style model / experiment bridge that can train a baseline model from the offline handler input artifacts created in Phase 76–85, write reproducible experiment artifacts, evaluate metrics, and register the run for research comparison.

This phase may train a lightweight baseline model, but it must remain research-only.

## Hard Scope Boundaries

Do **not**:

- Modify Qlib core code.
- Add broker, live trading, paper trading, order submission, or execution logic.
- Add GPU/CUDA requirements.
- Require LightGBM GPU.
- Add deep learning models.
- Optimize for trading PnL.
- Promote any model automatically to production.
- Change existing label semantics.
- Rewrite prior report formats unless needed for backward-compatible extension.
- Add heavyweight runtime assumptions that make CI or smoke tests slow.

Do:

- Use CPU by default.
- Keep training bounded and deterministic.
- Prefer lightweight sklearn-compatible baseline if LightGBM is unavailable.
- If LightGBM is already available in the environment, it may be used optionally behind a safe fallback.
- Keep all model outputs as research artifacts.
- Add tests around schema, metrics, artifact manifests, and CLI behavior.

## Expected Design

Add a controlled model bridge with these conceptual parts:

1. **Model training input contract**
   - Reads Phase 76–85 handler input package:
     - `handler_input.csv`
     - `handler_input_manifest.json`
     - `qlib_dataset_contract.json`
     - `qlib_handler_smoke_report.json`
   - Validates:
     - required timestamp / symbol columns
     - selected label column exists
     - feature columns exist and are numeric
     - train/valid/test split can be constructed
     - no obvious leakage columns are selected as features
     - row counts are non-zero

2. **Baseline trainer**
   - CPU-only.
   - Deterministic seed.
   - Bounded data option for smoke tests.
   - Should support at least one simple classification target.
   - Suggested target default:
     - `label`
     - or the generated future direction label column from the current handler input contract, whichever exists in the current codebase.
   - Suggested baseline:
     - `sklearn.ensemble.RandomForestClassifier` or `HistGradientBoostingClassifier`
     - or a small LightGBM classifier only if dependency is already present.
   - Must gracefully fail with a clear message if dependencies or data are invalid.

3. **Experiment artifact writer**
   - Writes a stable run directory such as:
     - `tmp/qlib-model-bridge-smoke/experiment/`
   - Required artifacts:
     - `experiment_manifest.json`
     - `train_config.json`
     - `metrics.json`
     - `predictions.csv`
     - `feature_columns.json`
     - `label_distribution.json`
     - `split_summary.json`
     - `model_card.json`
   - Optional artifact:
     - serialized model file if dependency support is clean and low-risk.

4. **Metrics layer**
   - At minimum:
     - accuracy
     - macro F1 if sklearn metrics are available
     - row counts by split
     - label distribution by split
     - prediction distribution by split
   - Must avoid PnL / trading metrics.

5. **Artifact registry**
   - Add a research-only run registry writer.
   - It should append or create a JSON/JSONL registry of model bridge runs.
   - Registry record should include:
     - run id
     - timestamp
     - source handler input manifest path
     - dataset contract path
     - selected label column
     - feature count
     - row counts
     - metrics summary
     - artifact paths
     - status
     - warnings

6. **Comparison report**
   - Add a simple run comparison report that can compare one or more model bridge run directories or registry records.
   - It should rank only by research metrics such as validation macro F1 / accuracy.
   - It must explicitly state that ranking is research-only and not a trading decision.

7. **End-to-end smoke runner**
   - Add a bounded smoke command that:
     - creates or reuses minimal input artifacts from Phase 76–85 smoke style
     - builds/validates handler input if needed
     - trains the bounded CPU baseline
     - writes experiment artifacts
     - registers the run
     - builds a comparison report
   - Suggested command:
     - `cajas/scripts/run_qlib_model_bridge_smoke.py --out-root tmp/qlib-model-bridge-smoke`
   - Runtime must remain bounded.

## Suggested Files to Add

You may adjust names if the current codebase suggests better names, but keep them conservative and clear.

### Model bridge / reports

- `cajas/reports/qlib_model_training_contract.py`
- `cajas/reports/qlib_model_training_contract_builder.py`
- `cajas/reports/qlib_experiment_artifacts.py`
- `cajas/reports/qlib_model_metrics.py`
- `cajas/reports/qlib_model_run_registry.py`
- `cajas/reports/qlib_model_run_comparison.py`

### Baseline

- `cajas/baseline/qlib_model_bridge_trainer.py`

### Scripts / CLIs

- `cajas/scripts/build_qlib_model_training_contract.py`
- `cajas/scripts/train_qlib_model_bridge_baseline.py`
- `cajas/scripts/register_qlib_model_run.py`
- `cajas/scripts/compare_qlib_model_runs.py`
- `cajas/scripts/run_qlib_model_bridge_smoke.py`

### Tests

- `cajas/tests/test_qlib_model_training_contract.py`
- `cajas/tests/test_qlib_model_training_contract_builder.py`
- `cajas/tests/test_qlib_model_bridge_trainer.py`
- `cajas/tests/test_qlib_experiment_artifacts.py`
- `cajas/tests/test_qlib_model_metrics.py`
- `cajas/tests/test_qlib_model_run_registry.py`
- `cajas/tests/test_qlib_model_run_comparison.py`
- `cajas/tests/test_build_qlib_model_training_contract_cli.py`
- `cajas/tests/test_train_qlib_model_bridge_baseline_cli.py`
- `cajas/tests/test_register_qlib_model_run_cli.py`
- `cajas/tests/test_compare_qlib_model_runs_cli.py`
- `cajas/tests/test_run_qlib_model_bridge_smoke.py`

### Docs / exports

- Update `cajas/reports/__init__.py`
- Update `cajas/baseline/__init__.py` if needed
- Update `cajas/README.md`
- Update `cajas/docs/qlib_integration_notes.md`
- Add or keep this prompt at:
  - `tasks/phase_086_095_qlib_model_experiment_bridge_prompt.md`

## CLI Behavior Requirements

All CLIs should:

- Use argparse.
- Return non-zero on invalid input.
- Create parent output directories as needed.
- Write deterministic JSON with sorted keys and indentation where practical.
- Print concise output paths.
- Avoid hidden network calls.
- Avoid Qlib core mutation.
- Avoid GPU/CUDA assumptions.

Suggested commands:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_qlib_model_training_contract.py \
  --handler-input tmp/qlib-dataset-handler-smoke/handler_input/handler_input.csv \
  --handler-manifest tmp/qlib-dataset-handler-smoke/handler_input/handler_input_manifest.json \
  --dataset-contract tmp/qlib-dataset-handler-smoke/dataset_contract/qlib_dataset_contract.json \
  --handler-smoke-report tmp/qlib-dataset-handler-smoke/validation/qlib_handler_smoke_report.json \
  --out tmp/qlib-model-bridge-smoke/contract/qlib_model_training_contract.json
```

```bash
./.venv-qlib313/bin/python cajas/scripts/train_qlib_model_bridge_baseline.py \
  --training-contract tmp/qlib-model-bridge-smoke/contract/qlib_model_training_contract.json \
  --out-dir tmp/qlib-model-bridge-smoke/experiment \
  --seed 42 \
  --max-rows 5000
```

```bash
./.venv-qlib313/bin/python cajas/scripts/register_qlib_model_run.py \
  --experiment-dir tmp/qlib-model-bridge-smoke/experiment \
  --registry tmp/qlib-model-bridge-smoke/registry/model_run_registry.jsonl
```

```bash
./.venv-qlib313/bin/python cajas/scripts/compare_qlib_model_runs.py \
  --registry tmp/qlib-model-bridge-smoke/registry/model_run_registry.jsonl \
  --out tmp/qlib-model-bridge-smoke/comparison/model_run_comparison.json
```

```bash
./.venv-qlib313/bin/python cajas/scripts/run_qlib_model_bridge_smoke.py \
  --out-root tmp/qlib-model-bridge-smoke
```

If current script contracts differ, adapt to the actual codebase and document the final valid commands.

## Training Rules

Training is allowed in this phase only under these constraints:

- CPU only.
- Bounded smoke mode.
- Deterministic seed.
- No broker/live/paper trading integration.
- No PnL metrics.
- No automatic production promotion.
- No GPU required.
- Training results are research artifacts only.

Use a fallback strategy:

1. If sklearn is available, use a lightweight sklearn baseline.
2. If the intended model dependency is missing, fail gracefully or use a simple deterministic fallback model.
3. Tests should not depend on heavyweight external packages unless they are already project requirements.

## Validation Commands

Run:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python -m pytest cajas/tests
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\.py$' || true
```

Also run the model bridge smoke:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_qlib_model_bridge_smoke.py \
  --out-root tmp/qlib-model-bridge-smoke
```

If runtime is too heavy, reduce rows/seeds inside the smoke runner, but do not skip the smoke unless the environment blocks execution. If blocked, report exactly what passed and what remains.

## Commit Requirements

After validation passes, create local commits. Suggested split:

1. Model training contract + builder + CLI + tests
2. Baseline trainer + experiment artifacts + metrics + tests
3. Run registry + comparison report + CLIs + tests
4. Smoke runner + docs + prompt

Do not push.

Report:

- branch name
- validation results
- smoke output paths
- local commit hashes
- final `git status --short`
- manual push command:

```bash
git push origin cajas/market-recognition-phase-0
```

## Final Response Format

Return a concise implementation summary with:

- Summary
- Files changed
- Validation
- Smoke output paths
- Git commits
- Notes / risks

