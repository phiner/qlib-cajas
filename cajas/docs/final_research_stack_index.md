# Final Research Stack Index

## Research Stack Status

- Research-gate and readiness flow are offline-only.
- Final readiness and research-only approval remain human-review surfaces.
- No broker/live/paper execution path is included in this repository workflow.

## Validation Workflow

- Fast validation:
  - `./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast`
- Quick validation:
  - `./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier quick`
- Micro smoke:
  - `./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro`
- Minimal smoke:
  - `./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier minimal --out-root tmp/smoke-validation-minimal`
- Closure/full smoke (intentionally expensive):
  - `./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier closure --out-root tmp/smoke-validation-closure`
  - `./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier full --out-root tmp/smoke-validation-full`

When to run:

- Tight edit loop: quick
- Pre-commit/default check: fast
- Handoff or merge sanity: micro
- Release-style check: closure/full

## Data I/O Workflow

- Data-source audit:
  - `cajas/scripts/audit_data_sources.py`
- Validation runtime / I/O audits:
  - `cajas/scripts/audit_validation_runtime.py`
  - `cajas/scripts/audit_io_runtime.py`
- Large CSV metadata:
  - `cajas/scripts/inspect_large_csv.py`
- Dataset manifest/cache/index:
  - `cajas/scripts/build_dataset_file_manifest.py`
  - `cajas/scripts/build_dataset_cache_index.py`
  - `cajas/scripts/convert_csv_to_columnar_cache.py`
- Chunked read utilities:
  - `cajas/data_io/chunked_csv_reader.py`

Real-data access rules:

- fast validation defaults to fixture/static paths
- real-data flows are explicit and guarded
- unbounded large-file reads require policy acknowledgement

## Current Recommended Commands

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_latest.json --out-md tmp/data-io-audit/data_source_audit_latest.md
```

## Remaining Known Risks

- Fast-tier runtime still has normal timing variance.
- Some low-risk full-read candidates may remain as audit false positives.
- Integration/slow tests are explicit and intentionally excluded from fast tier.
- Closure/full smoke remains intentionally expensive.

## Release Readiness Docs

- `cajas/docs/pr_readiness_checklist.md`
- `cajas/docs/final_phase_archive_index.md`
- `cajas/docs/pr_description_phase_next_mega_logic.md`
- `cajas/docs/merge_gate_checklist.md`
- `cajas/docs/mainline_handoff_note.md`
- `cajas/docs/post_merge_checklist.md`
- `cajas/docs/post_github_merge_sanity_report.md`
- `cajas/docs/post_merge_next_workstream_plan.md`

## Next Phase Prompt

- `tasks/phase_746_775_dataset_quality_feature_research_prompt.md`
