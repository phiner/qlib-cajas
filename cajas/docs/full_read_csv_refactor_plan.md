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
