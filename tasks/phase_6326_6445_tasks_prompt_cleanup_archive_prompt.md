# Phase 6326–6445 — Tasks Prompt Cleanup, Archive Structure, and Roadmap Linkage

## Context

You are working in the Qlib Base / qlib-cajas repository.

The user has already saved the master roadmap document for the EURUSD 15m research project:

`eurusd_15m_research_master_from_zero_to_gui_workflow.md`

The active project objective is now clear:

- EURUSD 15m Bid pattern research.
- Clean data view.
- Pattern candidates.
- Human review workflow.
- Local GUI review app.
- Later feedback summary, outcome analysis, and offline strategy hypothesis research.

Current problem:

- `tasks/` contains too many historical `phase_*.md` prompt files.
- Some are old infrastructure prompts.
- Some are old EURUSD prompts.
- Some are superseded variants.
- Root `tasks/` is noisy and hard to navigate.
- Previous accidental move/delete operations caused tracked `tasks/phase_*.md` deletion confusion.
- This phase must clean up carefully and safely.

Important scope boundary:

- This is a docs/tasks organization phase only.
- Do not change production/source behavior.
- Do not change Qlib core.
- Do not alter generated data artifacts.
- Do not run automated merge.
- Do not delete tracked files blindly.
- Prefer archiving over deletion.

## Goal

Clean up the task prompt documentation area and connect it to the saved master roadmap.

This phase should:

1. Audit all `tasks/phase_*.md` files.
2. Create a clear archive structure.
3. Move historical phase prompts into archive folders.
4. Keep root `tasks/` small and current.
5. Add an archive README / manifest.
6. Add or copy the master roadmap into the repo if not already present.
7. Update docs/README links.
8. Avoid source behavior changes.

## Required Work

### 1. Inspect current tasks state safely

Run:

```bash
git status --short --branch
find tasks -maxdepth 2 -type f | sort
find tasks -maxdepth 1 -type f -name "phase_*.md" | sort
```

Before moving files, determine:

- which files are tracked
- which files are untracked
- which files are current active prompts
- which files are historical prompts
- which files are duplicates or superseded variants

Use:

```bash
git ls-files tasks | sort
```

Do not proceed if `git status` already shows unexpected deletions. If unexpected deletions are present, stop and report.

### 2. Create archive structure

Create:

```text
tasks/archive/
tasks/archive/qlib_base_infrastructure/
tasks/archive/eurusd_research/
tasks/archive/superseded_or_local/
```

Use these guidelines:

#### `tasks/archive/qlib_base_infrastructure/`

Move older Qlib Base infrastructure/maintenance prompts here, including phases related to:

- dataset quality hardening
- schema contracts
- golden fixtures
- drift tracking
- runtime budgets
- validation bundles
- history/alias migration
- release readiness
- final reviewer packets
- maintenance continuation
- post-merge validation

#### `tasks/archive/eurusd_research/`

Move EURUSD research prompts here, including phases related to:

- EURUSD dataset audit
- anomaly triage
- clean view
- pattern candidates
- review QA/schema/template
- feedback intake
- review batch
- GUI review app
- completed-batch intake

#### `tasks/archive/superseded_or_local/`

Move clearly superseded duplicate prompts here, such as:

- older variants replaced by v2 / updated prompt
- local-only generated prompts that are useful but not active
- prompt variants that should not stay at root

Prefer archiving over deletion.

### 3. Keep root tasks minimal

After cleanup, root `tasks/` should ideally contain only:

```text
tasks/eurusd_15m_research_end_to_end_roadmap.md
tasks/phase_6326_6445_tasks_prompt_cleanup_archive_prompt.md
```

Optionally keep one current implementation prompt if it is immediately active, for example:

```text
tasks/phase_6086_6205_eurusd_15m_local_review_gui_prompt.md
```

Do not keep dozens of old phase prompts at root.

### 4. Add master roadmap into repo if needed

If the saved master roadmap exists outside the repo, copy or recreate it as:

```text
tasks/eurusd_15m_research_end_to_end_roadmap.md
```

The roadmap should summarize the complete path:

- Qlib Base infrastructure
- EURUSD 15m dataset audit
- anomaly triage
- clean view
- pattern features
- candidate pack
- review schema/template
- review feedback
- first batch
- local GUI
- completed review intake
- future outcome analysis
- future offline strategy hypothesis research

It must clearly state:

- EURUSD 15m Bid is fixed research base
- no 1H/4H aggregation
- no live/paper trading
- no broker routing
- no order generation
- no Qlib core changes
- GUI is review interface
- CSV/JSONL are durable storage formats

If the file already exists and is good, only update links/metadata as needed.

### 5. Add archive manifest

Create:

```text
tasks/archive/README.md
```

It should explain:

- why phase prompts were archived
- how archive directories are organized
- which file is the current master roadmap
- which root prompt is active
- how to add future prompts
- policy:
  - root `tasks/` should stay small
  - historical prompts should be archived
  - do not delete tracked prompts without explicit reason
  - use `git mv` for tracked prompt moves

Also optionally create:

```text
tasks/archive/archive_manifest.md
```

The manifest should include a compact table:

```markdown
| File | Archive group | Reason |
|---|---|---|
```

If the list is too long, summarize by phase ranges.

### 6. Use git-safe moves

For tracked files, use `git mv`.

For untracked files, use normal `mv` and then `git add` if the file should remain in archive.

Example:

```bash
git mv tasks/phase_1016_1045_qlib_experiment_reproducibility_prompt.md tasks/archive/qlib_base_infrastructure/
```

For many files, write a short shell/Python helper only if it is safe and reviewable.

Before committing, run:

```bash
git status --short
```

Confirm that moved tracked files show as renames where possible, not unexplained mass deletions.

### 7. Update docs links

Update at least:

```text
cajas/README.md
cajas/docs/current_qlib_base_stage_archive.md
cajas/docs/eurusd_pattern_research_kickoff.md
```

Add references to:

```text
tasks/eurusd_15m_research_end_to_end_roadmap.md
tasks/archive/README.md
```

Mention:

- phase prompts are archived
- master roadmap is now the main human-facing project overview
- current work should follow staged prompts, not root tasks clutter

Do not over-edit unrelated docs.

### 8. Validation / hygiene

Run:

```bash
git status --short --branch
git diff --check
find cajas -path "*/init.py" -print
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Since this is docs/tasks organization only, fast validation is optional. If you run it:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/fast_validation_latest.json
```

If skipped, explicitly state:

```text
Fast validation skipped because only tasks/docs organization changed.
```

Do not modify source code to make unrelated tests pass.

## Commit Guidance

Suggested commit:

```bash
git add tasks cajas/README.md cajas/docs/current_qlib_base_stage_archive.md cajas/docs/eurusd_pattern_research_kickoff.md

git commit -m "docs: archive phase prompts and link EURUSD roadmap"
```

If the move set is very large, one commit is still acceptable because it is a docs/tasks organization-only phase.

Do not perform automated merge operations.

If ready, push the current branch and ask the human user to merge manually on GitHub:

```bash
git push origin phase-eurusd-pattern-research-kickoff
```

or if using a new branch:

```bash
git push origin phase-tasks-archive-roadmap-cleanup
```

## Final Response Required

When finished, report:

- active branch
- root `tasks/` files remaining
- archive directories created
- number of prompts moved to each archive directory
- files deleted, if any, and exact reason
- master roadmap path
- archive README path
- docs updated
- validation/hygiene results
- fast validation runtime if run, or reason skipped
- git status summary
- push status
- manual GitHub merge instruction
- confirmation that no source behavior was changed
- confirmation that no automated merge was performed
