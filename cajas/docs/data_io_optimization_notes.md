# Data IO Optimization Notes

## Scope

Phase 276-315 introduces data I/O audit and large-CSV readiness utilities for offline research workflows.

## Data Directory Example

- `/home/phiner/projects/research/data`
- `EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv`
- `EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv`

## Large CSV Metadata

Use cheap metadata scan by default:

```bash
./.venv-qlib313/bin/python cajas/scripts/inspect_large_csv.py \
  --input "/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv" \
  --out tmp/data-io-audit/eurusd_2020_2024_metadata.json \
  --sample-lines 100
```

Optional heavy checks (`--count-rows`, `--hash`) are explicit.

## Manifest and Cache

Build reusable dataset manifest:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_dataset_file_manifest.py \
  --data-root /home/phiner/projects/research/data \
  --pattern "EURUSD_15 Mins_Bid_*.csv" \
  --out tmp/data-io-audit/eurusd_dataset_manifest.json
```

Build cache index from manifest:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_dataset_cache_index.py \
  --manifest tmp/data-io-audit/eurusd_dataset_manifest.json \
  --cache-root tmp/data-cache \
  --out tmp/data-cache/dataset_cache_index.json
```

## Chunked Reads

Use chunk iteration for large inputs and selected columns:

- `cajas/data_io/chunked_csv_reader.py`
- `cajas/data_io/fx_kline_schema.py`

## Validation Guardrails

- fast validation does not read real data by default
- micro smoke uses fixture artifacts by default
- real-data mode requires explicit `--include-real-data`
- for large files, `--allow-large-data` acknowledgement is required

## Runtime Audits

- data source usage audit: `cajas/scripts/audit_data_sources.py`
- io runtime audit: `cajas/scripts/audit_io_runtime.py`

These audits are static/metadata-only and avoid heavy pipeline execution.
