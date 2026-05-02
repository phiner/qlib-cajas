# Phase 746–775 Prompt: Dataset Quality Loop + Chunked Feature Research Readiness

You are working on branch:

- `phase-post-merge-research-next`

## Objective

Implement a bounded offline research phase focused on:

1. dataset quality reporting
2. label coverage and imbalance diagnostics
3. time-range/session coverage diagnostics
4. chunked feature extraction dry-run reporting
5. feature schema manifest generation
6. offline-only research queue summary
7. tiny fixtures and bounded tests

Do not introduce heavy training defaults or any trading execution features.

## Scope

### A. Dataset quality report builder

- Add/extend a report module and CLI to summarize:
  - row count
  - column completeness
  - null/invalid label checks
  - instrument/session consistency
- Use bounded/metadata-first reads where feasible.

### B. Label coverage and imbalance diagnostics

- Add class distribution checks for key label columns.
- Add imbalance warnings with configurable thresholds.
- Keep output classification-only and non-trading.

### C. Time-range/session coverage diagnostics

- Report temporal coverage:
  - earliest/latest timestamp
  - gaps or suspicious jumps
  - per-session/day coverage summaries

### D. Chunked feature extraction dry-run report

- Add a chunked dry-run mode that reports:
  - selected columns
  - chunk sizes
  - throughput summary
  - schema consistency per chunk
- No full heavy pipeline execution by default.

### E. Feature schema manifest

- Emit a compact schema manifest JSON/MD:
  - feature name
  - dtype
  - source stage
  - optional description/tag

### F. Offline research queue summary

- Add a small queue summary artifact for pending dataset QA and feature tasks.
- Keep this strictly offline/research-only.

## Boundaries

Do not:

- modify Qlib core for execution features
- add broker/live/paper execution
- add order generation/routing
- add position sizing
- add PnL optimization
- add execution simulation
- add network services

All validation remains CPU-only and local.

## Validation Targets

Run bounded checks:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/validation-runtime-audit/fast_validation_phase746.json
```

Optional if touched:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_phase746.json --out-md tmp/data-io-audit/data_source_audit_phase746.md
```

## Expected Deliverables

- dataset quality report module + CLI
- label imbalance diagnostics
- time coverage diagnostics
- chunked feature dry-run report
- feature schema manifest
- offline research queue summary
- small fixtures/tests
- updated docs and command examples
