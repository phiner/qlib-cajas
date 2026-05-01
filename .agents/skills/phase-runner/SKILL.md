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
