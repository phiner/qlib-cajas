# Post GitHub Merge Sanity Report

## Merge Status

- target branch: `main`
- source branch: `phase-next-mega-logic`
- local main commit: `2d846fc2`
- expected docs present:
  - `cajas/docs/pr_description_phase_next_mega_logic.md`
  - `cajas/docs/merge_gate_checklist.md`
  - `cajas/docs/mainline_handoff_note.md`
  - `cajas/docs/post_merge_checklist.md`
  - `cajas/docs/final_research_stack_index.md`

## Validation Results

- fast validation: pass
  - `pytest_fast`: `92.50s`
  - total: `96.65s`
- micro smoke: pass
  - `13.75s`
- data-source audit: pass
  - `reads_full_csv_likely_count = 2`
  - high-risk findings remain effectively `0`

## Commands Run

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/validation-runtime-audit/fast_validation_post_github_merge.json
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_post_github_merge.json --out-md tmp/data-io-audit/data_source_audit_post_github_merge.md
```

## Boundaries Confirmed

Merged mainline still does not add:

- broker/live/paper execution
- order generation/routing
- position sizing
- PnL optimization
- execution simulation

## Recommended Next Branch

```bash
git checkout -b phase-post-merge-research-next
```
