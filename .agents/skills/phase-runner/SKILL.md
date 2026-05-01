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

## Phase Prompt Handling

- Phase prompts are tracked under `tasks/`.
- Read the exact phase prompt requested by the user before editing.
- Do not rerun older phases unless explicitly requested.
- If the prompt is unclear, implement the safest bounded subset and report what was deferred.

## Project Boundaries

Unless explicitly requested by the phase prompt:

- Do not modify `qlib/` core.
- Do not modify upstream official examples.
- Do not train models.
- Do not build, fit, predict, evaluate, or serialize models.
- Do not run backtests, profit analysis, or trading strategy logic.
- Do not add live trading, broker execution, order submission, or position sizing.
- Do not treat `future_direction_8` as a buy/sell signal.
- Do not enable `training.enabled` in YAML.
- Do not install new runtime dependencies automatically.

## Files and Data

- Do not commit raw CSV/data files.
- Do not commit `tmp/`, `.codex/`, `.agents/`, generated model artifacts, or generated preview artifacts.
- Do commit source code, tests, docs, configs, and phase prompts under `tasks/`.
- Do not add `tasks/` to `.gitignore`.

## Python Environment

- Use `./.venv-qlib313/bin/python` for Python commands.
- Do not assume `python` exists on PATH.
- Use `pytest` from the project venv.
- Prefer targeted validation first, then broader validation when appropriate.

## Validation

Before editing:

```bash
git status --short
git branch --show-current
