# Phase 6566–6685 — Minimal Safe Repair for Tasks Docs Cleanup

## Context

You are working in the Qlib Base / qlib-cajas repository.

The previous docs/tasks cleanup attempts became too broad and unsafe.

Known issues from recent attempts:

- Temporary helper files were created and must not be committed:
  - `move_tasks.py`
  - `move_tasks.sh`
  - `tracked_tasks.txt`
- Agents attempted broad automatic classification of `tasks/phase_*.md` files.
- That broad classification is error-prone because generic words like `review`, `batch`, `gui`, or `pattern` can misclassify Qlib infrastructure prompts as EURUSD research prompts.
- `cajas/README.md` roadmap/archive links were not inserted correctly.
- The master roadmap file may not have been replaced with the correct full version supplied by the human.
- The current state may contain many pending renames from earlier cleanup attempts.

Important decision for this phase:

Do not continue broad archive classification.

This phase is a minimal safe repair only.

## Goal

Make the docs/tasks cleanup safe and reviewable without trying to perfectly classify all historical phase prompts.

This phase should:

1. Remove temporary helper files.
2. Ensure the full roadmap file is present at the correct path.
3. Ensure the archive README is present at the correct path.
4. Add correct roadmap/archive links to `cajas/README.md`.
5. Move only one known superseded prompt out of root if present:
   - `tasks/phase_6206_6325_tasks_archive_and_eurusd_roadmap_prompt.md`
6. Stop before committing if there are large unexpected renames or unsafe pending changes.
7. Report final status clearly.

Do not perform broad automatic task reclassification.

Do not write or run a move script that loops through all phase prompts.

Do not commit until the human reviews the final state.

## Files Supplied by Human

The human has supplied or will supply these replacement files.

Use them directly.

### Full roadmap replacement

Source file:

```text
/mnt/data/eurusd_15m_research_end_to_end_roadmap.md
```

Destination:

```text
tasks/eurusd_15m_research_end_to_end_roadmap.md
```

### Archive README replacement

Source file:

```text
/mnt/data/tasks_archive_README.md
```

Destination:

```text
tasks/archive/README.md
```

### README snippet

Source file:

```text
/mnt/data/cajas_README_project_roadmap_snippet.md
```

Insert into:

```text
cajas/README.md
```

Insert the snippet near the top, before `## Goal`, unless an equivalent `## Project Roadmap` section already exists.

Expected snippet:

```markdown
## Project Roadmap

- [EURUSD 15m research end-to-end roadmap](../tasks/eurusd_15m_research_end_to_end_roadmap.md)
- [Tasks archive policy](../tasks/archive/README.md)
```

Important:

Because `cajas/README.md` is inside the `cajas/` directory, links must use `../tasks/...`, not `tasks/...`.

## Required Steps

### 1. Inspect current state

Run:

```bash
git status --short --branch
find tasks -maxdepth 1 -type f | sort
```

If there are unexpected tracked deletions outside `tasks/`, stop and report.

If there are many pending renames from previous broad classification attempts, do not add more broad renames. Continue only with the minimal repair below.

### 2. Remove helper files

Run:

```bash
rm -f move_tasks.py move_tasks.sh tracked_tasks.txt
```

Confirm they are absent:

```bash
for f in move_tasks.py move_tasks.sh tracked_tasks.txt; do
  [ -e "$f" ] && echo "STILL_PRESENT $f" || true
done
```

No output is expected.

### 3. Ensure archive directories exist

Run:

```bash
mkdir -p tasks/archive/superseded_or_local
mkdir -p tasks/archive/qlib_base_infrastructure
mkdir -p tasks/archive/eurusd_research
```

### 4. Copy the full roadmap into place

Run:

```bash
cp /mnt/data/eurusd_15m_research_end_to_end_roadmap.md \
  tasks/eurusd_15m_research_end_to_end_roadmap.md
```

Verify this is not a short stub:

```bash
wc -l tasks/eurusd_15m_research_end_to_end_roadmap.md
grep -n "Project Purpose\\|Scope Boundaries\\|Local GUI Review App\\|Future Outcome Analysis\\|Final Target" \
  tasks/eurusd_15m_research_end_to_end_roadmap.md
```

The file should be a substantial roadmap and should include all of these section markers.

### 5. Copy archive README into place

Run:

```bash
cp /mnt/data/tasks_archive_README.md tasks/archive/README.md
```

Verify:

```bash
grep -n "Archive Structure\\|Root Tasks Policy\\|Master Roadmap\\|Move Policy" tasks/archive/README.md
```

### 6. Move only the known superseded root prompt

If this file exists at root:

```text
tasks/phase_6206_6325_tasks_archive_and_eurusd_roadmap_prompt.md
```

move it to:

```text
tasks/archive/superseded_or_local/phase_6206_6325_tasks_archive_and_eurusd_roadmap_prompt.md
```

Use this safe command:

```bash
if git ls-files --error-unmatch tasks/phase_6206_6325_tasks_archive_and_eurusd_roadmap_prompt.md >/dev/null 2>&1; then
  git mv tasks/phase_6206_6325_tasks_archive_and_eurusd_roadmap_prompt.md \
    tasks/archive/superseded_or_local/phase_6206_6325_tasks_archive_and_eurusd_roadmap_prompt.md
elif [ -f tasks/phase_6206_6325_tasks_archive_and_eurusd_roadmap_prompt.md ]; then
  mv tasks/phase_6206_6325_tasks_archive_and_eurusd_roadmap_prompt.md \
    tasks/archive/superseded_or_local/phase_6206_6325_tasks_archive_and_eurusd_roadmap_prompt.md
fi
```

Do not move any other prompts in this phase unless the human explicitly asks.

### 7. Fix `cajas/README.md` roadmap links

If `cajas/README.md` does not already contain `## Project Roadmap`, insert this section before `## Goal`:

```markdown
## Project Roadmap

- [EURUSD 15m research end-to-end roadmap](../tasks/eurusd_15m_research_end_to_end_roadmap.md)
- [Tasks archive policy](../tasks/archive/README.md)
```

Use a small Python edit, not broad sed replacement:

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("cajas/README.md")
text = path.read_text(encoding="utf-8")
section = """## Project Roadmap

- [EURUSD 15m research end-to-end roadmap](../tasks/eurusd_15m_research_end_to_end_roadmap.md)
- [Tasks archive policy](../tasks/archive/README.md)

"""

if "## Project Roadmap" not in text:
    marker = "## Goal"
    if marker not in text:
        raise SystemExit("Could not find '## Goal' marker in cajas/README.md")
    text = text.replace(marker, section + marker, 1)
else:
    # Ensure correct relative links if the section already exists.
    text = text.replace("(tasks/eurusd_15m_research_end_to_end_roadmap.md)", "(../tasks/eurusd_15m_research_end_to_end_roadmap.md)")
    text = text.replace("(tasks/archive/README.md)", "(../tasks/archive/README.md)")

path.write_text(text, encoding="utf-8")
PY
```

Verify:

```bash
grep -n "Project Roadmap\\|EURUSD 15m research end-to-end roadmap\\|Tasks archive policy" cajas/README.md
```

### 8. Root tasks check

Run:

```bash
find tasks -maxdepth 1 -type f | sort
```

Preferred root files:

```text
tasks/eurusd_15m_research_end_to_end_roadmap.md
tasks/phase_6086_6205_eurusd_15m_local_review_gui_prompt.md
tasks/phase_6326_6445_tasks_prompt_cleanup_archive_prompt.md
```

If other root files remain, report them. Do not move them automatically in this minimal repair phase unless they are the known `phase_6206...` file.

### 9. Validation / hygiene

Run:

```bash
git status --short --branch
git diff --check
find cajas -path "*/init.py" -print
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Fast validation is optional and may be skipped because this is docs/tasks-only repair.

If skipped, report:

```text
Fast validation skipped because only docs/tasks organization changed.
```

### 10. Stop before commit

Do not commit automatically.

Report final state and wait for human approval.

## Final Response Required

Report:

- active branch
- whether helper files are absent
- roadmap destination path
- roadmap line count
- archive README path
- whether `cajas/README.md` links use `../tasks/...`
- root `tasks/` files remaining
- whether `phase_6206...` was moved
- whether any other prompts were moved
- whether any files were deleted, and exact reason
- `git status --short --branch`
- `git diff --check` result
- `find cajas -path "*/init.py" -print` result
- `check_path_hygiene.py` result
- whether fast validation was run or skipped
- confirmation that no source behavior changed
- confirmation that no automated merge was performed
- confirmation that no commit/push was performed
