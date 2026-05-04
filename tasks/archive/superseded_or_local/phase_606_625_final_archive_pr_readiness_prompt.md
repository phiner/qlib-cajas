# Phase 606–625 Prompt: Final Archive, PR Readiness, and Merge Checklist

You are working on branch:

- `phase-next-mega-logic`

## Current state

Phase 586–605 completed bounded validation.

Latest status:

```text
Branch: phase-next-mega-logic

fast subset pytest:
  306 passed, 15 deselected in 88.22s

run_fast_validation.py --tier fast:
  pytest_fast: 88.30s
  total: 91.73s

micro smoke:
  12.62s

data-source audit:
  reads_full_csv_likely_count = 2
  no high-risk regression

validation delivery packet:
  tmp/validation-delivery/validation_delivery_packet.json
  tmp/validation-delivery/validation_delivery_packet.md
```

Commit was still blocked by approval-service `503`.

Manual commit/push commands from previous phase:

```bash
git commit -m "docs: add final validation delivery readiness pack"
git add tasks/phase_586_605_final_fast_overhead_trim_prompt.md
git commit -m "docs: add final fast overhead trim phase prompt"
git push origin phase-next-mega-logic
```

Important:

- The user may have already run these commands manually.
- Start by checking git status.
- If working tree is clean and branch is pushed or ready to push, do not create unnecessary changes.

## Phase objective

Implement **Final Archive, PR Readiness, and Merge Checklist**.

This is a final packaging and merge-preparation phase.

Primary goals:

1. Verify final branch status.
2. Ensure delivery artifacts and docs are discoverable.
3. Create a concise PR/merge checklist.
4. Create a final phase archive index.
5. Avoid further runtime-chasing unless validation regressed.
6. Keep all research-only/no-execution boundaries explicit.
7. Produce a push/PR-ready final state.

This phase should be small.

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

# Part A — Verify current git state

Run:

```bash
git branch --show-current
git status --short
git log --oneline -12
```

Cases:

## A1. Working tree clean

If clean:

- Do not modify code unless a doc/index gap is obvious.
- Run final lightweight verification from Part D.
- Produce final report.

## A2. Only Phase 586 files pending

If the delivery files are still staged/uncommitted, commit them using:

```bash
git commit -m "docs: add final validation delivery readiness pack"
git add tasks/phase_586_605_final_fast_overhead_trim_prompt.md
git commit -m "docs: add final fast overhead trim phase prompt"
```

If commit is blocked again by `503`, stop commit attempts and report exact manual commands.

## A3. Unexpected dirty files

If unrelated dirty files exist:

- Do not revert.
- List them.
- Ask user to decide or keep phase work separate.
- Do not mix unrelated changes into final archive commit.

---

# Part B — Final PR readiness checklist

Create or update:

- `cajas/docs/pr_readiness_checklist.md`

Keep it concise and actionable.

Include:

## Validation baseline

- fast validation command
- micro smoke command
- data-source audit command
- validation delivery packet command

## Current expected metrics

Use latest known values or current validation results:

```text
fast subset: ~80–90s
run_fast_validation --tier fast: ~90–95s total
micro smoke: ~10–15s
reads_full_csv_likely_count: 2
high-risk data-source candidates: 0
```

## Must-pass before merge

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_final.json --out-md tmp/data-io-audit/data_source_audit_final.md
```

## Explicit non-goals

- no broker
- no live trading
- no paper execution
- no orders
- no PnL optimization
- no position sizing
- no execution simulation

## Known residual risks

- fast total may hover around 90–95s due to fixed hygiene overhead
- some CLI/report tests still dominate slow list
- closure/full smoke remains intentionally expensive
- real data full reads require explicit flags

---

# Part C — Final phase archive index

Create or update:

- `cajas/docs/final_phase_archive_index.md`

This should index the important phase prompt files and final docs.

Include:

## Major prompt phases

- Phase 216–235 governance review closure
- Phase 236–275 validation runtime optimization
- Phase 276–315 data I/O optimization
- Phase 316–345 full-read CSV refactor
- Phase 346–365 baseline runtime CSV closure
- Phase 366–395 remaining full-read runtime
- Phase 396–425 generated artifact reader runtime
- Phase 426–455 commit hygiene/full-read/fast runtime
- Phase 456–485 subprocess hotspot
- Phase 486–515 under-90 fast validation
- Phase 546–565 validation delivery
- Phase 566–585 final validation delivery
- Phase 586–605 final fast overhead trim

## Final docs

- `cajas/docs/final_research_stack_index.md`
- `cajas/docs/future_work_checklist.md`
- `cajas/docs/pr_readiness_checklist.md`
- `cajas/docs/test_runtime_optimization_notes.md`
- `cajas/docs/data_io_optimization_notes.md`
- `cajas/docs/full_read_csv_refactor_plan.md`
- `cajas/docs/qlib_integration_notes.md`

## Final generated delivery artifacts

- `tmp/validation-delivery/validation_delivery_packet.json`
- `tmp/validation-delivery/validation_delivery_packet.md`

---

# Part D — Final lightweight validation

Run:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/validation-runtime-audit/fast_validation_phase606.json
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_phase606.json --out-md tmp/data-io-audit/data_source_audit_phase606.md
```

Do not run closure/full smoke unless explicitly requested.

If validation exceeds a few minutes, stop and report the bottleneck.

---

# Part E — Update references

If new docs were added, update:

- `cajas/README.md`
- `cajas/docs/final_research_stack_index.md`
- `tasks/phase_606_625_final_archive_pr_readiness_prompt.md`

Add links to:

- `cajas/docs/pr_readiness_checklist.md`
- `cajas/docs/final_phase_archive_index.md`

Do not duplicate large content.

---

# Part F — Commit guidance

If files were created/updated:

```bash
git add cajas/docs/pr_readiness_checklist.md \
        cajas/docs/final_phase_archive_index.md \
        cajas/docs/final_research_stack_index.md \
        cajas/README.md \
        tasks/phase_606_625_final_archive_pr_readiness_prompt.md

git commit -m "docs: add final PR readiness and phase archive index"
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
- Final docs/index paths
- Git commits
- Remaining risks
- Final status
- Manual push command

Do not push from Codex unless explicitly instructed.

Completion reference:

- final checklist/index docs expected from this phase:
  - `cajas/docs/pr_readiness_checklist.md`
  - `cajas/docs/final_phase_archive_index.md`
