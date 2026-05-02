# Post-Merge Next Workstream Plan

## Current Baseline

- branch: `phase-post-merge-research-next`
- latest main commit baseline: `a67b2a25` (with follow-up sanity/baseline work merged)
- fast validation runtime:
  - `pytest_fast`: `89.63s`
  - total: `93.03s`
- micro smoke runtime:
  - `11.53s`
- data-source audit:
  - `reads_full_csv_likely_count = 2`
  - no high-risk findings

Validation commands:

- `./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast`
- `./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro`
- `./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_phase726.json --out-md tmp/data-io-audit/data_source_audit_phase726.md`

## Candidate Next Workstreams

### Option 1 - Research Dataset Quality Loop

Focus:

- label/data QA tightening
- review queue summaries
- dataset coverage diagnostics
- drift/imbalance checks
- no model expansion required

Why safe:

- offline research only
- improves data confidence
- no trading execution scope

### Option 2 - Feature Engineering Research Lane

Focus:

- extra K-line/FX structure features
- chunked feature extraction flow
- large CSV readiness
- feature-set comparison reports

Why safe:

- offline-only
- directly builds on existing data-I/O guardrails
- bounded with row limits/chunking

### Option 3 - Model Evaluation/Reporting Lane

Focus:

- stronger baseline evaluation reports
- calibration/error-slice refinements
- run comparison summaries
- no heavier training defaults

Why safe:

- improves interpretability from existing artifacts
- no execution behavior change

### Option 4 - Developer Productivity Lane

Focus:

- more CLI tests converted to in-process
- keep fast validation stable below 90s when possible
- fixture cleanup
- runtime audit improvements

Why safe:

- maintenance-only improvements
- no research logic or execution scope changes

## Recommended Next Choice

Recommended direction:

`Option 1 + Option 2 (lightly combined): Dataset quality loop + chunked feature research readiness`

Reason:

- data-I/O foundation and guardrails are in place
- future multi-GB data readiness benefits from chunked-first tooling
- better dataset quality confidence should precede heavier model work
- remains clearly offline and non-execution

## Explicit Non-Goals

- broker integration
- live trading
- paper trading execution
- order generation/routing
- position sizing
- PnL optimization
- execution simulation
