# PR Description: phase-next-mega-logic

## Summary

- Research-only stack hardening and governance workflow closure.
- Validation runtime optimization across fast/micro/closure/full tiers.
- Data I/O large-CSV readiness and full-read risk reduction.
- Final readiness, delivery, and merge-oriented documentation pack.

## Key Outcomes

- `run_fast_validation.py --tier fast`: about `86s` in latest stable run (`phase606`)
- `run_smoke_validation.py --tier micro`: about `11s` in latest stable run
- `reads_full_csv_likely_count`: `2`
- high-risk data-source candidates: `0`

## Major Areas Changed

- governance and research-only approval workflow
- reproducibility/readiness report pipeline
- validation runtime scripts and tiered orchestration
- smoke-tier architecture and marker policy
- data source auditing
- large CSV metadata + chunked reader path
- CSV loading policy guards
- final delivery/readiness docs and checklists

## Validation

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_phase606.json --out-md tmp/data-io-audit/data_source_audit_phase606.md
```

## Explicit Non-Goals

- no broker integration
- no live trading
- no paper execution
- no order generation
- no order routing
- no position sizing
- no PnL optimization
- no execution simulation

## Known Residual Risks

- fast validation runtime has normal environment variance
- CLI/report tests still dominate top slow-duration slots
- closure/full smoke remains intentionally expensive
- real-data full reads require explicit policy flags
