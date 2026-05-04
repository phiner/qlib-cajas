# Phase 0 Git Hygiene and Commit Prompt for Codex

You are working in the `qlib-cajas` repository.

Current branch:

```bash
cajas/market-recognition-phase-0
```

Current known `git status` before this task:

```text
On branch cajas/market-recognition-phase-0
Your branch is up to date with 'origin/cajas/market-recognition-phase-0'.

Changes not staged for commit:
  modified:   .gitignore
  modified:   cajas/README.md

Untracked files:
  .codex
  AGENTS.md
  cajas/configs/
  cajas/data_examples/
  cajas/scripts/
  tmp/
```

## Goal

Clean up Git hygiene for the new `qlib-cajas` Phase 0 scaffold, then create clear commits.

This repository is a personal research fork of Microsoft Qlib. Do **not** modify Qlib core in this task.

## Hard Boundaries

Do not modify:

```text
qlib/
examples/ existing upstream files
scripts/ existing upstream files unless absolutely necessary
```

Do not commit:

```text
.codex/
tmp/
taskDocs/
raw CSV data
large generated datasets
model artifacts
cache files
```

Do commit:

```text
.gitignore
AGENTS.md
cajas/README.md
cajas/configs/
cajas/data_examples/
cajas/scripts/
```

## Required Work

### 1. Inspect repository state

Run:

```bash
git status
git diff -- .gitignore cajas/README.md
find cajas -maxdepth 3 -type f | sort
```

Confirm that this task only touches the Phase 0 scaffold and repository rules.

### 2. Update `.gitignore`

Ensure `.gitignore` contains rules for local agent state, local prompts/docs, local outputs, generated datasets, model artifacts, and common Python caches.

Add or normalize entries like the following, avoiding duplicate blocks if they already exist:

```gitignore
# Local agent/tooling state
.codex/

# Local task prompts/docs
taskDocs/

# Local generated outputs
tmp/
outputs/
runs/

# Generated datasets / model artifacts
*.parquet
*.pkl
*.joblib
*.model
*.bin

# Python cache
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
```

If the repository already has equivalent entries, keep the file clean and avoid unnecessary duplication.

### 3. Verify ignored paths

After editing `.gitignore`, run:

```bash
git status
git check-ignore -v .codex tmp || true
```

Expected result:

- `.codex/` should no longer appear as an untracked file in `git status`.
- `tmp/` should no longer appear as an untracked file in `git status`.
- `git check-ignore -v .codex tmp` should show matching `.gitignore` rules.

If `.codex` is a file rather than a directory, still ensure it is ignored by adding both patterns if necessary:

```gitignore
.codex
.codex/
```

### 4. Validate Phase 0 files

Inspect the files under `cajas/`:

```bash
find cajas -maxdepth 4 -type f | sort
```

Expected files should include:

```text
cajas/README.md
cajas/scripts/prepare_fx_dataset.py
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
cajas/data_examples/README.md
```

Confirm the data preparation script is syntactically valid:

```bash
python -m py_compile cajas/scripts/prepare_fx_dataset.py
```

Do not run long training jobs.

If the script has a `--help` option, optionally run:

```bash
python cajas/scripts/prepare_fx_dataset.py --help
```

### 5. Review staged content carefully

Before committing, stage only the intended files:

```bash
git add .gitignore AGENTS.md
git diff --staged --stat
git diff --staged
```

Make sure no raw data, no `tmp/`, and no `.codex/` content is staged.

### 6. Commit repository rules

Create the first commit:

```bash
git commit -m "docs: add agent workflow and git ignore rules"
```

If `AGENTS.md` was already committed earlier, or if this commit has nothing to commit, do not force an empty commit. Instead report that it was already clean and continue.

### 7. Commit Phase 0 scaffold

Stage the Phase 0 research layer:

```bash
git add cajas/README.md cajas/configs/ cajas/data_examples/ cajas/scripts/
git diff --staged --stat
git diff --staged
```

Again confirm no data artifacts are staged.

Create the second commit:

```bash
git commit -m "feat: add phase 0 cajas market recognition scaffold"
```

If there is nothing to commit, report that clearly.

### 8. Final verification

Run:

```bash
git status
git log --oneline -5
```

Expected final state:

- Working tree clean, except ignored local files are okay.
- Current branch remains `cajas/market-recognition-phase-0`.
- Recent commits include the git rules commit and Phase 0 scaffold commit, unless they were already committed.

### 9. Push

If commits were created successfully, push the branch:

```bash
git push
```

If push fails because upstream tracking is missing, use:

```bash
git push -u origin cajas/market-recognition-phase-0
```

## Completion Report

When finished, report in this exact structure:

```text
Phase 0 Git hygiene completed.

Branch:
- <branch name>

Commits:
- <commit hash> <commit message>
- <commit hash> <commit message>

Ignored local paths verified:
- .codex/: yes/no
- tmp/: yes/no
- taskDocs/: yes/no

Validation:
- python -m py_compile cajas/scripts/prepare_fx_dataset.py: pass/fail/not applicable
- git status: clean/not clean

Notes:
- <any important notes, especially if a commit was skipped because it already existed>
```

## Important Project Rules

This project is currently in a research-scaffold phase.

Do not introduce trading execution, live trading, broker integration, order placement, or automatic trading behavior.

The current goal is only:

- keep Git clean,
- protect local/generated files from commits,
- preserve Qlib upstream compatibility,
- keep the new research code under `cajas/`,
- prepare the repository for future EURUSD 15m market-recognition experiments.
