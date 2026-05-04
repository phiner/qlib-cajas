# Phase 7646–7765 Prompt — EURUSD 15m CSV/JSONL Persistence Hardening

## Context

Work directly on `main`.

Current committed baseline:

- Commit: `d638b14e7f0d68a2fc5025eb2498f35d42187c90`
- Commit message: `fix: restore EURUSD GUI save/reset action reliability`
- GUI review workflow currently uses CSV/JSONL as durable storage/interchange.
- Do **not** add SQLite in this phase.
- Do **not** introduce trading signals, orders, broker execution, model training, or automated labels.

Current confirmed behavior:

- `Save` writes/updates the current sample in completed CSV by `sample_id`.
- `Save and Next` saves first, then advances only after successful save.
- `Reset Form` resets visible form values only and does not delete saved CSV.
- Completed rows reload into form on revisit via merged completed data.
- Required review fields persist, including notes/status/scores.
- Duplicate-safe save by `sample_id` is preserved.
- Forbidden trading/action columns are filtered.

## Goal

Harden the CSV/JSONL review persistence layer so the local GUI review loop is reliable, auditable, and easy to recover from.

This phase should keep the implementation simple:

```text
CSV = editable table / completed review state
JSONL = append-friendly audit/interchange record
JSON = validation/report metadata only
SQLite = explicitly out of scope for now
```

## Required Work

### 1. Verify CSV completed-review schema

Inspect the completed review writer/reader path and ensure the completed CSV contains all currently visible review fields required by the GUI.

Confirm at minimum:

- `sample_id`
- candidate/sample identity fields needed to rejoin with source batch
- all visible human review fields
- review notes
- review status
- numeric score/confidence fields
- timestamp/update metadata if already available

Do not invent new label semantics.

If a field is missing because it is visible in the GUI but not persisted, add it.

### 2. Add or harden JSONL persistence

Ensure each successful save can produce a JSONL record suitable for audit/interchange.

The JSONL record should include:

- `sample_id`
- current review field values
- action type, for example `save` or `save_and_next`
- source batch path or identifier if available
- completed CSV path if available
- timestamp if available
- schema/version marker if already consistent with existing conventions

Important:

- JSONL should be append-friendly.
- CSV remains duplicate-safe by `sample_id`.
- JSONL may preserve event history; CSV represents latest completed state.
- Do not let JSONL failures silently corrupt CSV save behavior. Prefer explicit status/error reporting.

### 3. Add GUI-visible persistence status

Improve the existing action status area so after save it clearly shows:

- saved sample id
- completed CSV output path
- JSONL output path if enabled/available
- whether this was a new row or update of an existing `sample_id`
- current sample index after save/save-and-next

Keep the UI compact.

### 4. Add regression tests

Extend focused GUI/research tests to cover:

- save creates or updates completed CSV by `sample_id`
- repeated save for the same sample does not duplicate CSV rows
- save-and-next advances only after save
- reset form does not delete completed CSV
- completed CSV reloads into form values on revisit
- JSONL append record is written on successful save
- JSONL record includes required identity/review fields
- forbidden trading/action columns remain filtered from durable outputs

### 5. Update docs

Update:

- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `cajas/README.md`
- `tasks/eurusd_15m_research_end_to_end_roadmap.md`

Document clearly:

- current durable storage is CSV/JSONL only
- SQLite is intentionally deferred
- CSV is latest editable state
- JSONL is append/audit/interchange history
- GUI is still review-only
- no automated labels/trading/model training are introduced

## Validation Commands

Run:

```bash
./.venv-qlib313/bin/python -m pytest   cajas/tests/test_eurusd_pattern_review_gui.py   cajas/tests/test_validation_eurusd_pattern_review_gui.py

./.venv-qlib313/bin/python -m py_compile   cajas/apps/eurusd_pattern_review_app.py   cajas/research/eurusd_pattern_review_gui.py   cajas/tests/test_eurusd_pattern_review_gui.py

./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py   --tier fast   --timing-json tmp/fast_validation_latest.json

git diff --check
find cajas -path "*/init.py" -print
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

## Commit

Commit directly on `main`.

Suggested commit message:

```text
fix: harden EURUSD GUI CSV JSONL persistence
```

## Final Report Required

Return:

- active branch
- whether work was done on `main`
- commit hash
- files changed
- CSV persistence behavior
- JSONL persistence behavior
- validation results
- push status
- manual push command if not pushed

## Explicit Non-Goals

- Do not add SQLite.
- Do not add database migrations.
- Do not add automated trading.
- Do not add broker/order execution.
- Do not train models.
- Do not invent labels automatically.
- Do not modify Qlib core.
