# Phase 426–455 Prompt: Commit Hygiene + Final Full-Read Risk Closure + Fast Runtime Hotspot Fix

You are working on branch:

- `phase-next-mega-logic`

## Current state

Phase 396–425 completed successfully.

Latest phase results:

- Generated-artifact full-read candidates were refactored to bounded/chunked reads.
- `reads_full_csv_likely_count` improved from `14` to `9`.
- `chunking_support_count` improved from `22` to `24`.
- Fast validation remains green:
  - `run_fast_validation.py --tier fast`: `117.30s`
  - fast pytest subset: `302 passed` in about `117.44s`
- Under-90s fast validation target was not reached.

Latest top slow tests:

```text
test_validation_runners.py::test_fail_on_budget_returns_nonzero       ~7.95s
test_validation_runners.py::test_fast_validation_writes_timing_json    ~7.78s
test_baseline_runner.py::test_artifact_writing                         ~4.28s
```

Remaining likely full-read candidates:

- `feature_set_comparison.py` — generated_artifact_risk, refactored but still flagged due to `read_kwargs` pattern
- `horizon_label_preview.py` — generated_artifact_risk, refactored but still flagged due to `read_kwargs` pattern
- `qlib_handler_smoke_validator.py` — test_only, refactored but still flagged due to size-check not detected
- `external_holdout_dataset.py` — real_data_risk
- `label_variant_dataset.py` — real_data_risk
- `threshold_label_generator.py` — real_data_risk
- `kline_structure_features.py` — real_data_risk

Important repository state:

The final status from the previous run shows many modified and untracked files from earlier phases still present. Some are not part of Phase 396–425.

Do not continue feature work before separating/committing existing changes.

## Phase objective

Implement **Commit Hygiene + Final Full-Read Risk Closure + Fast Runtime Hotspot Fix**.

Primary goals:

1. Cleanly separate and commit already-completed phase work.
2. Do not mix unrelated old changes with new changes.
3. Close false positives in the data-source audit for already-guarded readers.
4. Add policy guards to remaining real-data-risk CSV readers.
5. Optimize the top slow fast-tier tests.
6. Push fast validation closer to under 90s.
7. Keep all research-only/no-execution boundaries unchanged.

## Non-negotiable boundaries

Do not:

- Modify Qlib core.
- Add broker adapters.
- Add live trading.
- Add paper trading execution.
- Add order generation.
- Add order routing.
- Add position sizing.
- Add portfolio optimization.
- Add PnL optimization.
- Add execution simulation.
- Add network calls.
- Add GPU/CUDA requirements.
- Add files named `init.py`; continue using `__init__.py`.

All validation remains:

- CPU-only
- local
- deterministic where feasible
- no network
- no broker/live/paper execution

---

# Part A — Commit hygiene first

Start with:

```bash
git status --short
git branch --show-current
```

Do not revert unrelated work.

Classify current changes into groups:

## A1. Earlier governance review / approval packet work

Likely untracked files:

- `cajas/data_examples/governance_review_decision_example.json`
- `cajas/reports/governance_review_decision.py`
- `cajas/reports/research_only_approval_packet.py`
- `cajas/scripts/build_governance_review_decision.py`
- `cajas/scripts/build_research_only_approval_packet.py`
- `cajas/scripts/run_governance_review_closure_smoke.py`
- `cajas/tests/test_governance_review_decision.py`
- `cajas/tests/test_research_only_approval_packet.py`
- `tasks/phase_216_235_manual_governance_review_closure_prompt.md`

If these are valid and tested, commit them separately:

```bash
git add <governance review files>
git commit -m "feat: add governance review approval workflow"
```

If not tested, run only targeted tests first.

## A2. Validation runtime / profiling work

Likely files:

- `cajas/tests/test_run_fast_validation_profiling.py`
- `tasks/phase_236_255_test_runtime_optimization_prompt.md`
- `tasks/phase_236_275_amendment_fast_validation_profiling_prompt.md`
- `tasks/phase_236_275_amendment_non_smoke_slow_tests_prompt.md`
- `tasks/phase_236_275_validation_runtime_audit_optimization_prompt.md`
- related modified files:
  - `cajas/reports/validation_runtime_audit.py`
  - `cajas/scripts/audit_validation_runtime.py`
  - `cajas/tests/test_validation_runtime_audit.py`
  - `cajas/tests/test_validation_runners.py`
  - `cajas/tests/test_validation_marker_policy.py`
  - `cajas/docs/test_runtime_optimization_notes.md`

Commit separately if valid:

```bash
git add <validation runtime files>
git commit -m "test: improve validation runtime profiling and tiers"
```

## A3. CSV/full-read work from phases 346–425

Likely files:

- baseline CSV policy changes
- data source audit changes
- generated artifact reader changes
- docs and task prompts for phases 346/366/396

Commit separately:

```bash
git add <csv/refactor files>
git commit -m "refactor: reduce csv full-read risks in research reports"
```

## A4. Docs/task prompts

Commit docs/prompts separately if not included:

```bash
git add tasks/... cajas/docs/...
git commit -m "docs: add validation and csv runtime phase prompts"
```

If there are unrelated pre-existing files that are not understood, leave them unstaged and report them.

End Part A with:

```bash
git status --short
```

The working tree does not have to be empty if unrelated files remain, but new Phase 426–455 work must be clearly separated.

---

# Part B — Fix data-source audit false positives

The previous phase identified refactored-but-still-flagged files:

- `feature_set_comparison.py`
- `horizon_label_preview.py`
- `qlib_handler_smoke_validator.py`

Update:

- `cajas/reports/data_source_audit.py`
- tests in `cajas/tests/test_data_source_audit.py`

Audit should recognize:

1. `read_kwargs` containing `nrows`
2. explicit `nrows=...`
3. calls guarded by `CsvLoadingPolicy`
4. file size checks before read
5. test-only fixture validators

Do not hide genuine full reads.

Expected result:

- these already-guarded sites should be classified as:
  - `policy_guarded_false_positive`
  - `bounded_preview`
  - `test_only_guarded`
- not counted as likely unbounded full reads.

---

# Part C — Add guards to remaining real-data-risk readers

Prioritize:

- `external_holdout_dataset.py`
- `label_variant_dataset.py`
- `threshold_label_generator.py`
- `kline_structure_features.py`

Add support where appropriate:

```python
row_limit: int | None = None
chunk_size: int | None = None
sample_only: bool = False
allow_large_data: bool = False
selected_columns: list[str] | None = None
manifest: str | None = None
```

For scripts/CLIs, add optional flags without breaking compatibility:

```bash
--row-limit N
--chunk-size N
--sample-only
--allow-large-data
--manifest PATH
```

Behavior:

- tiny fixture reads remain easy
- real/multi-GB full reads require explicit `--allow-large-data`
- row-limit/sample mode is allowed
- chunked mode is preferred when possible
- semantic outputs remain unchanged for small fixture data
- no trading/execution logic is added

Add or update tests for each changed module.

---

# Part D — Optimize top slow fast-tier tests

Top current slow tests:

```text
test_validation_runners.py::test_fail_on_budget_returns_nonzero
test_validation_runners.py::test_fast_validation_writes_timing_json
test_baseline_runner.py::test_artifact_writing
```

Do not run real slow subprocesses in fast-tier tests if avoidable.

## D1. validation runner tests

Update tests to use monkeypatch/fake command runner.

Goals:

- avoid actual `compileall`
- avoid actual pytest subprocess
- avoid real sleeps/time-heavy commands
- still validate:
  - budget handling
  - timing JSON writing
  - nonzero behavior when `--fail-on-budget`
  - command planning

If direct monkeypatching is hard, refactor `run_fast_validation.py` minimally to expose pure functions:

- build command plan
- run step with injected runner
- write timing JSON
- evaluate budget

Then tests can call pure functions.

## D2. baseline runner artifact writing test

Inspect:

- `cajas/tests/test_baseline_runner.py::test_artifact_writing`

If it writes many files or runs model logic:

- replace with tiny fixture
- monkeypatch model/training work
- verify artifact schema rather than full execution
- mark as `integration` if it truly needs end-to-end training

Do not remove coverage.

---

# Part E — Validation and audits

Run bounded checks:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_phase426_after.json --out-md tmp/data-io-audit/data_source_audit_phase426_after.md
./.venv-qlib313/bin/python cajas/scripts/audit_validation_runtime.py --tests-root cajas/tests --out-json tmp/validation-runtime-audit/validation_runtime_phase426.json --out-md tmp/validation-runtime-audit/validation_runtime_phase426.md
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration" --durations=30 -q
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/validation-runtime-audit/fast_validation_phase426.json
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
```

If any command exceeds a few minutes, stop and report exact bottleneck.

---

# Part F — Documentation

Update:

- `cajas/docs/full_read_csv_refactor_plan.md`
- `cajas/docs/data_io_optimization_notes.md`
- `cajas/docs/test_runtime_optimization_notes.md`
- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`
- `tasks/phase_426_455_commit_hygiene_full_read_fast_runtime_prompt.md`

Document:

- commit hygiene result
- files intentionally left uncommitted, if any
- data-source audit before/after
- full-read false positives fixed
- real-data-risk modules guarded
- fast runtime before/after
- remaining slow tests

---

# Commit guidance

Use multiple commits.

Suggested:

```bash
git commit -m "chore: separate prior governance and validation runtime work"
git commit -m "fix: improve data-source audit guarded-read classification"
git commit -m "refactor: guard remaining real-data csv readers"
git commit -m "test: optimize fast validation hotspot tests"
git commit -m "docs: document commit hygiene and runtime closure"
```

Only commit files you understand.

Final report should include:

- changed files
- commit groups
- validation results
- data-source audit before/after
- fast pytest runtime before/after
- run_fast_validation timing
- remaining full-read candidates
- remaining slow tests
- final `git status --short`
- manual push command:

```bash
git push origin phase-next-mega-logic
```

---

# Final response expected from Codex

Return compact summary:

- Summary
- Commit hygiene result
- Files changed
- Validation
- Data source audit before/after
- Runtime before/after
- Remaining risks
- Git commits
- Final status

Do not push from Codex unless explicitly instructed.
