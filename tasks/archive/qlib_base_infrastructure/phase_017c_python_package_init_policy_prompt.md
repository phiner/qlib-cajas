# Phase 17C Prompt: Add Persistent Python Package Init Policy

## Codex Communication Rules

- Communicate with the user in English only.
- All progress updates, questions, command summaries, and completion reports must be written in English.
- Do not use Chinese in Codex-facing interaction unless the user explicitly asks.
- Do not run `git push`.
- Stop after local commits and report the exact `git push` command for the user to run manually.

## Repository

Repository working directory:

```text
/home/phiner/projects/research/qlib-cajas/
```

Current branch:

```text
cajas/market-recognition-phase-0
```

## Context

Across recent phases, Python package initializer files have repeatedly been reported or created as:

```text
cajas/**/init.py
```

But Python package initializer files must be:

```text
cajas/**/__init__.py
```

This has already affected packages such as:

```text
cajas/handlers/
cajas/datasets/
cajas/config/
cajas/recorders/
cajas/audits/
cajas/readiness/
cajas/environment/
cajas/baseline/
cajas/qlib_compat/
```

Phase 17B is expected to clean current issues, but this Phase 17C should add persistent guardrails so the issue does not recur.

## Phase 17C Goal

Add durable repository-level and skill-level constraints to prevent future `init.py` package initializer mistakes.

Main objectives:

1. Add Python package init policy to `AGENTS.md`.
2. Add the same policy to `.agents/skills/phase-runner/SKILL.md` if that file exists.
3. Enhance `cajas/scripts/check_path_hygiene.py` / `cajas/quality/path_hygiene.py` to detect `cajas/**/init.py` as an error.
4. Add tests for the new path hygiene rule.
5. Run path hygiene and full relevant tests.
6. Create local commits only.
7. Do not push.

This phase is cleanup/guardrail only.

No Qlib core changes.

No Qlib init.

No workflow execution.

No training.

No model build/fit/predict/evaluate/serialize.

No trading/backtesting/profit analysis.

## Absolute Boundaries

Do not:

- Modify `qlib/` core.
- Modify official upstream examples.
- Initialize Qlib.
- Execute Qlib workflow.
- Train any model.
- Build/fit/predict/evaluate/serialize any model.
- Create predictions.
- Calculate model metrics from predictions.
- Run backtest/profit analysis.
- Add trading strategy.
- Add live trading/order execution.
- Commit raw CSV files.
- Commit `tmp/` outputs.
- Commit `.codex/`.
- Add `tasks/` to `.gitignore`.
- Create new task prompt directories.
- Treat `future_direction_8` as a buy/sell signal.
- Run `git push`.

Important exception:

- `.agents/skills/phase-runner/SKILL.md` may be modified and committed in this phase **only if it already exists** and is intentionally part of the repository workflow.
- Do not commit unrelated `.agents/` files.

## Task 1: Check State

Run:

```bash
git status --short
git branch --show-current
grep -n "tasks" .gitignore || true
git check-ignore -v tasks/phase_017b_cleanup_qlib_workflow_probe_prompt.md || true
```

Expected:

- Current branch is `cajas/market-recognition-phase-0`.
- `.gitignore` should not ignore `tasks/`.

Inspect current init mistakes:

```bash
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\.py$' || true
```

Expected end state:

```text
find cajas -path "*/init.py" -print
```

must produce no output.

## Task 2: Update AGENTS.md

Update:

```text
AGENTS.md
```

Add or update this section, without duplicating if similar text already exists:

```markdown
## Python Package Init Policy

- Python package initializer files must always be named `__init__.py`.
- Never create package initializer files named `init.py`.
- If a new Python package directory is added and package imports are needed, create `__init__.py`.
- Before every local commit, run:

```bash
find cajas -path "*/init.py" -print
```

- The command above must produce no output.
- If any `cajas/**/init.py` file exists, fix it with `git mv`:

```bash
git mv path/to/init.py path/to/__init__.py
```

- Do not report package init cleanup as complete while any `cajas/**/init.py` file remains.
```

Also ensure the existing Codex policy remains:

- English-only communication.
- Do not run `git push`.
- Create local commits after validation if the task asks for implementation/commit.

## Task 3: Update phase-runner Skill if Present

If this file exists:

```text
.agents/skills/phase-runner/SKILL.md
```

update it to include the same policy.

Important:

- The existing skill may be too generic or refer to an older repository.
- Do not rewrite the entire skill unless necessary.
- Add a concise section such as:

```markdown
## Python Package Init Policy

- Always use `__init__.py`, never `init.py`, for Python package initialization.
- Before committing, run:

```bash
find cajas -path "*/init.py" -print
```

- The command must produce no output.
- If any result appears, fix it with `git mv path/to/init.py path/to/__init__.py`.
```

Also ensure the skill does not contradict the current policy:

```text
local commits: yes
git push: no
English-only: yes
```

If the skill currently says "Do not commit unless explicitly asked" but this repository workflow expects Codex to commit after phase validation, update that wording to:

```text
Create focused local commits after validation when implementing a phase prompt. Never run git push.
```

Do not commit unrelated `.agents/` files.

## Task 4: Enhance Path Hygiene Rule

Update:

```text
cajas/quality/path_hygiene.py
cajas/scripts/check_path_hygiene.py
```

Goal:

- Detect `cajas/**/init.py` as a path hygiene issue.
- Keep existing `caixas/` and `taskDocs/` checks.
- Keep ignore behavior for `.git/`, `tmp/`, `.venv*`, `.codex/`, `__pycache__/`.
- Do not ignore `cajas/**/init.py`.

Suggested issue:

```text
pattern: "cajas/**/init.py"
message: "Python package initializer must be named __init__.py, not init.py."
```

The checker should catch:

```text
cajas/foo/init.py
cajas/foo/bar/init.py
```

But should not flag:

```text
cajas/foo/__init__.py
```

If the current path hygiene implementation only scans file contents and not file paths, extend it to also check scanned file paths.

## Task 5: Add or Update Tests

Update:

```text
cajas/tests/test_path_hygiene.py
```

Add tests for:

1. `caixas/` typo still detected.
2. `taskDocs/` still detected unless explicitly allowed.
3. `cajas/example/init.py` is detected as an issue.
4. `cajas/example/__init__.py` is not detected.
5. ignored directories such as `tmp/` and `.venv-qlib313/` are skipped.
6. report serialization remains stable.

Use temporary directories/files only.

## Task 6: Fix Existing init.py Files If Any

Run:

```bash
find cajas -path "*/init.py" -print
```

For each result, fix with:

```bash
git mv <path>/init.py <path>/__init__.py
```

If the file is untracked, use normal `mv`, then stage the correct `__init__.py`.

After fixes, rerun:

```bash
find cajas -path "*/init.py" -print
```

It must produce no output.

## Task 7: Validation Commands

Run:

```bash
git status --short
git branch --show-current
```

Run the package init check:

```bash
find cajas -path "*/init.py" -print
```

Expected:

- no output.

Compile changed Python files:

```bash
./.venv-qlib313/bin/python -m py_compile \
  cajas/quality/path_hygiene.py \
  cajas/scripts/check_path_hygiene.py
```

Run path hygiene:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py --json
```

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_path_hygiene.py
```

Run broader tests that are likely affected by package init exports and path hygiene:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_path_hygiene.py \
  cajas/tests/test_qlib_probe.py \
  cajas/tests/test_dataset_shape_probe.py \
  cajas/tests/test_prepared_dataset_h_like.py \
  cajas/tests/test_prepared_dataset_h_adapter.py \
  cajas/tests/test_adapter_comparison_probe.py \
  cajas/tests/test_qlib_workflow_config_probe.py
```

If time is reasonable, run the full suite:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests
```

Run:

```bash
git diff --check
git diff --stat
git status --short
```

Confirm:

- No `cajas/**/init.py`.
- No `caixas/` active references.
- `tmp/` artifacts are not staged.
- raw CSV is not staged.
- `.codex/` is not staged.
- unrelated `.agents/` files are not staged.

## Suggested Commits

Prefer focused commits.

### Commit 1: Phase 17C prompt

```bash
git add tasks/phase_017c_python_package_init_policy_prompt.md
git commit -m "docs: add phase 17C package init policy prompt"
```

### Commit 2: policy docs/skill

```bash
git add AGENTS.md
```

If `.agents/skills/phase-runner/SKILL.md` exists and was intentionally updated:

```bash
git add .agents/skills/phase-runner/SKILL.md
```

Then:

```bash
git commit -m "docs: add python package init policy"
```

### Commit 3: path hygiene enforcement

```bash
git add cajas/quality/path_hygiene.py \
  cajas/scripts/check_path_hygiene.py \
  cajas/tests/test_path_hygiene.py
git commit -m "test: enforce python package init path hygiene"
```

### Commit 4: init.py renames if any

If any existing `init.py` files were renamed:

```bash
git add -u cajas
git add cajas
git commit -m "fix: rename package init files to standard names"
```

Skip any commit with no changes.

Do not run `git push`.

Report:

```bash
git push origin cajas/market-recognition-phase-0
```

## Completion Report Format

Report exactly in English:

```text
Phase 17C completed.

Branch:
- cajas/market-recognition-phase-0

Policy updates:
- AGENTS.md updated:
- phase-runner skill updated:
- local commits enabled:
- git push disabled:

Package init check:
- incorrect init.py files before:
- incorrect init.py files after:
- command result:

Path hygiene:
- init.py rule added:
- caixas rule still active:
- taskDocs rule still active:
- status:

Changed files:
- ...

Validation commands run:
- ...

Tests:
- focused:
- broader/full:

Git:
- local commit(s):
- push: not run by Codex
- manual push command: git push origin cajas/market-recognition-phase-0

Untracked intentionally left:
- .agents/ unrelated files if present

Notes:
- ...
```

## Forbidden Work

Do not:

- Modify `qlib/` core.
- Modify official examples.
- Initialize Qlib.
- Execute Qlib workflow.
- Train any model.
- Build/fit/predict/evaluate/serialize any model.
- Create predictions.
- Calculate model metrics from predictions.
- Run backtest/profit analysis.
- Add trading strategy.
- Add live trading/order execution.
- Commit raw CSV files.
- Commit `tmp/` outputs.
- Commit `.codex/`.
- Commit unrelated `.agents/` files.
- Add `tasks/` to `.gitignore`.
- Create new task prompt directories.
- Treat `future_direction_8` as a buy/sell signal.
- Run `git push`.
