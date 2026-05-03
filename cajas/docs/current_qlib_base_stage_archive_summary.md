# Current Qlib Base Stage Archive - Summary

**Version:** 1.0  
**Date:** 2026-05-02  
**Branch:** `phase-post-merge-research-next`

## Executive Summary

- **Mainline:** Qlib-based research platform with dataset quality validation pipeline
- **Core:** Schema contracts, golden fixtures, drift detection, CI guardrails
- **Status:** Fast validation ~85s, contract validation passing, data-source audit stable
- **Scope:** Research infrastructure only, not trading execution
- **Excluded:** Manual annotation, old Rust trading, broker adapters, live trading

## Key Components

1. **Dataset Quality Pipeline** - Quality scoring, label/time/feature diagnostics
2. **Schema Contracts** - Required field validation, type checking, breaking change detection
3. **Golden Fixtures** - 7 shape files for regression testing
4. **Drift Detection** - Breaking vs additive classification, reviewer-friendly reports
5. **Integrated Validation** - Contract validation in smoke, fast tier ~85s

## Validation Status

- Contract tests: 17 passed in 1.90s
- Dataset quality tests: 22 passed in 8.09s
- Fast validation: 327 passed in 85.39s
- Data-source audit: read_csv_count=29 (stable)
- Drift summary: 0 breaking, 0 additive (current smoke)

## Engineering Boundaries

- ❌ No trading execution, broker adapters, order generation
- ❌ No model performance claims from quality scores
- ❌ No production deployment
- ✅ Qlib core unchanged, all work in `cajas/` layer
- ✅ Bounded reads by default, explicit flags for large data

## Current Risks

- Schema contracts are shape-only (depth 4)
- Golden fixtures may need scenario expansion
- No semantic drift detection
- No trend analysis across runs
- Fast validation runtime increased slightly

## Recommended Next Phases

1. **Phase 956-985:** Enhanced drift semantics and trend tracking
2. **Phase 986-1015:** Golden fixture scenario expansion
3. **Phase 1016-1045:** Qlib experiment reproducibility strengthening
4. **Phase 1046-1075:** Runtime budget enforcement and test optimization
5. **Phase 1076-1105:** Reviewer report enhancements (diffs and trends)

## Key Files

- `cajas/reports/dataset_quality_research.py` - Core report generation
- `cajas/reports/dataset_quality_schema_contract.py` - Contract validation
- `cajas/scripts/run_dataset_quality_smoke.py` - Integrated smoke workflow
- `cajas/data_examples/golden/dataset_quality/` - Golden shape fixtures (7 files)
- `cajas/tests/test_dataset_quality_schema_contract.py` - Contract tests

## Quick Commands

```bash
# Run dataset quality smoke
python cajas/scripts/run_dataset_quality_smoke.py --out-root tmp/dataset-quality-smoke

# Run contract tests
pytest cajas/tests/test_dataset_quality_schema_contract.py -q

# Run fast validation
python cajas/scripts/run_fast_validation.py --tier fast

# Audit data sources
python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /path/to/data --out-json tmp/audit.json --out-md tmp/audit.md
```

## Historical Routes Excluded

- Manual K-line annotation system
- Old Rust trading system (cajasTrading)
- Trading execution infrastructure
- ML label learning loop

These are historical only, not part of current active mainline.
