# Phase 396–425 Prompt: Generated Artifact Reader Closure + Fast Validation Under-90s Push

You are working on branch:

- `phase-next-mega-logic`

## Current state

Phase 366–395 core goals completed.

Latest improvements:

- CSV policy controls added to:
  - `cajas/audits/leakage_drift_audit.py`
  - `cajas/baseline/prediction_review.py`
  - `cajas/baseline/qlib_model_bridge_trainer.py`
- Static audit now treats policy-guarded `read_csv` callsites as non-likely-unbounded reads.
- Validation runtime audit now reports subprocess findings with file/line/snippet/cost/action.
- Subprocess-heavy `test_run_smoke_validation_tiers` micro orchestration test moved to `integration`.

Latest validation:

```text
PASS targeted tests:
  test_leakage_drift_audit.py
  test_prediction_review.py
  test_qlib_model_bridge_trainer.py
  test_validation_runtime_audit.py
  test_data_source_audit.py
  test_run_smoke_validation_tiers.py

PASS audit_data_sources.py
PASS audit_validation_runtime.py
PASS fast pytest subset:
  302 passed, 15 deselected in 115.50s
PASS run_fast_validation.py --tier fast:
  total: 119.28s
PASS find cajas -path "*/init.py" -print:
  no output
```

Latest metrics:

```text
reads_full_csv_likely_count: 17 -> 14
run_fast_validation --tier fast: 136.67s -> 119.28s
```

Known remaining risks:

- 14 likely full-read candidates remain.
- Remaining candidates are mostly `generated_artifact_risk`, likely report builders that only need preview/count/stat summaries.
- Fast validation is green but still around 119s.
- Working tree may contain unrelated pre-existing modified/untracked files; do not revert or mix unrelated changes.

## Phase objective

Implement **Generated Artifact Reader Closure + Fast Validation Under-90s Push**.

Primary goals:

1. Refactor remaining generated-artifact full-read candidates where reports only need:
   - preview rows
   - counts
   - schema
   - distribution summaries
   - small top-k samples
2. Reduce `reads_full_csv_likely_count` from 14 to a materially lower count, ideally under 8.
3. Reduce fast validation runtime from ~119s toward under 90s.
4. Keep fast validation green.
5. Keep all safety/research boundaries unchanged.

If under-90s cannot be reached in this pass, produce exact top slow tests and classify them for the next pass.

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

# Part A — Exact remaining candidate audit

Start with:

```bash
git status --short
```

Do not revert unrelated files.

Run:

```bash
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py \
  --project-root cajas \
  --data-root /home/phiner/projects/research/data \
  --out-json tmp/data-io-audit/data_source_audit_phase396_before.json \
  --out-md tmp/data-io-audit/data_source_audit_phase396_before.md
```

Inspect the remaining 14 likely full-read candidates.

Create/update:

- `cajas/docs/full_read_csv_refactor_plan.md`

Add Phase 396 section:

- remaining candidate path
- category:
  - generated_artifact_risk
  - real_data_risk
  - test_only
  - docs_only
  - policy_guarded_false_positive
- action:
  - refactor now
  - classify lower risk
  - leave with reason

---

# Part B — Refactor generated-artifact report readers

Prioritize generated-artifact readers that use `pd.read_csv` but only need bounded report data.

Likely modules may include report builders for:

- comparisons
- summaries
- review queues
- suggestions
- predictions
- metrics
- catalog/index reports
- final bundles
- validation summaries

For each refactor, prefer one of:

## B1. Preview-only read

For reports that display examples:

- add `row_limit`
- use `nrows=row_limit`
- default row limit small, e.g. 1000 or less
- make full read explicit with `allow_large_data`

## B2. Chunked aggregate stats

For reports that need counts or distributions:

- use `chunked_csv_reader`
- compute counts incrementally
- selected columns only
- avoid full dataframe materialization

## B3. Metadata/manifest read

For reports that only need schema/row count/status:

- use dataset manifest if available
- use large CSV metadata scanner
- avoid reading CSV body

## B4. Static audit precision

If a site is already safe but static audit flags it:

- improve audit classifier
- include why it is policy guarded
- reduce false likely-full-read count without hiding real risks

Do not break backward compatibility.

Add optional params/API fields where needed:

```python
row_limit: int | None = None
chunk_size: int | None = None
sample_only: bool = False
allow_large_data: bool = False
selected_columns: list[str] | None = None
manifest: str | None = None
```

---

# Part C — Fast validation under-90s push

Current fast subset:

```text
302 passed, 15 deselected in 115.50s
```

Run one duration report:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests \
  -m "not smoke and not slow and not closure and not full and not integration" \
  --durations=50 -q
```

Identify top slow fast-tier tests.

For each top slow file, choose one:

1. Convert subprocess CLI execution to direct function test.
2. Monkeypatch subprocess calls.
3. Use tiny static fixtures.
4. Mark slow cross-module test as `integration`.
5. Split into fast unit + integration end-to-end.

Do not remove coverage.

Focus especially on tests involving:

- CLI subprocess
- validation runners
- audit builders
- report builders over temp trees
- data I/O scans
- repeated compile/discovery
- large fixture generation

Update marker policy if needed.

---

# Part D — Improve validation runtime audit recommendations

Update:

- `cajas/reports/validation_runtime_audit.py`
- `cajas/scripts/audit_validation_runtime.py`

Add or improve:

- top suspicious fast-tier files
- subprocess call counts by file
- temp directory write patterns
- likely expensive file traversal patterns
- recommended action:
  - keep_fast
  - monkeypatch_subprocess
  - mark_integration
  - mark_slow
  - split_unit_integration
  - fixture_reduce
- marker status per file

The audit should make it obvious why fast validation is still >90s.

---

# Part E — Tests

Add/update tests for:

## Generated artifact readers

- preview-only readers do not full-read large CSV by default
- row_limit is respected
- chunked aggregate stats match tiny full-read fixture results
- manifest-only mode avoids CSV body read
- backward-compatible default works for tiny fixture

## Data-source audit

- policy-guarded generated artifact reads are classified lower risk
- unguarded `pd.read_csv` remains likely full-read
- before/after summaries include actionable count

## Runtime optimization

- validation runtime audit detects subprocess and traversal patterns
- expensive orchestration tests are no longer in fast tier when marked integration
- fast marker expression excludes integration/smoke/slow/closure/full

Keep tests deterministic and lightweight.

---

# Part F — Documentation

Update:

- `cajas/docs/full_read_csv_refactor_plan.md`
- `cajas/docs/data_io_optimization_notes.md`
- `cajas/docs/test_runtime_optimization_notes.md`
- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`
- `tasks/phase_396_425_generated_artifact_reader_runtime_prompt.md`

Document:

- remaining full-read candidates before/after
- which generated artifact readers were refactored
- fast runtime before/after
- top slow tests before/after
- remaining risks and next targets

---

# Part G — Validation commands

Use targeted checks first for changed modules.

Then run bounded validation:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_phase396_after.json --out-md tmp/data-io-audit/data_source_audit_phase396_after.md
./.venv-qlib313/bin/python cajas/scripts/audit_validation_runtime.py --tests-root cajas/tests --out-json tmp/validation-runtime-audit/validation_runtime_phase396.json --out-md tmp/validation-runtime-audit/validation_runtime_phase396.md
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration" --durations=30 -q
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/validation-runtime-audit/fast_validation_phase396.json
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
```

If any command exceeds a few minutes, stop and report bottleneck instead of burning time.

---

# Commit guidance

Suggested split:

1. `refactor: bound generated artifact csv readers`
2. `test: reduce fast-tier orchestration runtime`
3. `feat: improve runtime audit recommendations`
4. `docs: document generated artifact reader closure`

Report:

- changed files
- validation results
- data source audit before/after
- fast pytest runtime before/after
- run_fast_validation timing
- remaining full-read candidates
- remaining slow tests
- commit hashes
- final `git status --short`
- manual push command:

```bash
git push origin phase-next-mega-logic
```

---

# Final response expected from Codex

Return compact summary:

- Summary
- Files changed
- Validation
- Data source audit before/after
- Runtime before/after
- Remaining risks
- Git commits
- Final status

Do not push from Codex unless explicitly instructed.
