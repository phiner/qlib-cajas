# Phase 6446–6565 — Strict Manual Repair for Tasks Archive and Roadmap Docs

## Context

The previous tasks cleanup attempt was not acceptable.

Known problems from the previous attempt:

- helper files were created and left in the working tree:
  - `move_tasks.py`
  - `move_tasks.sh`
  - `tracked_tasks.txt`
- root `tasks/` was not reliably reduced to the intended small set
- `phase_6206_6325_tasks_archive_and_eurusd_roadmap_prompt.md` may still be at root
- `cajas/README.md` roadmap/archive links were not correctly inserted
- archive classification used broad automatic keyword logic and may contain some imperfect placements
- the master roadmap must not be replaced by a shortened stub

This repair phase must be conservative and manual.

## Goal

Finish the docs/tasks cleanup safely.

This phase should:

1. Remove temporary helper files.
2. Ensure root `tasks/` contains only the intended files.
3. Ensure the full roadmap file exists.
4. Ensure archive README exists.
5. Fix `cajas/README.md` links with correct relative paths.
6. Run hygiene checks.
7. Report final state.
8. Do not commit unless the final state is clean and reviewed.

## Required Manual Repair Steps

### 1. Stop and inspect

Run:

```bash
git status --short --branch
find tasks -maxdepth 1 -type f | sort
```

If there are unexpected tracked deletions outside `tasks/`, stop and report.

### 2. Remove helper files

Remove these if present:

```bash
rm -f move_tasks.py move_tasks.sh tracked_tasks.txt
```

They must not appear in `git status --short --branch`.

### 3. Ensure archive directories exist

Run:

```bash
mkdir -p tasks/archive/qlib_base_infrastructure
mkdir -p tasks/archive/eurusd_research
mkdir -p tasks/archive/superseded_or_local
```

### 4. Move `phase_6206` out of root

If this file exists at root:

```text
tasks/phase_6206_6325_tasks_archive_and_eurusd_roadmap_prompt.md
```

move it to:

```text
tasks/archive/superseded_or_local/phase_6206_6325_tasks_archive_and_eurusd_roadmap_prompt.md
```

Use `git mv` if tracked, otherwise `mv`.

Suggested safe shell:

```bash
if git ls-files --error-unmatch tasks/phase_6206_6325_tasks_archive_and_eurusd_roadmap_prompt.md >/dev/null 2>&1; then
  git mv tasks/phase_6206_6325_tasks_archive_and_eurusd_roadmap_prompt.md tasks/archive/superseded_or_local/phase_6206_6325_tasks_archive_and_eurusd_roadmap_prompt.md
elif [ -f tasks/phase_6206_6325_tasks_archive_and_eurusd_roadmap_prompt.md ]; then
  mv tasks/phase_6206_6325_tasks_archive_and_eurusd_roadmap_prompt.md tasks/archive/superseded_or_local/phase_6206_6325_tasks_archive_and_eurusd_roadmap_prompt.md
fi
```

### 5. Root tasks target

After repair, root `tasks/` should contain only:

```text
tasks/eurusd_15m_research_end_to_end_roadmap.md
tasks/phase_6086_6205_eurusd_15m_local_review_gui_prompt.md
tasks/phase_6326_6445_tasks_prompt_cleanup_archive_prompt.md
```

Run:

```bash
find tasks -maxdepth 1 -type f | sort
```

If additional root prompt files remain, move them to an archive directory.

Use this policy:

- EURUSD research implementation prompt -> `tasks/archive/eurusd_research/`
- Qlib infrastructure/maintenance prompt -> `tasks/archive/qlib_base_infrastructure/`
- old cleanup/roadmap/superseded local prompt -> `tasks/archive/superseded_or_local/`

### 6. Restore full roadmap

Ensure this file exists:

```text
tasks/eurusd_15m_research_end_to_end_roadmap.md
```

It must be the full roadmap, not a short stub.

Minimum expected content markers:

- `Project Purpose`
- `Scope Boundaries`
- `Repository Posture`
- `Data Inputs`
- `Completed Infrastructure Path`
- `EURUSD Research Path`
- `Feature and Candidate Research`
- `Human Review Schema and Template`
- `Review Feedback Intake and Summary`
- `First Review Batch`
- `Local GUI Review App`
- `Completed Batch Intake and Merge`
- `Future Outcome Analysis`
- `Future Offline Strategy Hypotheses`
- `Current Artifact Map`
- `How to Start Using the System`
- `Daily Validation Commands`
- `Git Workflow`
- `Final Target`

Run:

```bash
head -n 60 tasks/eurusd_15m_research_end_to_end_roadmap.md
wc -l tasks/eurusd_15m_research_end_to_end_roadmap.md
```

If the file is short or missing these sections, replace it with the full roadmap provided by the human user.

### 7. Ensure archive README exists

Ensure this file exists:

```text
tasks/archive/README.md
```

It must explain:

- archive structure
- root tasks policy
- master roadmap path
- move policy
- `git mv` for tracked files
- no helper files in working tree

### 8. Fix README links

In `cajas/README.md`, add this section near the top, before `## Goal`:

```markdown
## Project Roadmap

- [EURUSD 15m research end-to-end roadmap](../tasks/eurusd_15m_research_end_to_end_roadmap.md)
- [Tasks archive policy](../tasks/archive/README.md)
```

Important:

- Because `cajas/README.md` is inside the `cajas/` directory, links must use `../tasks/...`.
- Do not use `tasks/...` from inside `cajas/README.md`.

Verify:

```bash
grep -n "Project Roadmap\|EURUSD 15m research end-to-end roadmap\|Tasks archive policy" cajas/README.md
```

### 9. Optional docs links

If already touched or appropriate, add small references to the roadmap/archive in:

```text
cajas/docs/current_qlib_base_stage_archive.md
cajas/docs/eurusd_pattern_research_kickoff.md
```

Keep edits small. Do not rewrite those documents.

### 10. Archive counts

Run:

```bash
find tasks/archive/qlib_base_infrastructure -maxdepth 1 -type f | wc -l
find tasks/archive/eurusd_research -maxdepth 1 -type f | wc -l
find tasks/archive/superseded_or_local -maxdepth 1 -type f | wc -l
```

Report the counts.

If obviously misclassified files remain, fix them manually with `git mv`.

Do not attempt a broad automatic reclassification script.

### 11. Validation / hygiene

Run:

```bash
git status --short --branch
find tasks -maxdepth 1 -type f | sort
git diff --check
find cajas -path "*/init.py" -print
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Fast validation may be skipped because this is docs/tasks-only cleanup. If skipped, say:

```text
Fast validation skipped because only docs/tasks organization changed.
```

### 12. Commit guidance

Only after the final state is reviewed and clean enough, commit:

```bash
git add tasks cajas/README.md cajas/docs/current_qlib_base_stage_archive.md cajas/docs/eurusd_pattern_research_kickoff.md
git commit -m "docs: repair tasks archive and roadmap links"
```

Do not push unless explicitly asked.

Do not perform automated merge operations.

## Final Response Required

Report:

- active branch
- root `tasks/` files remaining
- archive counts by directory
- temporary helper files absent: yes/no
- roadmap restored/full: yes/no
- roadmap line count
- archive README path
- README links fixed: yes/no
- docs updated
- files deleted, if any, and exact reason
- validation/hygiene results
- fast validation skipped or runtime if run
- git status summary
- commit status
- push status
- confirmation that no source behavior changed
- confirmation that no automated merge was performed
