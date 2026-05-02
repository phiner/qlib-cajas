# Phase 316–345 Prompt: Full-Read CSV Refactor + Fast Validation Runtime Closure

You are working on branch:

- `phase-next-mega-logic`

## Current state

Phase 276–315 completed.

Latest known results:

- Added data-source audit and I/O runtime audit.
- Added large CSV metadata scanner.
- Added dataset file manifest.
- Added chunked CSV reader and FX/K-line schema helpers.
- Added dataset cache index and columnar/shard fallback converter.
- Added validation guardrails:
  - `--include-real-data`
  - `--allow-large-data`
- Fast validation and micro smoke should not read real data by default.

Latest validation:

```text
compileall: pass
path hygiene: pass
find init.py: pass
git ls-files init.py: pass
fast pytest subset: 298 passed, 13 deselected in 136.15s
data source audit: pass
I/O runtime audit: pass
inspect_large_csv: pass
build_dataset_file_manifest: pass
```

Data source audit summary:

```text
hardcoded_data_root_count: 7
read_csv_count: 27
reads_full_csv_likely_count: 25
chunking_support_count: 7
eurusd_refs: 2
```

Large CSV metadata summary:

```text
file: /home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv
size_bytes: 7507023
header: ['Time (UTC)', 'Open', 'High', 'Low', 'Close', 'Volume ']
delimiter: ,
warning: filename contains spaces
manifest source_files: 2
row_count_status: not_requested
```

Known remaining risks:

- There are still many likely full-read `read_csv` call sites.
- Fast pytest subset is still slow at ~136 seconds.
- Some unrelated pre-existing uncommitted changes may exist from earlier phases; do not overwrite or mix them blindly.
- This phase should continue coding/refactoring rather than repeatedly running expensive validation loops.

## Phase objective

Implement **Full-Read CSV Refactor + Fast Validation Runtime Closure**.

Primary goals:

1. Reduce `reads_full_csv_likely_count`.
2. Refactor high-risk `read_csv` sites to use chunking, row limits, manifests, or cache-aware helpers.
3. Ensure smoke/validation paths use tiny fixtures or sample modes by default.
4. Add explicit real-data/full-data modes where needed.
5. Profile and reduce fast pytest runtime.
6. Keep all research safety boundaries unchanged.

Target outcomes:

- `reads_full_csv_likely_count` should decrease materially.
- Fast pytest subset should become faster than 136 seconds, preferably under 90 seconds if feasible.
- If runtime cannot be reduced further in this pass, produce exact slow test/file evidence and mark or refactor accordingly.
- Real-data full reads must require explicit user intent.

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

# Part A — Rank and classify full-read CSV call sites

Start by running:

```bash
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py \
  --project-root cajas \
  --data-root /home/phiner/projects/research/data \
  --out-json tmp/data-io-audit/data_source_audit.json \
  --out-md tmp/data-io-audit/data_source_audit.md
```

Inspect the exact `read_csv` / full-read findings.

Create or update:

- `cajas/docs/full_read_csv_refactor_plan.md`

Include:

- file path
- function/script
- whether it is production path, smoke path, test path, docs-only, or fixture path
- risk level:
  - high: can read real user CSV
  - medium: generated artifact CSV may become large
  - low: tiny fixture only
- remediation:
  - chunked reader
  - row limit
  - manifest/cache
  - fixture mode
  - leave unchanged with reason

Do not refactor blindly. Prioritize high-risk code paths.

---

# Part B — Add common CSV loading policy helpers

Create:

- `cajas/data_io/csv_loading_policy.py`

It should define a small policy object or helpers for CSV reads:

Fields / options:

- `row_limit`
- `chunk_size`
- `sample_only`
- `allow_large_data`
- `include_real_data`
- `selected_columns`
- `use_cache`
- `cache_root`
- `manifest`
- `max_bytes_without_allow_large_data`

Provide helpers:

- detect file size
- classify file as tiny/small/large
- reject or warn on large file without explicit allowance
- choose full-read vs chunked-read
- produce consistent warnings
- document decision in JSON-serializable form

Example behavior:

- tiny fixture CSV: full read allowed
- real data CSV over threshold: require `--allow-large-data` for full read
- if `row_limit` is set: safe sampled read
- if `chunk_size` is set: chunked read preferred

---

# Part C — Refactor high-risk script entrypoints

Refactor scripts that can read user CSV files.

Likely target categories from the audit:

- feature builders
- dataset export scripts
- qlib handler input builders
- training/baseline scripts
- future training skeleton scripts
- report builders that read generated CSVs
- tests that invoke these scripts

For each high-risk script:

Add or standardize options:

```bash
--row-limit N
--chunk-size N
--sample-only
--allow-large-data
--use-cache
--cache-root PATH
--manifest PATH
```

Behavior:

- Default smoke/test paths should use tiny fixtures or row limits.
- If a user passes a real CSV and no `--allow-large-data`, large full-read should be blocked or downgraded to sample/chunk mode.
- Existing behavior should remain available with explicit flags.

Do not break existing CLI compatibility. Add new optional flags only.

---

# Part D — Refactor tests and fixtures

Fast tests must not do expensive full reads.

Update tests that load CSVs:

- use `cajas/data_examples/validation_fixtures/eurusd_tiny.csv`
- use row limits
- use chunked reader
- monkeypatch heavy file reads
- mark real-data/full-data tests as `integration` or `slow`

Add tests:

- full read blocked for large file without `--allow-large-data`
- row-limit read allowed
- chunked read allowed
- tiny fixture full read allowed
- script CLI passes loading policy options through
- real data mode is opt-in

---

# Part E — Reduce fast pytest runtime

Current fast subset:

```text
298 passed, 13 deselected in 136.15s
```

Do not guess. Measure.

Run:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration" --durations=50
```

If this is too slow, run:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration" --collect-only -q
```

Then split by suspicious files.

Actions:

- Convert slow fast tests into smaller unit tests.
- Mark genuinely expensive cross-module tests as `integration` or `slow`.
- Avoid subprocess CLI execution in fast subset unless cheap.
- Avoid tests that build large artifact trees in fast subset.
- Use direct function tests for builder logic.
- Use monkeypatch for script orchestration tests.

Add or update:

- `cajas/docs/test_runtime_optimization_notes.md`

Include:

- slowest remaining fast tests
- actions taken
- remaining runtime
- next recommendations

---

# Part F — Improve audit_data_sources scoring

Update:

- `cajas/reports/data_source_audit.py`
- `cajas/scripts/audit_data_sources.py`

Make the audit more actionable:

- classify each finding as:
  - `real_data_risk`
  - `generated_artifact_risk`
  - `fixture_only`
  - `docs_only`
  - `test_only`
  - `unknown`
- include suggested remediation
- include whether the file already supports chunking/cache/row-limit
- include line number and snippet
- include summary by category
- exclude or downgrade obvious docs/examples where appropriate, but do not hide them

Goal:

- reduce meaningless `reads_full_csv_likely_count`
- increase useful triage quality

---

# Part G — Add validation command presets

Update:

- `cajas/scripts/run_fast_validation.py`
- `cajas/scripts/run_smoke_validation.py` if needed

Ensure daily paths are clear:

```bash
# Tight loop, no full pytest
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier quick

# Before commit
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast

# Tiny smoke
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
```

`fast` should not include integration/slow/smoke/closure/full.

If `fast` remains > 120 seconds, print a warning with duration report suggestion.

---

# Part H — Documentation updates

Update:

- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`
- `cajas/docs/test_runtime_optimization_notes.md`
- `cajas/docs/data_io_optimization_notes.md`
- `cajas/docs/full_read_csv_refactor_plan.md`
- `tasks/phase_316_345_full_read_csv_refactor_prompt.md`

Document:

- which read_csv sites were refactored
- which remain and why
- how to read real data safely
- how to use row limits/chunking/cache
- how to keep fast validation from reading real data
- updated runtime numbers

---

# Part I — Validation commands

Prioritize bounded checks.

Run:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_after_refactor.json --out-md tmp/data-io-audit/data_source_audit_after_refactor.md
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration"
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/validation-runtime-audit/fast_validation_after_refactor.json
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
```

Optional if needed:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration" --durations=50
```

Do not run full row count/hash on real data unless explicitly needed.

If commands exceed a few minutes, stop and report bottleneck rather than burning time.

---

# Commit guidance

Suggested split:

1. `feat: add csv loading policy for large data guardrails`
2. `refactor: migrate high-risk csv reads to chunked policy`
3. `test: reduce fast validation runtime from csv-heavy tests`
4. `docs: document full-read csv refactor plan`

Report:

- changed files
- validation results
- data source audit before/after summary
- fast pytest runtime before/after
- fast validation runtime
- remaining full-read call sites
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

---

## Implementation Notes (local)

- Added `cajas/data_io/csv_loading_policy.py` and wired policy checks into high-risk CSV entrypoints.
- Refactored selected builders/handlers/scripts to support row-limit/chunk/sample/full-read guardrails.
- Improved `data_source_audit` with category triage, line snippets, and remediation suggestions.
- Added `cajas/docs/full_read_csv_refactor_plan.md` with before/after audit/runtime snapshot.
