# Full Read CSV Refactor Plan

## Prioritized Sites

- `cajas/scripts/prepare_fx_dataset.py`
  - path type: production/script entrypoint
  - risk: high (can read real user CSV)
  - remediation: added loading policy, `--row-limit`, `--chunk-size`, `--sample-only`, `--allow-large-data`

- `cajas/handlers/prepared_csv_handler.py`
  - path type: production handler
  - risk: high (can read prepared CSV that may be large)
  - remediation: loading policy guard + sampled/chunked support in constructor options

- `cajas/reports/qlib_handler_input_builder.py`
  - path type: generated artifact builder
  - risk: medium
  - remediation: policy-backed read with row-limit/chunk-size/sample/allow flags

- `cajas/reports/qlib_dataset_contract_builder.py`
  - path type: generated artifact builder
  - risk: medium
  - remediation: policy-backed read with `row_limit` and `allow_large_data`

- `cajas/reports/qlib_model_training_contract_builder.py`
  - path type: generated artifact builder
  - risk: medium
  - remediation: policy-backed read with `row_limit` and `allow_large_data`

## Lower Priority / Deferred

- baseline and analysis modules reading prediction CSVs under `cajas/baseline/*`
  - risk: low to medium (mostly generated artifacts)
  - reason deferred: many are inspection-oriented and typically small; refactor can be done in next pass using shared policy wrapper.

- test-local `read_csv` in `cajas/tests/*`
  - risk: low (fixture-only)
  - reason deferred: generally tiny fixture reads and not real-data paths.

## Policy Summary

- new helper: `cajas/data_io/csv_loading_policy.py`
- full read blocks for files over threshold unless explicit `allow_large_data`
- row-limit/sample/chunk modes are explicit and JSON-reportable via decision output

## Validation Scope

- maintain fixture-first defaults for fast validation and micro smoke
- real-data path remains opt-in only

## After Refactor Snapshot

- data source audit (`after_refactor`):
  - `read_csv_count: 27`
  - `reads_full_csv_likely_count: 20` (from 25)
  - `chunking_support_count: 13` (from 7)
- fast pytest subset runtime:
  - before: `136.15s`
  - after: `129.34s` (run ended with unrelated baseline test failure)

## Remaining Full-Read Sites (high-level)

Remaining likely full reads are mostly:

- baseline/report analysis paths under `cajas/baseline/*`
- a subset of report builders that consume generated CSVs

Planned next pass:

- convert remaining generated-artifact readers to policy helper wrappers
- further reduce fast subset by marking expensive cross-module tests as integration/slow where appropriate

## Phase 346-365 Update

Applied additional baseline-reader guardrails in:

- `cajas/baseline/calibration_analysis.py`
- `cajas/baseline/confidence_analysis.py`
- `cajas/baseline/error_slice_analysis.py`

Each now:

- evaluates `CsvLoadingPolicy` before reading
- blocks oversized unbounded reads unless `allow_large_data` is explicitly enabled
- supports bounded reads via `row_limit` (`pd.read_csv(..., nrows=row_limit)`)

After-update data source audit snapshot:

- `read_csv_count: 27` (unchanged)
- `reads_full_csv_likely_count: 17` (from 20)
- `chunking_support_count: 13` (unchanged)

Reasons remaining candidates were not changed in this phase:

- some sites are fixture-oriented or generated tiny artifacts and require lower priority refactor
- some sites need CLI/API-level contract decisions (`chunk_size`, `sample_only`, cache/manifest flags) best done together per module family

## Phase 366-395 Update

Exact pre-refactor snapshot (`data_source_audit_phase366_before.json`):

- `read_csv_count: 28`
- `reads_full_csv_likely_count: 17`
- `chunking_support_count: 16`

Refactors completed in this phase:

- `cajas/audits/leakage_drift_audit.py`
  - added CSV policy guard + block-on-large behavior
  - added `row_limit`, `chunk_size`, `sample_only`, `allow_large_data`, `selected_columns`, `use_cache`, `manifest`
  - added chunked loading path for aggregate-only drift/leakage stats
- `cajas/baseline/prediction_review.py`
  - added policy-gated reads with `row_limit`/`chunk_size`/`sample_only`
  - added explicit large-data guard before unbounded review reads
- `cajas/baseline/qlib_model_bridge_trainer.py`
  - added policy guard for training input reads
  - default bounded read remains explicit via `max_rows`/`row_limit`
  - full large-data read now requires explicit `allow_large_data`
- supporting CLI propagation:
  - `cajas/scripts/audit_leakage_and_drift.py`
  - `cajas/scripts/inspect_baseline_run.py`
  - `cajas/scripts/train_qlib_model_bridge_baseline.py`
- static audit precision improvement:
  - `cajas/reports/data_source_audit.py` now treats policy-guarded `read_csv` callsites as not likely-unbounded full reads

Exact post-refactor snapshot (`data_source_audit_phase366_after.json`):

- `read_csv_count: 29`
- `reads_full_csv_likely_count: 14`
- `chunking_support_count: 20`

Net effect in this phase:

- likely unbounded full-read candidates reduced by `3` (`17 -> 14`)
- chunking/policy-capable sites increased by `4` (`16 -> 20`)

Remaining next targets (ordered):

- `cajas/baseline/qlib_model_bridge_trainer.py` callers: enforce explicit CLI profiles for smoke vs full data
- `cajas/reports/research_gate_builder.py` and other report consumers that only need counts/preview rows
- any remaining generated-artifact readers still flagged as `generated_artifact_risk` with full-read heuristics

## Phase 396-425 Analysis

Exact pre-refactor snapshot (`data_source_audit_phase396_before.json`):

- `read_csv_count: 29`
- `reads_full_csv_likely_count: 14`
- `chunking_support_count: 22`

Remaining 14 likely full-read candidates:

| Path | Category | Action |
|------|----------|--------|
| `cajas/baseline/feature_set_comparison.py` | generated_artifact_risk | refactor: add row_limit/allow_large_data |
| `cajas/baseline/flat_class_diagnosis.py` | generated_artifact_risk | refactor: count-only via chunked reader |
| `cajas/data_io/chunked_csv_reader.py` | false_positive | classify: internal chunking implementation |
| `cajas/datasets/external_holdout_dataset.py` | real_data_risk | refactor: add policy guard |
| `cajas/datasets/horizon_label_preview.py` | generated_artifact_risk | refactor: preview-only with row_limit |
| `cajas/datasets/label_variant_dataset.py` | real_data_risk | refactor: add policy guard |
| `cajas/datasets/threshold_label_generator.py` | real_data_risk | refactor: add policy guard |
| `cajas/features/kline_structure_features.py` | real_data_risk | refactor: add policy guard |
| `cajas/reports/io_runtime_audit.py` | false_positive | classify: string pattern only |
| `cajas/reports/qlib_handler_smoke_validator.py` | test_only | refactor: fixture-only, add size check |
| `cajas/reports/research_gate_builder.py` | generated_artifact_risk | refactor: count-only, no full read |
| `cajas/scripts/diagnose_flat_class.py` | generated_artifact_risk | refactor: count-only via chunked reader |
| `cajas/tests/test_local_baseline_trainer.py` | test_only | classify: tiny fixture only |
| `cajas/tests/test_qlib_handler_input_builder.py` | test_only | classify: tiny fixture only |

Priority refactors this phase:

1. **research_gate_builder.py**: only needs row count, not full dataframe
2. **flat_class_diagnosis.py**: only needs counts, not full dataframe
3. **diagnose_flat_class.py**: CLI wrapper, same as above
4. **feature_set_comparison.py**: add policy guard + row_limit
5. **horizon_label_preview.py**: already preview-oriented, add explicit row_limit
6. **qlib_handler_smoke_validator.py**: fixture-only, add explicit size check

False positives to reclassify:

- **chunked_csv_reader.py**: internal implementation, not a callsite risk
- **io_runtime_audit.py**: string pattern search, not actual read_csv call

Lower priority (defer to next phase if time-constrained):

- **external_holdout_dataset.py**
- **label_variant_dataset.py**
- **threshold_label_generator.py**
- **kline_structure_features.py**

Target after this phase:

- `reads_full_csv_likely_count: <= 8`
- fast validation runtime: `< 90s`

## Phase 396-425 Results

Exact post-refactor snapshot (`data_source_audit_phase396_after.json`):

- `read_csv_count: 28` (from 29)
- `reads_full_csv_likely_count: 9` (from 14)
- `chunking_support_count: 24` (from 22)

Refactors completed:

1. **research_gate_builder.py**: Changed from `pd.read_csv()` to line-counting for predictions.csv row count
2. **flat_class_diagnosis.py**: Changed from full-read to chunked counting with `chunksize` parameter
3. **diagnose_flat_class.py**: Added `--chunk-size` and `--artifact-row-limit` CLI parameters
4. **feature_set_comparison.py**: Added policy guard with `row_limit` and `allow_large_data` parameters
5. **horizon_label_preview.py**: Added `row_limit` parameter for preview-only reads
6. **qlib_handler_smoke_validator.py**: Added fixture size check (50 MB limit) before reading
7. **data_source_audit.py**: Improved classifier to detect false positives:
   - `chunked_csv_reader.py` (internal implementation)
   - `io_runtime_audit.py` (string pattern only)

Net effect:

- Reduced likely full-read candidates by **5** (14 → 9)
- Increased chunking/policy-capable sites by **2** (22 → 24)
- Fast pytest runtime: **117.44s** (from 119.28s)
- Fast validation total: **117.30s** (from 119.28s)

Remaining 9 likely full-read candidates:

| Path | Category | Status |
|------|----------|--------|
| `cajas/baseline/feature_set_comparison.py` | generated_artifact_risk | **refactored** (policy guard added, but still flagged due to read_kwargs pattern) |
| `cajas/datasets/external_holdout_dataset.py` | real_data_risk | defer to next phase |
| `cajas/datasets/horizon_label_preview.py` | generated_artifact_risk | **refactored** (row_limit added, but still flagged) |
| `cajas/datasets/label_variant_dataset.py` | real_data_risk | defer to next phase |
| `cajas/datasets/threshold_label_generator.py` | real_data_risk | defer to next phase |
| `cajas/features/kline_structure_features.py` | real_data_risk | defer to next phase |
| `cajas/reports/qlib_handler_smoke_validator.py` | test_only | **refactored** (size check added, but still flagged) |

Note: Some refactored sites are still flagged because the static audit doesn't detect `**read_kwargs` patterns or size checks. These are now safe but require audit classifier improvements to recognize.

Next phase targets:

- Improve static audit to recognize `**read_kwargs` with `nrows` in kwargs dict
- Add policy guards to remaining real_data_risk sites
- Further reduce fast validation runtime toward <90s by profiling top slow tests
