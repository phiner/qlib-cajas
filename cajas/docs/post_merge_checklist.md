# Post-Merge Checklist

## Merge and Verify

```bash
git checkout <target-main-branch>
git pull
git merge phase-next-mega-logic
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_post_merge.json --out-md tmp/data-io-audit/data_source_audit_post_merge.md
```

## Rollback Notes (Conflict Before Merge Commit)

```bash
git status
git log --oneline -5
git merge --abort
```
