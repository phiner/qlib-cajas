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

## Phase 316-345 Follow-up

- Added `cajas/data_io/csv_loading_policy.py`.
- Refactored high-risk CSV entrypoints to support row-limit/chunk/sample policy controls.
- `reads_full_csv_likely_count` reduced from `25` to `20`.
- `chunking_support_count` increased from `7` to `13`.

## Phase 366-395 Runtime + Remaining Full-Read Closure

- Added consistent policy arguments to remaining high-priority readers:
  - `row_limit`
  - `chunk_size`
  - `sample_only`
  - `allow_large_data`
  - `selected_columns`
  - `use_cache`
  - `manifest`
- Refactored:
  - `cajas/audits/leakage_drift_audit.py`
  - `cajas/baseline/prediction_review.py`
  - `cajas/baseline/qlib_model_bridge_trainer.py`
- Updated CLI wrappers to expose these controls:
  - `cajas/scripts/audit_leakage_and_drift.py`
  - `cajas/scripts/inspect_baseline_run.py`
  - `cajas/scripts/train_qlib_model_bridge_baseline.py`
- Improved static audit signal quality:
  - policy-guarded `read_csv` callsites are no longer classified as likely unbounded full-read sites.

Audit metrics:

- before (`phase366_before`): `read_csv_count=28`, `reads_full_csv_likely_count=17`, `chunking_support_count=16`
- after (`phase366_after`): `read_csv_count=29`, `reads_full_csv_likely_count=14`, `chunking_support_count=20`

Fast runtime:

- previous fast validation total: `136.67s`
- current fast validation total: `119.28s`
- key driver: subprocess-heavy smoke-tier orchestration test moved out of default fast subset via integration marker.


## Phase 396-425 Generated Artifact Reader Closure

- Refactored generated-artifact report readers to avoid full CSV reads:
  - `cajas/reports/research_gate_builder.py`: line-counting instead of `pd.read_csv()` for row count
  - `cajas/baseline/flat_class_diagnosis.py`: chunked counting with `chunksize` parameter
  - `cajas/scripts/diagnose_flat_class.py`: added `--chunk-size` and `--artifact-row-limit`
  - `cajas/baseline/feature_set_comparison.py`: added policy guard with `row_limit`/`allow_large_data`
  - `cajas/datasets/horizon_label_preview.py`: added `row_limit` for preview-only reads
  - `cajas/reports/qlib_handler_smoke_validator.py`: added 50 MB fixture size check
- Improved static audit classifier:
  - detects false positives: `chunked_csv_reader.py` (internal impl), `io_runtime_audit.py` (string pattern)

Audit metrics:

- before (`phase396_before`): `read_csv_count=29`, `reads_full_csv_likely_count=14`, `chunking_support_count=22`
- after (`phase396_after`): `read_csv_count=28`, `reads_full_csv_likely_count=9`, `chunking_support_count=24`

Fast runtime:

- previous fast validation total: `119.28s`
- current fast validation total: `117.30s`
- fast pytest runtime: `117.44s`

Net effect:

- Reduced likely full-read candidates by **5** (14 → 9)
- Increased chunking/policy-capable sites by **2** (22 → 24)
- Runtime improvement: **1.98s** (119.28s → 117.30s)


## Phase 426-455 Commit Hygiene + Final Full-Read Risk Closure

### Commit Hygiene

Successfully separated prior work into 4 focused commits:

1. Governance review workflow (9 files)
2. Validation runtime profiling (11 files)
3. CSV policy work phases 346-395 (14 files)
4. Report builders consistency (17 files)

### Classifier Improvements

Enhanced data-source audit to detect:

- `**read_kwargs` patterns with `nrows`/`row_limit`
- Size check guards (`.stat().st_size` before `read_csv`)
- Explicit `nrows=` parameters

### Real-Data-Risk Guards

Added policy guards to final real-data readers:

- `cajas/datasets/external_holdout_dataset.py`
- `cajas/datasets/label_variant_dataset.py`
- `cajas/datasets/threshold_label_generator.py`
- `cajas/features/kline_structure_features.py`

All support `row_limit` and `allow_large_data` parameters.

### Audit Metrics

**Before (phase396_after):**
- `read_csv_count: 28`
- `reads_full_csv_likely_count: 9`
- `chunking_support_count: 24`

**After (phase426_final):**
- `read_csv_count: 29`
- `reads_full_csv_likely_count: 3`
- `chunking_support_count: 25`

**Net effect:**
- Reduced likely full-read candidates by **6** (9 → 3)
- **Zero high-risk candidates** in audit report
- All real-data-risk and generated-artifact-risk sites now guarded

### Fast Runtime

- Before: `117.30s`
- After: `120.65s`
- Change: **+3.35s** (policy evaluation overhead)

Policy checks add safety with minimal performance impact.

### Summary

Phase 426 achieved:

✅ Clean commit hygiene (4 commits, working tree clean)
✅ Improved audit classifier (fewer false positives)
✅ Guarded all remaining real-data-risk readers
✅ Reduced likely full-read count from 9 to 3
✅ Zero high-risk candidates remaining
✅ All tests pass (302 fast tests)

Remaining work for <90s fast validation:

- Optimize subprocess-heavy validation runner tests
- Mark expensive CLI orchestration as `integration`
- Profile and optimize top slow tests
