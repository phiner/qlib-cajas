# Phase 646–665 Prompt: Post-Push Merge Verification + Mainline Handoff

You are working on branch:

- `phase-next-mega-logic`

## Current state

Phase 626–645 completed final PR/merge-gate artifacts.

Latest known status:

- Final PR description added:
  - `cajas/docs/pr_description_phase_next_mega_logic.md`
- Merge checklist added:
  - `cajas/docs/merge_gate_checklist.md`
- References updated:
  - `cajas/docs/pr_readiness_checklist.md`
  - `cajas/docs/final_research_stack_index.md`
- Phase prompt updated:
  - `tasks/phase_626_645_final_pr_merge_gate_prompt.md`

Latest validation reused from phase606:

```text
run_fast_validation --tier fast:
  total 86.029s
  pytest_fast 82.899s

micro smoke:
  10.79s

data-source audit:
  reads_full_csv_likely_count = 2
  high_risk_count effectively 0
```

Current blocking issue:

- Commit was blocked in Codex by approval-service `503`.
- User should manually run:

```bash
git commit -m "docs: add final PR description and merge gate checklist"
git push origin phase-next-mega-logic
```

Important:

- Start by checking current branch/status.
- If the user already manually committed/pushed, do not duplicate the commit.
- This phase is only for final verification and handoff after push/PR.

## Phase objective

Implement **Post-Push Merge Verification + Mainline Handoff**.

This is a final verification and handoff phase.

Primary goals:

1. Confirm the branch is committed and pushed.
2. Confirm PR/merge docs are present.
3. Run the merge-gate validation commands once.
4. Produce a final mainline handoff note.
5. Create a post-merge checklist for future work.
6. Do not add new research features.
7. Preserve all research-only/no-execution boundaries.

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

# Part A — Verify commit and push state

Run:

```bash
git branch --show-current
git status --short
git log --oneline -8
git status -sb
```

Expected:

- branch is `phase-next-mega-logic`
- working tree is clean
- latest commit should include final PR/merge docs if user committed them

If final PR/merge docs are still staged, commit them:

```bash
git commit -m "docs: add final PR description and merge gate checklist"
```

If not pushed, remind user to push:

```bash
git push origin phase-next-mega-logic
```

Do not push from Codex unless explicitly instructed.

Completion reference:

- expected handoff docs from this phase:
  - `cajas/docs/mainline_handoff_note.md`
  - `cajas/docs/post_merge_checklist.md`

---

# Part B — Verify final docs exist

Check:

```bash
test -f cajas/docs/pr_description_phase_next_mega_logic.md
test -f cajas/docs/merge_gate_checklist.md
test -f cajas/docs/pr_readiness_checklist.md
test -f cajas/docs/final_phase_archive_index.md
test -f cajas/docs/final_research_stack_index.md
test -f cajas/docs/future_work_checklist.md
```

Report any missing docs.

Do not rewrite docs unless a small missing reference is obvious.

---

# Part C — Run merge-gate validation

Run only lightweight merge gate commands:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/validation-runtime-audit/fast_validation_phase646.json
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_phase646.json --out-md tmp/data-io-audit/data_source_audit_phase646.md
```

Do not run closure/full smoke unless explicitly requested.

Expected:

- fast validation passes
- micro smoke passes
- data-source audit has no high-risk regression
- `reads_full_csv_likely_count` remains low, ideally `<= 2`

If a command exceeds a few minutes, stop and report bottleneck.

---

# Part D — Create final mainline handoff note

Create:

- `cajas/docs/mainline_handoff_note.md`

Include:

## Branch

- `phase-next-mega-logic`

## Final validation baseline

- latest fast validation runtime
- latest micro smoke runtime
- latest data-source audit count

## What this branch delivers

- research stack hardening
- validation tiering
- data I/O large CSV readiness
- fast validation optimization
- research-only approval/merge docs

## What it does not deliver

- broker
- live trading
- paper execution
- orders
- position sizing
- PnL optimization
- execution simulation

## Recommended first actions after merge

- run fast validation on target branch
- run micro smoke
- run data-source audit
- check docs index
- do not start execution features without a separate design branch

---

# Part E — Create post-merge checklist

Create:

- `cajas/docs/post_merge_checklist.md`

Include:

```bash
git checkout <target-main-branch>
git pull
git merge phase-next-mega-logic
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_post_merge.json --out-md tmp/data-io-audit/data_source_audit_post_merge.md
```

Also include rollback notes:

```bash
git status
git log --oneline -5
git merge --abort
```

if a merge conflict happens before commit.

---

# Part F — Update references

If new docs are created, update:

- `cajas/docs/final_research_stack_index.md`
- `cajas/docs/pr_readiness_checklist.md`
- `tasks/phase_646_665_post_push_merge_handoff_prompt.md`

Add links to:

- `cajas/docs/mainline_handoff_note.md`
- `cajas/docs/post_merge_checklist.md`

Do not duplicate large content.

---

# Part G — Commit guidance

If new docs are created:

```bash
git add cajas/docs/mainline_handoff_note.md \
        cajas/docs/post_merge_checklist.md \
        cajas/docs/final_research_stack_index.md \
        cajas/docs/pr_readiness_checklist.md \
        tasks/phase_646_665_post_push_merge_handoff_prompt.md

git commit -m "docs: add post-push mainline handoff checklist"
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
- Mainline handoff path
- Post-merge checklist path
- Git commits or manual commit commands
- Final status
- Manual push command

Do not push from Codex unless explicitly instructed.
