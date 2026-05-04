# Phase 706–725 Prompt: Post-GitHub-Merge Main Sanity Check + Next Branch Baseline

You are working after the GitHub PR/merge has been completed.

## Current state

The user has completed the GitHub operation.

Assumption:

- `phase-next-mega-logic` has been merged into `main` on GitHub.
- Local repository may still be on an old branch or stale local `main`.
- This phase should verify the merged `main` baseline locally.
- Do not continue feature work on `phase-next-mega-logic`.

## Phase objective

Implement **Post-GitHub-Merge Main Sanity Check + Next Branch Baseline**.

Primary goals:

1. Switch to local `main`.
2. Pull latest `main`.
3. Confirm the GitHub merge commit or merged branch content is present.
4. Run the lightweight post-merge validation trio on `main`.
5. Confirm docs/index/checklists exist on `main`.
6. Confirm data-source audit remains stable.
7. Create a short post-merge sanity report.
8. Prepare guidance for the next development branch.

This is a verification phase, not a feature phase.

## Non-negotiable boundaries

Do not:

- Modify Qlib core.
- Add broker/live/paper execution.
- Add order generation/routing.
- Add position sizing.
- Add PnL optimization.
- Add execution simulation.
- Add network calls other than normal git pull/fetch.
- Add GPU/CUDA requirements.
- Add files named `init.py`.

All validation remains:

- CPU-only
- local
- deterministic where feasible
- no trading execution

---

# Part A — Sync local main

Run:

```bash
git branch --show-current
git status --short
```

If current working tree is dirty:

- Stop and report the dirty files.
- Do not switch branches until user confirms.

If clean:

```bash
git checkout main
git pull --ff-only
git log --oneline -10
```

Confirm that the merge content is present.

Look for docs such as:

```bash
test -f cajas/docs/pr_description_phase_next_mega_logic.md
test -f cajas/docs/merge_gate_checklist.md
test -f cajas/docs/mainline_handoff_note.md
test -f cajas/docs/post_merge_checklist.md
test -f cajas/docs/final_research_stack_index.md
```

If any are missing, report exactly which.

---

# Part B — Run post-merge lightweight validation on main

Run:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/validation-runtime-audit/fast_validation_post_github_merge.json

./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro

./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py \
  --project-root cajas \
  --data-root /home/phiner/projects/research/data \
  --out-json tmp/data-io-audit/data_source_audit_post_github_merge.json \
  --out-md tmp/data-io-audit/data_source_audit_post_github_merge.md
```

Expected:

- fast validation passes
- micro smoke passes
- data-source audit has no high-risk regression
- `reads_full_csv_likely_count` remains low, ideally `<= 2`

Do not run closure/full smoke unless explicitly requested.

If a command exceeds a few minutes, stop and report the bottleneck.

---

# Part C — Build/update post-merge sanity report

Create or update:

- `cajas/docs/post_github_merge_sanity_report.md`

Include:

## Merge status

- target branch: `main`
- source branch: `phase-next-mega-logic`
- local main commit
- whether expected docs are present

## Validation results

- fast validation status and runtime
- micro smoke status and runtime
- data-source audit count
- high-risk findings status

## Commands run

List the exact commands from Part B.

## Boundaries confirmed

State that the merged mainline still does not add:

- broker/live/paper execution
- order generation/routing
- position sizing
- PnL optimization
- execution simulation

## Recommended next branch

Suggested next branch name:

```bash
git checkout -b phase-post-merge-research-next
```

But do not create it unless the user explicitly wants to start new work.

---

# Part D — Update references if needed

If the sanity report is created, update:

- `cajas/docs/final_research_stack_index.md`
- `cajas/docs/post_merge_checklist.md`

Add links to:

- `cajas/docs/post_github_merge_sanity_report.md`

Do not duplicate large content.

---

# Part E — Commit guidance

If docs are added/updated:

```bash
git add cajas/docs/post_github_merge_sanity_report.md \
        cajas/docs/final_research_stack_index.md \
        cajas/docs/post_merge_checklist.md

git commit -m "docs: add post-github-merge sanity report"
```

Push:

```bash
git push origin main
```

If commit/push is blocked in Codex, report manual commands.

---

# Final response expected from Codex

Return compact summary:

- Summary
- Branch/status
- Local main commit
- Validation results
- Runtime summary
- Data-source audit summary
- Missing docs, if any
- Files changed
- Git commits or manual commands
- Final status
- Suggested next branch name

Do not start new feature work unless explicitly instructed.
