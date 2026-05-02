# Phase 626–645 Prompt: Final Manual Commit, Push, PR Description, and Merge Gate

You are working on branch:

- `phase-next-mega-logic`

## Current state

Phase 606–625 completed successfully, but commit creation was blocked by approval-service:

```text
503 Service Unavailable
```

Latest status from Phase 606–625:

- Final PR-readiness docs added.
- Final archive index added.
- Final research stack index updated.
- README references updated.
- Lightweight final validation passed.

Latest validation:

```text
PASS run_fast_validation.py --tier fast
  pytest_fast: 82.90s
  total: 86.03s

PASS run_smoke_validation.py --tier micro
  micro smoke: 10.79s

PASS audit_data_sources.py
  reads_full_csv_likely_count = 2
  no high-risk regression
```

Final docs/index paths:

- `cajas/docs/pr_readiness_checklist.md`
- `cajas/docs/final_phase_archive_index.md`
- `cajas/docs/final_research_stack_index.md`
- `tmp/validation-delivery/validation_delivery_packet.json`
- `tmp/validation-delivery/validation_delivery_packet.md`

Known remaining risks:

- Fast total can vary by environment, but latest run is under 90s.
- CLI/report tests remain the main slow-duration cluster.
- Closure/full smoke remains intentionally expensive.
- Commit is pending manual execution because of platform `503`.

## Phase objective

Implement **Final Manual Commit, Push, PR Description, and Merge Gate**.

This is a final handoff/merge phase. Do not add new features.

Primary goals:

1. Verify current staged/unstaged state.
2. Provide exact manual commit commands if platform commit is still blocked.
3. Generate a PR description / merge summary.
4. Generate a merge gate checklist.
5. Run only lightweight final checks if needed.
6. Prepare branch for push and PR.

## Non-negotiable boundaries

Do not:

- Modify Qlib core.
- Add broker/live/paper execution.
- Add order generation/routing.
- Add position sizing.
- Add PnL optimization.
- Add execution simulation.
- Add network calls.
- Add GPU/CUDA requirements.
- Add files named `init.py`.

All validation remains:

- CPU-only
- local
- deterministic where feasible
- no network
- no trading execution

---

# Part A — Inspect status and commit manually if possible

Start with:

```bash
git branch --show-current
git status --short
git diff --cached --name-only
git diff --name-only
git diff --check
```

If files are staged and ready, commit the staged delivery/readiness files:

```bash
git commit -m "docs: add final validation delivery readiness pack"
```

Then add current phase docs/prompt if present:

```bash
git add cajas/docs/pr_readiness_checklist.md \
        cajas/docs/final_phase_archive_index.md \
        cajas/docs/final_research_stack_index.md \
        cajas/README.md \
        tasks/phase_606_625_final_archive_pr_readiness_prompt.md
```

Then commit:

```bash
git commit -m "docs: add final PR readiness and phase archive index"
```

If commit is blocked again by `503`, stop and report exact manual commands. Do not retry repeatedly.

---

# Part B — Create PR description

Create:

- `cajas/docs/pr_description_phase_next_mega_logic.md`

The PR description should be concise but comprehensive.

Include:

## Summary

- Research-only stack hardening
- Validation runtime optimization
- Data I/O large CSV readiness
- Fast/micro/closure/full validation tiers
- Final readiness/delivery docs

## Key outcomes

Use current known values:

```text
run_fast_validation.py --tier fast: ~86s latest run
run_smoke_validation.py --tier micro: ~11s latest run
reads_full_csv_likely_count: 2
high-risk data-source candidates: 0
```

## Major areas changed

- governance/research-only approval
- reproducibility/readiness reports
- validation runtime scripts
- smoke tier architecture
- data source audit
- large CSV metadata and chunked reader
- CSV loading policy
- final docs and checklists

## Validation

List commands:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_phase606.json --out-md tmp/data-io-audit/data_source_audit_phase606.md
```

## Explicit non-goals

- no broker
- no live trading
- no paper execution
- no order generation
- no order routing
- no position sizing
- no PnL optimization
- no execution simulation

## Known residual risks

- fast validation variance
- CLI/report tests still dominate slow slots
- closure/full smoke intentionally expensive
- real-data full reads require explicit flags

---

# Part C — Create merge gate checklist

Create or update:

- `cajas/docs/merge_gate_checklist.md`

Include:

## Required before merge

```bash
git status --short
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_merge_gate.json --out-md tmp/data-io-audit/data_source_audit_merge_gate.md
```

## Optional before merge

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests -m "integration and not slow and not smoke"
```

## Do not require by default

- closure smoke
- full smoke
- heavy real-data scans
- full CSV hashing
- full row count on multi-GB files

## Merge blockers

- dirty working tree
- fast validation failure
- micro smoke failure
- new high-risk data-source audit finding
- any broker/live/paper/order/PnL execution code

---

# Part D — Lightweight final validation

Run only if needed:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/validation-runtime-audit/fast_validation_phase626.json
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_phase626.json --out-md tmp/data-io-audit/data_source_audit_phase626.md
```

Do not run closure/full smoke unless explicitly requested.

---

# Part E — Update references

Update if needed:

- `cajas/README.md`
- `cajas/docs/final_research_stack_index.md`
- `cajas/docs/pr_readiness_checklist.md`
- `tasks/phase_626_645_final_pr_merge_gate_prompt.md`

Add references to:

- `cajas/docs/pr_description_phase_next_mega_logic.md`
- `cajas/docs/merge_gate_checklist.md`

Do not duplicate large content.

---

# Part F — Commit guidance

If files were added/updated:

```bash
git add cajas/docs/pr_description_phase_next_mega_logic.md \
        cajas/docs/merge_gate_checklist.md \
        cajas/docs/pr_readiness_checklist.md \
        cajas/docs/final_research_stack_index.md \
        cajas/README.md \
        tasks/phase_626_645_final_pr_merge_gate_prompt.md

git commit -m "docs: add final PR description and merge gate checklist"
```

If commit is blocked by `503`, stop and report manual commands.

Final push:

```bash
git push origin phase-next-mega-logic
```

---

# Final response expected from Codex

Return compact summary:

- Summary
- Branch/status
- Files changed
- Validation results
- Runtime summary
- Data-source audit summary
- PR description path
- Merge checklist path
- Git commits or manual commit commands
- Final status
- Manual push command

Do not push from Codex unless explicitly instructed.

Completion reference:

- expected merge-gate docs from this phase:
  - `cajas/docs/pr_description_phase_next_mega_logic.md`
  - `cajas/docs/merge_gate_checklist.md`
