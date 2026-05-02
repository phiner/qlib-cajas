# PR Readiness Checklist

## Validation Baseline Commands

- Fast validation:
  - `./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast`
- Micro smoke:
  - `./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro`
- Data-source audit:
  - `./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_final.json --out-md tmp/data-io-audit/data_source_audit_final.md`
- Validation delivery packet:
  - `./.venv-qlib313/bin/python cajas/scripts/build_validation_delivery_packet.py --fast-timing tmp/validation-runtime-audit/fast_validation_phase606.json --data-source-audit tmp/data-io-audit/data_source_audit_phase606.json --runtime-audit tmp/validation-runtime-audit/validation_runtime_phase606.json --out-json tmp/validation-delivery/validation_delivery_packet.json --out-md tmp/validation-delivery/validation_delivery_packet.md --allow-missing-inputs`

## Current Expected Metrics

- fast subset runtime: about `80-90s`
- `run_fast_validation.py --tier fast`: about `90-95s` total
- micro smoke: about `10-15s`
- `reads_full_csv_likely_count`: `2`
- high-risk data-source candidates: `0`

## Must Pass Before Merge

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_final.json --out-md tmp/data-io-audit/data_source_audit_final.md
```

## Explicit Non-Goals

- no broker
- no live trading
- no paper execution
- no orders
- no PnL optimization
- no position sizing
- no execution simulation

## Known Residual Risks

- fast total can hover around `90-95s` due to fixed hygiene overhead
- CLI/report tests still dominate slow duration slots
- closure/full smoke tiers remain intentionally expensive
- real-data full reads require explicit flags

## Reference Docs

- `cajas/docs/pr_description_phase_next_mega_logic.md`
- `cajas/docs/merge_gate_checklist.md`
- `cajas/docs/mainline_handoff_note.md`
- `cajas/docs/post_merge_checklist.md`
