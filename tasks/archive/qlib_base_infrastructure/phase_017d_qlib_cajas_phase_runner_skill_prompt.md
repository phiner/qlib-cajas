# Phase 17D Prompt: Make phase-runner Skill qlib-cajas Specific

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

The user wants to officially keep a repository-local Codex skill:

```text
.agents/skills/phase-runner/SKILL.md
```

The current skill was originally written for a broader `cajasTradingSystem` / Rust / kline-labeler / backtester project. It is too long and contains unrelated rules.

This phase should replace it with a concise `qlib-cajas`-specific skill.

Important:

- In this phase, committing `.agents/skills/phase-runner/SKILL.md` is allowed and intended.
- Do not commit unrelated `.agents/` files.
- Keep the skill short and focused.
- Keep the policy consistent with current project rules:
  - English-only Codex interaction.
  - Local commits allowed after validation.
  - Never run `git push`.
  - Use `./.venv-qlib313/bin/python`.
  - Never create `init.py`; always use `__init__.py`.
  - Do not train or trade unless explicitly approved by a future phase.

## Phase 17D Goal

Make the repository-local `phase-runner` skill a concise, durable, `qlib-cajas`-specific execution policy.

Main objectives:

1. Replace `.agents/skills/phase-runner/SKILL.md` with a concise qlib-cajas-specific version.
2. Ensure it includes local commit yes / push no.
3. Ensure it includes Python package `__init__.py` policy.
4. Ensure it includes current project safety boundaries.
5. Ensure it includes validation defaults.
6. Ensure it does not mention old `cajasTradingSystem`, Rust, kline-labeler, broker, backtester, or annotation workflow unless directly relevant to `qlib-cajas`.
7. Commit only the skill and this prompt if present.
8. Do not push.

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

## Task 1: Check Current State

Run:

```bash
git status --short
git branch --show-current
```

Expected:

- Branch is `cajas/market-recognition-phase-0`.

Also run:

```bash
find .agents -maxdepth 4 -type f -print 2>/dev/null | sort
```

Identify `.agents/skills/phase-runner/SKILL.md`.

If there are unrelated `.agents/` files, do not stage them unless explicitly needed.

## Task 2: Replace phase-runner Skill With qlib-cajas Version

Update:

```text
.agents/skills/phase-runner/SKILL.md
```

Replace its content with the following concise version:

```markdown
---
name: phase-runner
description: Use for qlib-cajas phase-based development tasks. Reads phase prompts under tasks/, implements scoped changes, validates, creates local commits, and reports manual push commands. Never pushes.
---

# Phase Runner Skill for qlib-cajas

You are working inside the `qlib-cajas` repository.

## Communication

- Communicate with the user in English only.
- Keep progress updates concise and implementation-focused.
- Do not use Chinese unless explicitly requested.
- Do not promise future/background work. Perform the requested work in the current session.
- If blocked, state the exact blocker and provide the best partial result available.

## Phase Prompt Handling

- Phase prompts are tracked under `tasks/`.
- Read the exact phase prompt requested by the user before editing.
- Do not rerun older phases unless explicitly requested.
- If the prompt is unclear, implement the safest bounded subset and report what was deferred.
- Do not create new task prompt directories.
- Do not add `tasks/` to `.gitignore`.

## Project Boundaries

Unless explicitly requested by a future phase prompt:

- Do not modify `qlib/` core.
- Do not modify upstream official examples.
- Do not initialize Qlib.
- Do not execute Qlib workflows.
- Do not train models.
- Do not build, fit, predict, evaluate, or serialize models.
- Do not create predictions.
- Do not calculate model metrics from predictions.
- Do not run backtests, profit analysis, or trading strategy logic.
- Do not add live trading, broker execution, order submission, or position sizing.
- Do not treat `future_direction_8` as a buy/sell signal.
- Do not enable `training.enabled` in YAML.
- Do not install new runtime dependencies automatically.

## Files and Data

- Do not commit raw CSV/data files.
- Do not commit `tmp/`, `.codex/`, generated model artifacts, or generated preview artifacts.
- Commit `.agents/skills/phase-runner/SKILL.md` only when the user explicitly asks to version the skill.
- Do not commit unrelated `.agents/` files.
- Do commit source code, tests, docs, configs, and phase prompts under `tasks/`.

## Python Environment

- Use `./.venv-qlib313/bin/python` for Python commands.
- Do not assume `python` exists on PATH.
- Use `pytest` from the project venv.
- Prefer targeted validation first, then broader validation when appropriate.
- Use explicit `cajas/...` paths only. Never use `caixas/...`.

## Python Package Init Policy

- Python package initializer files must always be named `__init__.py`.
- Never create package initializer files named `init.py`.
- If a new Python package directory is added and package imports are needed, create `__init__.py`.
- Before every local commit, run:

```bash
find cajas -path "*/init.py" -print
```

- The command above must produce no output.
- If any `cajas/**/init.py` file exists, fix it with:

```bash
git mv path/to/init.py path/to/__init__.py
```

- Do not report package init cleanup as complete while any `cajas/**/init.py` file remains.

## Validation Defaults

Before editing:

```bash
git status --short
git branch --show-current
```

After editing, run validation requested by the phase prompt.

Always consider:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git diff --check
git status --short
```

For changed Python modules, run:

```bash
./.venv-qlib313/bin/python -m py_compile <changed_python_files>
```

For tests, use explicit `cajas/tests/...` paths only.

## Git Policy

- Create focused local commits after validation passes.
- Prefer multiple focused commits over one mixed commit.
- Use conventional commit messages:
  - `docs: ...`
  - `feat: ...`
  - `fix: ...`
  - `test: ...`
  - `chore: ...`
  - `refactor: ...`
- Never run `git push`.
- After local commits, report:
  - local commit hashes
  - `git status --short`
  - manual push command:
    `git push origin cajas/market-recognition-phase-0`

## End-of-Task Report

End every implementation task with this structure:

```text
Done.

Changed:
- ...

Files:
- ...

Validation:
- PASS: ...
- NOT RUN: ... because ...

Git:
- local commit(s):
- push: not run by Codex
- manual push command: git push origin cajas/market-recognition-phase-0

Notes / risks:
- ...
```

## Strict Defaults

- English-only interaction.
- Local commits yes.
- Push no.
- Training no.
- Model build/fit/predict/evaluate/serialize no.
- Qlib init/workflow execution no.
- Trading/backtest/profit analysis no.
- Qlib core changes no.
- Raw data/tmp artifacts no.
```

## Task 3: Check for Unrelated Old Skill Content

After writing the new skill, ensure the file no longer mentions old unrelated project areas:

```bash
grep -nE "cajasTradingSystem|kline-labeler|backtester|broker|Rust|Cargo|annotation|vocabulary|mock broker|rtk cargo" .agents/skills/phase-runner/SKILL.md || true
```

Expected:

- No output, except if a word appears only in a harmless context. Prefer no output.

## Task 4: Validate the Skill File

Run:

```bash
test -f .agents/skills/phase-runner/SKILL.md
grep -n "qlib-cajas" .agents/skills/phase-runner/SKILL.md
grep -n "Never run `git push`" .agents/skills/phase-runner/SKILL.md
grep -n "__init__.py" .agents/skills/phase-runner/SKILL.md
grep -n "find cajas -path" .agents/skills/phase-runner/SKILL.md
```

Run repository hygiene:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git diff --check
git status --short
```

Expected:

- path hygiene passes
- no `cajas/**/init.py`
- `.agents/skills/phase-runner/SKILL.md` is the only `.agents` file staged later

## Task 5: Commit Locally Only

First inspect staged/untracked files:

```bash
git status --short
```

Stage only:

```bash
git add tasks/phase_017d_qlib_cajas_phase_runner_skill_prompt.md
git add .agents/skills/phase-runner/SKILL.md
```

Do not stage unrelated `.agents/` files.

Commit:

```bash
git commit -m "docs: specialize phase runner skill for qlib-cajas"
```

Do not run `git push`.

Report manual push command:

```bash
git push origin cajas/market-recognition-phase-0
```

## Completion Report Format

Report exactly in English:

```text
Phase 17D completed.

Branch:
- cajas/market-recognition-phase-0

Skill update:
- path:
- qlib-cajas specific:
- old cajasTradingSystem content removed:
- English-only policy:
- local commit policy:
- no-push policy:
- __init__.py policy:
- validation defaults:

Changed files:
- ...

Validation commands run:
- ...

Git:
- local commit(s):
- push: not run by Codex
- manual push command: git push origin cajas/market-recognition-phase-0

Notes:
- ...
```
