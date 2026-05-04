# Tasks Archive

This directory stores historical phase prompts for the Qlib Base / qlib-cajas project.

The root `tasks/` directory should stay small. Historical prompts should be archived here after they are no longer the active working prompt.

## Archive Structure

```text
tasks/archive/
  qlib_base_infrastructure/
  eurusd_research/
  superseded_or_local/
```

### `qlib_base_infrastructure/`

Use this directory for historical prompts related to:

- Qlib Base infrastructure
- dataset quality
- schema contracts
- golden fixtures
- drift detection
- runtime budget
- validation bundles
- history/alias migration
- release readiness
- final reviewer packets
- maintenance continuation
- post-merge validation
- generic validation/runtime/governance hardening

### `eurusd_research/`

Use this directory for prompts related to the EURUSD 15m research track:

- EURUSD dataset audit
- OHLC anomaly triage
- clean dataset view
- pattern feature scaffold
- pattern candidate pack
- review QA
- label schema
- review template
- review feedback
- review batch
- GUI review app
- completed-batch intake
- future outcome analysis

### `superseded_or_local/`

Use this directory for:

- superseded prompt drafts
- local/generated prompt variants
- older roadmap/archive cleanup prompts
- temporary prompts that are useful for history but not active

## Root Tasks Policy

Root `tasks/` should normally contain only:

```text
tasks/eurusd_15m_research_end_to_end_roadmap.md
tasks/phase_6086_6205_eurusd_15m_local_review_gui_prompt.md
tasks/phase_6326_6445_tasks_prompt_cleanup_archive_prompt.md
```

Future active phase prompts may temporarily live at root while they are being used. After the phase is completed, move them into the appropriate archive directory.

## Master Roadmap

The human-facing project overview is:

```text
tasks/eurusd_15m_research_end_to_end_roadmap.md
```

This roadmap is the main long-term reference for:

- project purpose
- scope boundaries
- completed milestones
- current artifact map
- GUI review workflow
- future outcome-analysis path

Do not replace it with a short stub.

## Move Policy

For tracked prompt files, use:

```bash
git mv old_path new_path
```

For untracked prompt files, use `mv` and then `git add` only if the file should be preserved.

Do not leave helper scripts such as these in the working tree:

```text
move_tasks.py
move_tasks.sh
tracked_tasks.txt
```

Do not delete tracked prompts unless there is an explicit reason. Prefer archiving over deletion.

## Validation After Cleanup

After moving prompts, run:

```bash
git status --short --branch
find tasks -maxdepth 1 -type f | sort
git diff --check
find cajas -path "*/init.py" -print
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Fast validation may be skipped for docs/tasks-only cleanup, but the reason should be stated explicitly.

## Manual Merge Policy

Do not perform automated merge operations.

After review and validation, push the branch and let the human user merge manually on GitHub.
