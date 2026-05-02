# Phase 666–685 Prompt: Merge Rehearsal + Post-Merge Validation Baseline

You are working on branch:

- `phase-next-mega-logic`

## Current state

Phase 646–665 completed.

Latest completed work:

- Verified branch state and final docs presence.
- Ran merge-gate lightweight validation once.
- Added final mainline handoff and post-merge checklist docs.
- Updated references.

Latest validation:

```text
PASS run_fast_validation.py --tier fast
  total: 90.376s
  pytest_fast: 87.386s

PASS run_smoke_validation.py --tier micro
  micro smoke: 10.90s

PASS audit_data_sources.py
  reads_full_csv_likely_count = 2
  high-risk findings effectively 0
```

Latest docs:

- `cajas/docs/mainline_handoff_note.md`
- `cajas/docs/post_merge_checklist.md`
- `cajas/docs/final_research_stack_index.md`
- `cajas/docs/pr_readiness_checklist.md`

Current issue:

- Commit was blocked by approval-service `503`.
- Staged changes are ready.
- User should manually run:

```bash
git commit -m "docs: add post-push mainline handoff checklist"
git push origin phase-next-mega-logic
```

## Phase objective

Implement **Merge Rehearsal + Post-Merge Validation Baseline**.

This phase is only for merge-readiness verification and post-merge validation planning.

Primary goals:

1. Confirm the Phase 646 handoff commit exists.
2. Confirm branch is pushed or ready to push.
3. Perform a local merge rehearsal into the intended target branch if the user confirms or the target branch is obvious.
4. Run post-merge lightweight validation commands.
5. Create/update a post-merge validation baseline note.
6. Do not add new features.
7. Preserve all research-only/no-execution boundaries.

## Important merge target handling

Start by identifying likely target branch:

```bash
git branch --show-current
git branch --list
git remote -v
```

If target branch is obvious from project convention, use it. If not obvious, stop and ask the user which branch to merge into.

Likely candidates might be:

- `cajas/market-recognition-phase-0`
- `main`
- `master`

Do not guess destructively.

Prefer a non-destructive rehearsal:

```bash
git checkout <target-branch>
git pull --ff-only
git merge --no-commit --no-ff phase-next-mega-logic
```

Then run checks. If successful, abort rehearsal unless the user explicitly asked to complete merge:

```bash
git merge --abort
```

If user explicitly wants final merge, complete it only after validation passes.

## Non-negotiable boundaries

Do not:

- Modify Qlib core for new features.
- Add broker/live/paper execution.
- Add order generation/routing.
- Add position sizing.
- Add PnL optimization.
- Add execution simulation.
- Add network calls except normal git pull/push if explicitly part of merge workflow.
- Add GPU/CUDA requirements.
- Add files named `init.py`.

All validation remains:

- CPU-only
- local
- deterministic where feasible
- no trading execution

---

# Part A — Confirm commit/push state

Run:

```bash
git branch --show-current
git status --short
git log --oneline -8
```

If staged files remain:

```bash
git commit -m "docs: add post-push mainline handoff checklist"
```

If commit succeeds:

```bash
git status --short
```

If push has not happened and user has allowed pushing, push:

```bash
git push origin phase-next-mega-logic
```

If push is not allowed from Codex, report manual push command.

---

# Part B — Verify final docs exist

Run:

```bash
test -f cajas/docs/mainline_handoff_note.md
test -f cajas/docs/post_merge_checklist.md
test -f cajas/docs/pr_description_phase_next_mega_logic.md
test -f cajas/docs/merge_gate_checklist.md
test -f cajas/docs/pr_readiness_checklist.md
test -f cajas/docs/final_phase_archive_index.md
test -f cajas/docs/final_research_stack_index.md
```

Report missing files if any.

---

# Part C — Merge rehearsal

Only proceed if target branch is known.

Suggested non-destructive rehearsal:

```bash
git checkout <target-branch>
git pull --ff-only
git merge --no-commit --no-ff phase-next-mega-logic
```

If conflicts occur:

- stop
- record conflict files
- do not resolve automatically unless trivial and clearly within docs
- run:

```bash
git merge --abort
```

If merge applies cleanly, run Part D validation.

After validation, unless explicitly instructed to complete merge:

```bash
git merge --abort
git checkout phase-next-mega-logic
```

---

# Part D — Post-merge lightweight validation baseline

Run on the merge-rehearsed tree:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/validation-runtime-audit/fast_validation_merge_rehearsal.json
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_merge_rehearsal.json --out-md tmp/data-io-audit/data_source_audit_merge_rehearsal.md
```

Expected:

- fast validation passes
- micro smoke passes
- data-source audit has no high-risk regressions
- `reads_full_csv_likely_count` remains low, ideally `<= 2`

Do not run closure/full smoke unless explicitly requested.

---

# Part E — Post-merge validation baseline note

Create or update:

- `cajas/docs/post_merge_validation_baseline.md`

Include:

## Branches

- source branch
- target branch
- rehearsal status

## Validation results

- fast validation runtime
- micro smoke runtime
- data-source audit result

## Expected post-merge commands

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_post_merge.json --out-md tmp/data-io-audit/data_source_audit_post_merge.md
```

## Boundaries

- no broker
- no live trading
- no paper execution
- no order routing
- no position sizing
- no PnL optimization
- no execution simulation

## Remaining risks

- fast runtime can vary around 90s
- closure/full smoke is expensive
- real data full reads require explicit flags

---

# Part F — Update references

If `post_merge_validation_baseline.md` is created, update:

- `cajas/docs/post_merge_checklist.md`
- `cajas/docs/final_research_stack_index.md`
- `tasks/phase_666_685_merge_rehearsal_post_merge_validation_prompt.md`

Add links to:

- `cajas/docs/post_merge_validation_baseline.md`

---

# Part G — Commit guidance

If docs are added/updated:

```bash
git add cajas/docs/post_merge_validation_baseline.md \
        cajas/docs/post_merge_checklist.md \
        cajas/docs/final_research_stack_index.md \
        tasks/phase_666_685_merge_rehearsal_post_merge_validation_prompt.md

git commit -m "docs: add post-merge validation baseline"
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
- Source branch/status
- Target branch/rehearsal status
- Files changed
- Validation results
- Runtime summary
- Data-source audit summary
- Conflict status
- Post-merge baseline path
- Git commits or manual commands
- Final status
- Manual push command

Do not push from Codex unless explicitly instructed.

Completion reference:

- expected sanity baseline doc from this phase:
  - `cajas/docs/post_github_merge_sanity_report.md`
