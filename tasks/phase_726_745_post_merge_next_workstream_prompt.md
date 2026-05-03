# Phase 726–745 Prompt: Start Post-Merge Research Branch + Next Workstream Baseline

You are working after `phase-next-mega-logic` has been merged into `main`.

## Current state

Post-GitHub-merge sanity verification completed on `main`.

Latest known status:

- Branch: `main`
- Working tree: clean
- Local main commit:
  - `a67b2a25 docs: add post-merge validation baseline`
- Final docs are present.
- Post-merge sanity report has been added:
  - `cajas/docs/post_github_merge_sanity_report.md`
- Post-merge checklist and final research stack index have been updated.
- Phase prompt was tracked:
  - `tasks/phase_706_725_post_github_merge_main_sanity_prompt.md`

Latest validation on `main`:

```text
PASS run_fast_validation.py --tier fast
  pytest_fast: 92.50s
  total: 96.65s

PASS run_smoke_validation.py --tier micro
  total: 13.75s

PASS audit_data_sources.py
  reads_full_csv_likely_count = 2
  high-risk findings effectively 0
```

Manual push still needed:

```bash
git push origin main
```

Suggested next branch:

```bash
phase-post-merge-research-next
```

## Phase objective

Implement **Start Post-Merge Research Branch + Next Workstream Baseline**.

This phase should not add a large new feature yet. It should prepare the next development lane cleanly after the merge.

Primary goals:

1. Push latest `main`.
2. Create a new branch from updated `main`.
3. Confirm validation baseline on the new branch.
4. Create a next-workstream planning document.
5. Choose the next safest research direction.
6. Preserve all no-execution boundaries.
7. Avoid re-opening old branch cleanup unless needed.

## Non-negotiable boundaries

Do not:

- Modify Qlib core for execution features.
- Add broker adapters.
- Add live trading.
- Add paper trading execution.
- Add order generation/routing.
- Add position sizing.
- Add portfolio optimization.
- Add PnL optimization.
- Add execution simulation.
- Add network calls except normal git push/pull.
- Add GPU/CUDA requirements.
- Add files named `init.py`.

All validation remains:

- CPU-only
- local
- deterministic where feasible
- no trading execution

---

# Part A — Push and create new branch

Start from `main`.

Run:

```bash
git branch --show-current
git status --short
git log --oneline -5
```

Expected:

- branch is `main`
- working tree clean
- latest commit includes post-merge validation baseline

Push:

```bash
git push origin main
```

Then create the new branch:

```bash
git checkout -b phase-post-merge-research-next
```

Confirm:

```bash
git branch --show-current
git status --short
```

Expected:

- branch is `phase-post-merge-research-next`
- working tree clean

---

# Part B — Confirm baseline on new branch

Run lightweight baseline only:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/validation-runtime-audit/fast_validation_phase726.json

./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro

./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py \
  --project-root cajas \
  --data-root /home/phiner/projects/research/data \
  --out-json tmp/data-io-audit/data_source_audit_phase726.json \
  --out-md tmp/data-io-audit/data_source_audit_phase726.md
```

Expected:

- fast validation passes
- micro smoke passes
- `reads_full_csv_likely_count <= 2`
- no high-risk data-source findings

Do not run closure/full smoke.

---

# Part C — Create next-workstream planning doc

Create:

- `cajas/docs/post_merge_next_workstream_plan.md`

This document should be concise and actionable.

Include:

## Current baseline

- branch
- latest main commit
- fast validation runtime
- micro smoke runtime
- data-source audit count
- validation tier commands

## Candidate next workstreams

List and briefly compare:

### Option 1 — Research dataset quality loop

Focus:

- better label/data QA
- review queue summaries
- dataset coverage diagnostics
- drift/imbalance checks
- no model expansion required

Why safe:

- offline research only
- improves data quality
- no trading execution

### Option 2 — Feature engineering research lane

Focus:

- additional K-line/FX structure features
- chunked feature extraction
- large CSV readiness
- feature-set comparison reports

Why safe:

- offline only
- builds on data I/O work
- can stay bounded with row limits/chunking

### Option 3 — Model evaluation/reporting lane

Focus:

- stronger baseline evaluation reports
- calibration/error-slice improvements
- run comparison summaries
- no heavier training by default

Why safe:

- uses existing baseline artifacts
- improves interpretability
- no execution

### Option 4 — Developer productivity lane

Focus:

- more CLI tests converted to in-process
- keep fast validation stable below 90s
- fixture cleanup
- runtime audit improvements

Why safe:

- no research behavior change
- keeps project maintainable

## Recommended next choice

Recommend one direction.

Given the current state, prefer:

```text
Option 1 + Option 2 combined lightly:
Research dataset quality loop + chunked feature research readiness
```

Reason:

- CSV/data I/O base is now ready.
- Real data files are still small now, but future multi-GB readiness matters.
- The system needs better data-quality confidence before heavier model work.
- Still avoids broker/live/paper execution.

## Explicit non-goals

- broker
- live trading
- paper trading execution
- order generation/routing
- position sizing
- PnL optimization
- execution simulation

---

# Part D — Create next phase prompt file

Create:

- `tasks/phase_746_775_dataset_quality_feature_research_prompt.md`

This prompt should be the next actual implementation phase.

Theme:

```text
Dataset Quality Loop + Chunked Feature Research Readiness
```

High-level scope:

1. Dataset quality report builder.
2. Label coverage and imbalance diagnostics.
3. Time-range/session coverage diagnostics.
4. Chunked feature extraction dry-run report.
5. Feature schema manifest.
6. Offline-only research queue summary.
7. Tiny fixtures and bounded tests.
8. No training-heavy default.
9. No trading execution.

Do not implement the full phase yet; only create the prompt file for the next phase.

---

# Part E — Update references

Update if useful:

- `cajas/docs/final_research_stack_index.md`
- `cajas/docs/future_work_checklist.md`
- `cajas/README.md`

Add references to:

- `cajas/docs/post_merge_next_workstream_plan.md`
- `tasks/phase_746_775_dataset_quality_feature_research_prompt.md`

Keep changes small.

---

# Part F — Validation

Run bounded checks:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/validation-runtime-audit/fast_validation_phase726_final.json
```

Micro smoke can be skipped if already run in Part B unless files touched validation/smoke scripts.

---

# Part G — Commit guidance

Commit:

```bash
git add cajas/docs/post_merge_next_workstream_plan.md \
        cajas/docs/final_research_stack_index.md \
        cajas/docs/future_work_checklist.md \
        cajas/README.md \
        tasks/phase_746_775_dataset_quality_feature_research_prompt.md

git commit -m "docs: plan next post-merge research workstream"
```

Push:

```bash
git push origin phase-post-merge-research-next
```

---

# Final response expected from Codex

Return compact summary:

- Summary
- Branch/status
- Baseline validation results
- Runtime summary
- Data-source audit summary
- Files changed
- Next recommended workstream
- Git commit
- Final status
- Manual push command if needed

Do not start implementing Phase 746–775 yet.
