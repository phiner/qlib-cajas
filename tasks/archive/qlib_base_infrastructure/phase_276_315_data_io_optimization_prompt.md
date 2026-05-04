# Phase 276–315 Prompt: Data I/O Optimization + Large CSV Readiness + Validation Runtime Refactor

You are working on branch:

- `phase-next-mega-logic`

## Current problem

Validation and smoke runs are consuming too much time and too many tokens. The machine also shows high CPU `wa` / I/O wait during runs.

This suggests bottlenecks may include:

- repeated filesystem scans
- repeated reads of generated artifacts
- repeated writes to nested `tmp/` outputs
- repeated generation of large intermediate files
- pytest tests invoking full pipelines
- smoke runners nesting other smoke runners
- inefficient JSON/CSV/JSONL reads/writes
- repeated compile/test/script execution instead of coding first
- no caching or manifest-based reuse
- validation scripts optimized for completeness, not development iteration

The local data directory example is:

```bash
/home/phiner/projects/research/data
```

Known files:

```text
EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv
EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv
```

These current files are not multi-GB yet, but the project should be prepared for future multi-GB CSVs.

## Phase objective

Implement **Data I/O Optimization + Large CSV Readiness + Validation Runtime Refactor**.

Focus on coding improvements that reduce unnecessary disk I/O and repeated work.

Target outcomes:

1. Validation commands should stop repeatedly regenerating the same full artifact tree unless explicitly requested.
2. Smoke runners should support fixture/reuse modes.
3. Artifact scans should use cached manifests where safe.
4. Validation should prefer static/tiny fixtures for default paths.
5. Expensive filesystem operations should be measured and reported.
6. Heavy validation should be explicit, not accidental.
7. Real data files should never be read by fast validation unless explicitly requested.
8. The project should be closer to a “ready to run validation” architecture without burning time every coding turn.

## Important instruction

Do not spend most of the task repeatedly running long validation commands.

Prioritize code changes.

Run only bounded, targeted checks until the end. If a command exceeds a few minutes, stop and report where it got stuck.

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

# Part A — I/O runtime audit

## A1. Add I/O audit utility

Create:

- `cajas/reports/io_runtime_audit.py`
- `cajas/scripts/audit_io_runtime.py`

The audit should statically inspect the project and optionally inspect a tmp output root.

It should report:

- scripts that recursively scan directories
- scripts that call `Path.rglob`
- scripts that repeatedly read JSON/CSV/JSONL
- scripts that write many artifact files
- smoke runners that call other smoke runners
- nested output root depth
- largest files under a provided tmp root
- most common file extensions under tmp root
- likely redundant generated files
- recommended optimization action

Suggested CLI:

```bash
./.venv-qlib313/bin/python cajas/scripts/audit_io_runtime.py \
  --project-root cajas \
  --tmp-root tmp \
  --out-json tmp/io-runtime-audit/io_runtime_audit.json \
  --out-md tmp/io-runtime-audit/io_runtime_audit.md
```

This should not run heavy pipelines. It should inspect files and metadata only.

## A2. Add runtime/file-count helpers

Create:

- `cajas/reports/runtime_io_summary.py`

Reusable functions:

- count files under root
- summarize extension counts
- summarize largest files
- summarize directory depth
- safe JSON read helper
- safe JSON write helper with deterministic serialization
- optional atomic write helper

Use this in audit/report scripts where appropriate.

---

# Part B — Data source usage audit

## B1. Add data source audit

Create:

- `cajas/reports/data_source_audit.py`
- `cajas/scripts/audit_data_sources.py`

The audit should statically inspect:

- `cajas/`
- `tasks/`
- optionally config/docs

It should report:

- hardcoded references to `/home/phiner/projects/research/data`
- references to `EURUSD_15 Mins_Bid_*.csv`
- references to `.csv` inputs
- default CLI input paths
- config file data paths
- scripts that call `read_csv`
- scripts that call `open(...csv...)`
- scripts that read full CSV into memory
- scripts that support chunking already
- scripts that write large generated CSV outputs

Suggested CLI:

```bash
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py \
  --project-root cajas \
  --data-root /home/phiner/projects/research/data \
  --out-json tmp/data-io-audit/data_source_audit.json \
  --out-md tmp/data-io-audit/data_source_audit.md
```

The report should answer:

- Are the current known EURUSD CSV files referenced by code/config?
- Which scripts may read them?
- Which validation/smoke commands might accidentally read full data?
- Which paths are fixture-only?

Do not run heavy data reads in this audit.

---

# Part C — Large CSV metadata and manifest

## C1. Add large CSV metadata scanner

Create:

- `cajas/data_io/__init__.py`
- `cajas/data_io/large_csv_metadata.py`
- `cajas/scripts/inspect_large_csv.py`

The scanner should collect metadata without loading the full CSV into memory:

- file path
- file size
- modified time
- SHA256 optional, disabled by default for large files
- first N lines sample
- header columns
- delimiter guess
- approximate row count using streaming line count only when requested
- optional exact row count using streaming only when requested
- date/time column candidates
- numeric column candidates from sample
- min/max timestamp only if feasible in sample or explicit chunk mode
- warnings for spaces/special chars in file name
- suggested normalized dataset id

Suggested CLI:

```bash
./.venv-qlib313/bin/python cajas/scripts/inspect_large_csv.py \
  --input "/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv" \
  --out tmp/data-io-audit/eurusd_2020_2024_metadata.json
```

Options:

```bash
--sample-lines 100
--count-rows
--hash
--chunk-size 100000
```

Defaults should be cheap:

- sample only
- no full hash
- no full row count unless requested

## C2. Add dataset file manifest

Create:

- `cajas/data_io/dataset_file_manifest.py`
- `cajas/scripts/build_dataset_file_manifest.py`

Manifest fields:

- dataset id
- source files
- file sizes
- headers
- row count status
- timestamp range status
- schema fingerprint
- optional checksum
- generated time
- reusable flag
- warnings

Suggested CLI:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_dataset_file_manifest.py \
  --data-root /home/phiner/projects/research/data \
  --pattern "EURUSD_15 Mins_Bid_*.csv" \
  --out tmp/data-io-audit/eurusd_dataset_manifest.json
```

The manifest should not load full data by default.

---

# Part D — Chunked CSV reader utilities

Create:

- `cajas/data_io/chunked_csv_reader.py`
- `cajas/data_io/fx_kline_schema.py`

## D1. Chunked reader

Implement utilities that support:

- streaming chunks
- selected columns
- dtype hints
- parse date/time columns only when requested
- row limit
- date range filtering in streaming mode
- memory-safe iteration
- per-chunk validation
- deterministic chunk stats

Example API:

```python
from cajas.data_io.chunked_csv_reader import iter_csv_chunks

for chunk in iter_csv_chunks(
    path,
    columns=["timestamp", "open", "high", "low", "close"],
    chunk_size=100_000,
    row_limit=None,
):
    ...
```

If pandas is available, use `pandas.read_csv(..., chunksize=...)`.

If pandas is not available, provide a csv-module fallback for metadata/sample utilities.

## D2. FX/K-line schema detector

Implement:

- column normalization suggestions
- common column aliases:
  - timestamp/date/time
  - open
  - high
  - low
  - close
  - volume
  - bid/ask if present
- validation:
  - required OHLC columns
  - numeric parseability from sample
  - timestamp parseability from sample
  - monotonic timestamp sample check
- report warnings, do not crash for unknown formats unless strict mode enabled

---

# Part E — Data cache and converted format readiness

## E1. Dataset cache index

Create:

- `cajas/data_io/dataset_cache_index.py`
- `cajas/scripts/build_dataset_cache_index.py`

Purpose:

- map source CSV files to reusable derived artifacts
- avoid repeated full CSV reads
- track source file size/mtime/schema fingerprint
- detect stale cache

Output:

- `dataset_cache_index.json`

Suggested CLI:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_dataset_cache_index.py \
  --manifest tmp/data-io-audit/eurusd_dataset_manifest.json \
  --cache-root tmp/data-cache \
  --out tmp/data-cache/dataset_cache_index.json
```

## E2. Optional columnar conversion command

Create:

- `cajas/scripts/convert_csv_to_columnar_cache.py`

Requirements:

- optional and explicit
- do not run by default in tests/smoke
- support output formats based on installed libraries:
  - parquet if pyarrow/fastparquet available
  - feather if available
  - fallback: chunked normalized CSV shards
- support:
  - `--input`
  - `--out-dir`
  - `--chunk-size`
  - `--columns`
  - `--row-limit`
  - `--force`
- write manifest:
  - `columnar_cache_manifest.json`

If parquet dependencies are not installed, do not fail the whole project. Use fallback shard mode and report a warning.

---

# Part F — Refactor existing data readers to support chunking/cache

Audit and update current scripts that read CSV data.

Likely targets:

- dataset export scripts
- kline feature builders
- qlib handler input builders
- model bridge smoke data generation
- future training skeleton tests/scripts
- any scripts using pandas `read_csv` without chunking

Rules:

- For tiny fixtures, normal full read is OK.
- For real data paths, prefer:
  - row limits for smoke
  - chunked reader
  - selected columns
  - dataset manifest
  - cache reuse
- Add CLI options where useful:
  - `--row-limit`
  - `--chunk-size`
  - `--use-cache`
  - `--cache-root`
  - `--manifest`
  - `--sample-only`
  - `--no-full-data`

Do not break existing CLI compatibility.

---

# Part G — Validation and smoke must not read real data by default

Update validation scripts:

- `cajas/scripts/run_fast_validation.py`
- `cajas/scripts/run_smoke_validation.py`
- any micro/minimal smoke scripts

Ensure:

- fast validation never reads `/home/phiner/projects/research/data` by default
- micro smoke uses tiny fixtures
- minimal smoke uses tiny fixtures or cached prepared artifacts
- real data checks require explicit flag, e.g.:

```bash
--include-real-data
--data-root /home/phiner/projects/research/data
```

Add guardrails:

- if a script is about to read files larger than threshold, print warning
- require `--allow-large-data` for full scan / full read
- allow `--sample-only` by default

---

# Part H — I/O budget and logging

Add lightweight I/O runtime logging helpers:

- elapsed time per major file operation
- file count scanned
- bytes read estimate where feasible
- bytes written estimate where feasible
- largest output files
- warning if nested output path is too deep

Create:

- `cajas/reports/io_budget.py`

Use in new data audit/cache scripts and optionally validation scripts.

---

# Part I — Tests

Add focused tests.

Required coverage:

## Data source audit

- detects hardcoded data root references
- detects read_csv usage
- detects CSV CLI input options
- writes JSON/Markdown
- does not read large files

## I/O runtime audit

- detects rglob usage
- detects nested smoke runner calls
- reports tmp file counts without reading file contents
- writes JSON/Markdown

## Large CSV metadata

- reads header/sample only
- row count optional
- hash optional
- handles file names with spaces
- detects columns from tiny fixture

## Chunked reader

- iterates tiny CSV in chunks
- supports selected columns
- supports row limit
- supports sample-only behavior
- validates OHLC schema from fixture

## Dataset manifest/cache

- builds manifest from tiny fixture files
- detects schema fingerprint
- detects stale cache when file metadata changes
- does not require full data load

## Columnar conversion

- writes fallback normalized CSV shards if parquet unavailable
- writes manifest
- respects row limit
- does not run by default in smoke

## Validation guardrails

- fast validation does not read real data root by default
- smoke micro does not read real data root
- real data mode requires explicit flag
- large data warning triggers on threshold fixture

Keep tests deterministic and lightweight. Use tiny fixtures only.

---

# Part J — Documentation

Update:

- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`
- `cajas/docs/test_runtime_optimization_notes.md`
- create `cajas/docs/data_io_optimization_notes.md`
- `cajas/data_examples/README.md`
- `tasks/phase_276_315_data_io_optimization_prompt.md`

Document:

- current data directory example
- how to inspect large CSV metadata
- how to build dataset manifest
- how to use chunked reads
- how to convert to cache/shards
- why fast validation should not read real data
- when to use `--include-real-data`
- how to avoid I/O wait during development
- future multi-GB readiness approach

---

# Part K — Validation commands

Prioritize bounded checks.

Run:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration"
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit.json --out-md tmp/data-io-audit/data_source_audit.md
./.venv-qlib313/bin/python cajas/scripts/audit_io_runtime.py --project-root cajas --tmp-root tmp --out-json tmp/io-runtime-audit/io_runtime_audit.json --out-md tmp/io-runtime-audit/io_runtime_audit.md
./.venv-qlib313/bin/python cajas/scripts/inspect_large_csv.py --input "/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv" --out tmp/data-io-audit/eurusd_2020_2024_metadata.json --sample-lines 100
./.venv-qlib313/bin/python cajas/scripts/build_dataset_file_manifest.py --data-root /home/phiner/projects/research/data --pattern "EURUSD_15 Mins_Bid_*.csv" --out tmp/data-io-audit/eurusd_dataset_manifest.json
```

Do not run full row count or hash on large files unless explicitly needed:

```bash
# Optional explicit heavy checks only:
./.venv-qlib313/bin/python cajas/scripts/inspect_large_csv.py --input "...csv" --out tmp/data-io-audit/full_metadata.json --count-rows --hash
```

If commands exceed a few minutes, stop and report the bottleneck.

---

# Commit guidance

Suggested split:

1. `feat: add data source and io runtime audits`
2. `feat: add large csv metadata and chunked reader utilities`
3. `feat: add dataset cache manifest and columnar cache fallback`
4. `test: guard validation from accidental real data reads`
5. `docs: document data io optimization workflow`

Report:

- changed files
- validation results
- data source audit summary
- large CSV metadata summary
- runtime/I/O notes
- whether current EURUSD files are referenced by validation by default
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
- Data source audit result
- Large CSV metadata result
- I/O optimization notes
- Remaining risks
- Git commits
- Final status

Do not push from Codex unless explicitly instructed.

---

## Implementation Notes (local)

- Added static IO runtime audit and data source audit modules/CLIs.
- Added large CSV metadata scanner, dataset manifest, cache index, and chunked reader utilities under `cajas/data_io/`.
- Added optional CSV-shard fallback converter for cache preparation.
- Added fast/smoke validation guardrail flags for explicit real-data acknowledgement.
- Added lightweight deterministic tests and tiny CSV fixture for new data IO paths.
