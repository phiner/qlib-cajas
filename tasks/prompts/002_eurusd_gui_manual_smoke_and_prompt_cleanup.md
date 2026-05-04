# 002 — EURUSD GUI Manual Smoke and Prompt Cleanup

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Recent commit:
- `3eef1903`
- Fixed EURUSD GUI Save-and-Next sample index session-state regression.
- CSV/JSONL persistence remains authoritative/current scope.
- SQLite is deferred.
- No trading signals/orders/model training/Qlib core changes.

Current reported status:
- Active branch: `main`
- Git status: clean
- Manual GUI smoke was not run in the previous session.
- A phase prompt file was committed:
  - `tasks/phase_8126_8245_eurusd_15m_gui_sample_index_state_fix_prompt.md`

User preference:
- Use simple sequential prompt numbering going forward.
- Clean/delete old `phase_*.md` prompt files.
- Keep important roadmap docs.
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.

## Objective

Do two things:

1. Run a manual/local GUI smoke checklist for the fixed Save / Save and Next / Reset behavior.
2. Clean old phase prompt markdown files and establish the simple sequential prompt convention.

## Part A — Manual GUI Smoke

Run:

```bash
./scripts/run_eurusd_review_gui.sh
```

Then manually check:

1. Open the EURUSD 15m review GUI.
2. Pick a sample.
3. Change at least one review field.
4. Click `Save`.
5. Confirm:
   - green success status appears
   - no red error
   - completed CSV is updated
   - JSONL event is appended
   - sample index does not advance
6. Change at least one review field again.
7. Click `Save and Next`.
8. Confirm:
   - green success status appears
   - no red error
   - sample advances exactly one row
   - no `st.session_state.sample_idx cannot be modified` error
9. Navigate back to the prior sample.
10. Confirm completed values reload from completed CSV.
11. Click `Reset Form`.
12. Confirm:
   - visible form values reset to defaults
   - completed CSV is not deleted
   - JSONL is not deleted
   - sample index does not advance
13. Watch terminal for repeated Streamlit session-state warnings related to sample index or review widgets.

If a GUI issue remains, fix only that GUI issue and add/adjust regression tests.

## Part B — Clean Phase Prompt Markdown Files

Inspect:

```bash
find tasks -maxdepth 3 -type f | sort
```

Delete old generated phase prompt files, including:

```text
tasks/phase_*.md
tasks/phase_*_prompt.md
```

In particular, remove or migrate:

```text
tasks/phase_8126_8245_eurusd_15m_gui_sample_index_state_fix_prompt.md
```

Do not delete:
- `tasks/eurusd_15m_research_end_to_end_roadmap.md`
- `tasks/README.md` if present
- high-level roadmap/status docs
- docs under `cajas/docs/`
- generated data under `tmp/`

Create/update:

```text
tasks/README.md
```

Document the new convention:

```text
tasks/prompts/001_<short_topic>.md
tasks/prompts/002_<short_topic>.md
tasks/prompts/003_<short_topic>.md
```

Rules:
- Use 3-digit sequential IDs.
- Use short snake_case topic names.
- Do not use large phase ranges for small fixes.
- Keep only currently useful prompts.
- Delete stale prompts after work is completed.
- Roadmaps may stay in `tasks/` root.

Create:

```text
tasks/prompts/
```

Optionally keep only the current active next prompt as:

```text
tasks/prompts/002_eurusd_gui_manual_smoke_and_prompt_cleanup.md
```

Do not keep multiple old phase prompts.

## Reference Cleanup

Search and update stale references:

```bash
grep -R "phase_.*prompt" -n README.md cajas tasks scripts .github 2>/dev/null || true
grep -R "tasks/phase_" -n README.md cajas tasks scripts .github 2>/dev/null || true
```

Update references to the new sequential prompt path or remove stale references.

## Validation

Run:

```bash
git diff --check
find cajas -path "*/init.py" -print
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Run focused tests if GUI code changed:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_eurusd_pattern_review_gui.py cajas/tests/test_validation_eurusd_pattern_review_gui.py
```

Run py_compile if Python changed:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py cajas/tests/test_eurusd_pattern_review_gui.py
```

Run fast validation if Python changed or if you want a full confidence check:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/fast_validation_latest.json
```

## Commit

Work directly on `main`.

Suggested commit message if only docs/tasks changed:

```bash
git add tasks
git commit -m "docs: clean up task prompt numbering"
```

Suggested commit message if GUI fixes were needed too:

```bash
git add cajas tasks
git commit -m "fix: finalize EURUSD GUI save-next smoke cleanup"
```

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Manual GUI smoke result
- Whether Save works
- Whether Save and Next works
- Whether Reset works
- Whether CSV persisted correctly
- Whether JSONL appended correctly
- Whether Streamlit sample_idx error is gone
- Files deleted
- Files created/updated
- New prompt numbering convention
- Remaining files under `tasks/`
- Whether any `phase_*.md` prompt files remain, and why
- Validation command results
- `git status --short`
- Push status: not pushed
- Manual push command:

```bash
git push origin main
```

## Hard Boundaries

Do not:
- create branches
- push automatically
- merge automatically
- add SQLite
- introduce trading signals/orders
- train models
- modify Qlib core
- delete completed review CSV/JSONL data
