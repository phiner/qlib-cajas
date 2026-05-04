# Phase 776–805 Prompt: Split Dataset Quality Bundle into Modular CLIs + Smoke Workflow

You are working on branch:

- `phase-post-merge-research-next`

## Current state

Phase 746–775 completed and committed.

Latest commit:

```text
f72115f4 feat: add dataset quality and feature research bundle builder
```

Current branch:

```text
phase-post-merge-research-next
```

Latest validation:

```text
PASS run_fast_validation.py --tier fast
  308 passed, 15 deselected
  total ~80.81s

PASS run_smoke_validation.py --tier micro

PASS audit_data_sources.py
PASS py_compile dataset_quality_research.py and build_dataset_quality_research_bundle.py
PASS git diff --check
PASS find cajas -path "*/init.py" -print
```

Files added in Phase 746–775:

- `cajas/reports/dataset_quality_research.py`
- `cajas/scripts/build_dataset_quality_research_bundle.py`
- `cajas/tests/test_dataset_quality_research_bundle.py`
- `cajas/reports/__init__.py`

Known current issue:

- Untracked prompt artifact remains:
  - `tasks/phase_726_745_post_merge_next_workstream_prompt.md`

Manual push still needed:

```bash
git push origin phase-post-merge-research-next
```

## Phase objective

Implement **Split Dataset Quality Bundle into Modular CLIs + Smoke Workflow**.

The previous phase added a combined bundle builder. This phase should make it easier to use, test, and evolve by splitting the workflow into modular commands and adding a dedicated smoke runner.

Primary goals:

1. Keep the existing bundle builder backward compatible.
2. Add focused CLIs for each report section:
   - dataset quality
   - label coverage diagnostics
   - time/session coverage diagnostics
   - chunked feature dry-run
   - feature schema manifest
   - offline research queue summary
3. Add a dedicated dataset quality smoke runner.
4. Add tiny deterministic fixtures if needed.
5. Add documentation for the dataset quality workflow.
6. Preserve fast validation performance.
7. Preserve data-source audit stability.
8. Keep everything offline-research-only.

## Non-negotiable boundaries

Do not:

- Modify Qlib core for execution features.
- Add broker adapters.
- Add live trading.
- Add paper trading execution.
- Add order generation.
- Add order routing.
- Add position sizing.
- Add portfolio optimization.
- Add PnL optimization.
- Add execution simulation.
- Add network calls except normal git push/pull.
- Add GPU/CUDA requirements.
- Add heavy training by default.
- Add files named `init.py`; continue using `__init__.py`.

All validation remains:

- CPU-only
- local
- deterministic where feasible
- no network
- no trading execution
- bounded by default
- real data access must be explicit

---

# Part A — Branch hygiene

Start with:

```bash
git branch --show-current
git status --short
git log --oneline -5
```

Expected:

- branch is `phase-post-merge-research-next`
- latest commit includes `f72115f4`
- possible untracked file:
  - `tasks/phase_726_745_post_merge_next_workstream_prompt.md`

If that prompt file should be retained in the repo, commit it separately:

```bash
git add tasks/phase_726_745_post_merge_next_workstream_prompt.md
git commit -m "docs: add post-merge next workstream phase prompt"
```

Do not mix it into implementation commits.

Push current branch if not already pushed:

```bash
git push origin phase-post-merge-research-next
```

---

# Part B — Preserve existing bundle API

Inspect:

- `cajas/reports/dataset_quality_research.py`
- `cajas/scripts/build_dataset_quality_research_bundle.py`
- `cajas/tests/test_dataset_quality_research_bundle.py`

Before splitting, identify current public functions/classes.

Requirements:

- Existing tests must keep passing.
- Existing CLI must keep working.
- New modular CLIs may call into existing functions.
- Do not duplicate substantial logic if it can be shared cleanly.

If needed, refactor `dataset_quality_research.py` internally, but keep exported API compatible.

---

# Part C — Add modular CLIs

Create scripts as thin wrappers around the existing report logic.

Suggested scripts:

- `cajas/scripts/build_dataset_quality_report.py`
- `cajas/scripts/build_label_coverage_diagnostics.py`
- `cajas/scripts/build_time_coverage_diagnostics.py`
- `cajas/scripts/run_chunked_feature_dry_run.py`
- `cajas/scripts/build_feature_schema_manifest.py`
- `cajas/scripts/build_offline_research_queue_summary.py`

Each CLI should support:

```bash
--input PATH
--labels PATH
--manifest PATH
--out-json PATH
--out-md PATH
--row-limit N
--chunk-size N
--sample-only
--allow-large-data
```

Not every CLI needs every option if not relevant, but prefer consistency.

Behavior:

- default to tiny/bounded reads
- real/full data requires explicit `--allow-large-data`
- write JSON and Markdown when applicable
- return nonzero on missing required input
- print output paths and compact status

Do not run model training.

Do not produce trading signals.

---

# Part D — Dataset quality smoke runner

Create:

- `cajas/scripts/run_dataset_quality_smoke.py`

Default command:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_dataset_quality_smoke.py --out-root tmp/dataset-quality-smoke
```

Default inputs:

- `cajas/data_examples/validation_fixtures/eurusd_tiny.csv`
- tiny labels fixture if available

If no labels fixture exists, add one:

- `cajas/data_examples/validation_fixtures/eurusd_tiny_labels.jsonl`
  or
- `cajas/data_examples/validation_fixtures/eurusd_tiny_labels.csv`

Smoke runner should call the modular CLIs or shared functions to generate:

```text
tmp/dataset-quality-smoke/dataset_quality/dataset_quality_report.json
tmp/dataset-quality-smoke/dataset_quality/dataset_quality_report.md
tmp/dataset-quality-smoke/labels/label_coverage_diagnostics.json
tmp/dataset-quality-smoke/labels/label_coverage_diagnostics.md
tmp/dataset-quality-smoke/time/time_coverage_diagnostics.json
tmp/dataset-quality-smoke/time/time_coverage_diagnostics.md
tmp/dataset-quality-smoke/features/chunked_feature_dry_run.json
tmp/dataset-quality-smoke/features/chunked_feature_dry_run.md
tmp/dataset-quality-smoke/features/feature_schema_manifest.json
tmp/dataset-quality-smoke/features/feature_schema_manifest.md
tmp/dataset-quality-smoke/research_queue/offline_research_queue_summary.json
tmp/dataset-quality-smoke/research_queue/offline_research_queue_summary.md
```

Add flags:

```bash
--input PATH
--labels PATH
--out-root PATH
--row-limit N
--chunk-size N
--include-real-data
--allow-large-data
```

Real data remains explicit.

---

# Part E — Tests

Add focused tests.

Suggested files:

- `cajas/tests/test_dataset_quality_modular_clis.py`
- `cajas/tests/test_run_dataset_quality_smoke.py`

Required coverage:

## Modular CLIs

- each CLI writes JSON output
- Markdown output is created where supported
- missing input fails cleanly
- row-limit/sample-only options are accepted
- tiny fixture works
- no real-data read by default

## Smoke runner

- creates expected output tree
- uses tiny fixture by default
- does not require real data
- prints compact summary
- preserves forbidden actions in queue summary

## Backward compatibility

- existing `build_dataset_quality_research_bundle.py` still works
- existing `test_dataset_quality_research_bundle.py` still passes

Keep tests deterministic and fast.

Do not mark as smoke unless the test is expensive. This smoke should be lightweight.

---

# Part F — Documentation

Create or update:

- `cajas/docs/dataset_quality_loop.md`
- `cajas/docs/post_merge_next_workstream_plan.md`
- `cajas/docs/future_work_checklist.md`
- `cajas/README.md`
- `tasks/phase_776_805_dataset_quality_modular_cli_smoke_prompt.md`

Document:

- combined bundle builder
- modular CLIs
- dataset quality smoke runner
- tiny fixture defaults
- real-data flags
- outputs
- no-execution boundaries

Include command examples:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_dataset_quality_research_bundle.py \
  --input cajas/data_examples/validation_fixtures/eurusd_tiny.csv \
  --out-root tmp/dataset-quality-bundle

./.venv-qlib313/bin/python cajas/scripts/run_dataset_quality_smoke.py \
  --out-root tmp/dataset-quality-smoke
```

---

# Part G — Validation

Run:

```bash
./.venv-qlib313/bin/python -m py_compile \
  cajas/reports/dataset_quality_research.py \
  cajas/scripts/build_dataset_quality_research_bundle.py \
  cajas/scripts/build_dataset_quality_report.py \
  cajas/scripts/build_label_coverage_diagnostics.py \
  cajas/scripts/build_time_coverage_diagnostics.py \
  cajas/scripts/run_chunked_feature_dry_run.py \
  cajas/scripts/build_feature_schema_manifest.py \
  cajas/scripts/build_offline_research_queue_summary.py \
  cajas/scripts/run_dataset_quality_smoke.py

./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_dataset_quality_research_bundle.py \
  cajas/tests/test_dataset_quality_modular_clis.py \
  cajas/tests/test_run_dataset_quality_smoke.py \
  -q

./.venv-qlib313/bin/python cajas/scripts/run_dataset_quality_smoke.py --out-root tmp/dataset-quality-smoke

./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/validation-runtime-audit/fast_validation_phase776.json

./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro

./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py \
  --project-root cajas \
  --data-root /home/phiner/projects/research/data \
  --out-json tmp/data-io-audit/data_source_audit_phase776.json \
  --out-md tmp/data-io-audit/data_source_audit_phase776.md

git diff --check
find cajas -path "*/init.py" -print
```

If commands exceed a few minutes, stop and report bottleneck.

---

# Commit guidance

Suggested split:

1. `feat: add modular dataset quality research clis`
2. `feat: add dataset quality smoke workflow`
3. `docs: document dataset quality loop workflow`

Push:

```bash
git push origin phase-post-merge-research-next
```

---

# Final response expected from Codex

Return compact summary:

- Summary
- Branch/status
- Files changed
- Validation results
- Runtime summary
- Data-source audit summary
- Dataset quality smoke outputs
- Backward compatibility status
- Git commits
- Remaining risks
- Final status
- Manual push command if needed

Do not add trading execution or model-heavy training.
