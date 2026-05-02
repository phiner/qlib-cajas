# Merge Gate Checklist

## Required Before Merge

```bash
git status --short
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_merge_gate.json --out-md tmp/data-io-audit/data_source_audit_merge_gate.md
```

## Optional Before Merge

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests -m "integration and not slow and not smoke"
```

## Do Not Require By Default

- closure smoke
- full smoke
- heavy real-data scans
- full CSV hashing
- full row count on multi-GB files

## Merge Blockers

- dirty working tree
- fast validation failure
- micro smoke failure
- new high-risk data-source audit finding
- any broker/live/paper/order/PnL execution code
