# Task 062 — Make Chinese Human Rationale Fields First-Class in EURUSD Review Records

## Context

Task 061 is complete. The project now has a formal bilingual boundary policy:

- English is authoritative for runtime identifiers, schema keys, filenames, CLI args, tests, reports, and machine status values.
- Chinese is authoritative for semantic human reasoning, review standards, examples, counterexamples, and future LLM-facing instructions.
- The language-boundary report is `language_boundary_ready`.

Now the next step is to make Chinese human rationale real in the active EURUSD review workflow, not only documented.

Current constraints:

- Work directly on `main`.
- CSV + JSONL durable storage only.
- No SQLite.
- No old CSV/JSON compatibility or migration burden.
- No live LLM API calls yet.
- No trading signals, no orders, no position sizing, no model training.
- Prefer clean replacement over legacy wrapping.
- The system runtime remains English; semantic content fields may carry Chinese text using English keys with `_zh` suffix.

## Goal

Promote Chinese human rationale fields to first-class review-record fields across the active EURUSD 15m review workflow.

This means the GUI, persistence helpers, validation reports, and tests should recognize Chinese rationale fields as core review data, not optional debug text.

## Required Fields

Add/support the following fields in active review records where appropriate:

- `human_rationale_zh`
- `human_counterexample_zh`
- `human_uncertainty_reason_zh`
- `human_context_notes_zh`

Keep existing machine-facing fields in English, for example:

- `sample_id`
- `candidate_type`
- `human_label`
- `human_confidence`
- `standard_version`
- `review_updated_at_utc`

Do not introduce Chinese schema keys.

## GUI Requirements

Update the review GUI so human semantic reasoning is easy to enter.

Suggested layout:

1. Keep the compact current review controls.
2. Add Chinese text areas with clear labels:
   - `Human rationale (ZH)` / `人工判断理由`
   - `Counterexample notes (ZH)` / `反例/否定理由`
   - `Uncertainty reason (ZH)` / `不确定原因`
   - `Context notes (ZH)` / `上下文备注`
3. Preserve existing compact save feedback behavior.
4. Do not add large persistent banners.
5. Do not add legacy/migration UI.
6. Do not require every rationale field to be non-empty yet, but fields must persist when entered.

## Persistence Requirements

CSV:

- Treat CSV as authoritative latest state by `sample_id`.
- Include the new `_zh` fields as columns.
- Saving the same sample again should update the latest row by `sample_id`.

JSONL:

- Continue append-only audit events.
- Include the new `_zh` fields in save events.
- Do not backfill or migrate old data.
- Do not add compatibility aliases.

## Validation / Reporting

Extend existing GUI validation or add a focused report to confirm:

- bilingual policy is present
- required `_zh` rationale fields are known
- CSV persistence includes `_zh` fields
- JSONL audit persistence includes `_zh` fields
- GUI exposes rationale inputs
- no Chinese schema keys are introduced
- status: `zh_rationale_fields_ready` or `blocked`

Suggested outputs if adding a dedicated report:

- `tmp/validation-eurusd-zh-rationale-fields.json`
- `tmp/validation-eurusd-zh-rationale-fields.md`

## Implementation Targets

Inspect and update as appropriate:

- `cajas/apps/eurusd_pattern_review_app.py`
- `cajas/research/eurusd_pattern_review_gui.py`
- `cajas/reports/validation_eurusd_pattern_review_gui.py`
- `cajas/tests/test_eurusd_pattern_review_gui.py`
- `cajas/tests/test_validation_eurusd_pattern_review_gui.py`
- `cajas/docs/eurusd_review_language_policy.md`
- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `tasks/eurusd_15m_research_end_to_end_roadmap.md`

Add new files only if useful:

- `cajas/reports/validation_eurusd_zh_rationale_fields.py`
- `cajas/scripts/build_eurusd_zh_rationale_fields_report.py`
- `cajas/tests/test_validation_eurusd_zh_rationale_fields.py`

## Validation Commands

Run focused tests first:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python -m pytest   cajas/tests/test_eurusd_pattern_review_gui.py   cajas/tests/test_validation_eurusd_pattern_review_gui.py
```

If a dedicated report/test is added, include it:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python -m pytest   cajas/tests/test_validation_eurusd_zh_rationale_fields.py
```

Run compile and hygiene:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python -m py_compile   cajas/apps/eurusd_pattern_review_app.py   cajas/research/eurusd_pattern_review_gui.py   cajas/reports/validation_eurusd_pattern_review_gui.py

git diff --check

PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py

find cajas -path '*/init.py' -print
```

Run fast validation if practical, but do not block this task on already-known unrelated legacy failures. Clearly report whether failures are new or pre-existing:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py   --tier fast   --timing-json tmp/fast_validation_latest.json
```

## Expected Final State

- Chinese human rationale fields are part of active review records.
- GUI supports entering Chinese rationale without disrupting compact workflow.
- CSV latest-state persistence includes `_zh` fields.
- JSONL audit events include `_zh` fields.
- Validation confirms the bilingual boundary is respected.
- No Chinese runtime keys, filenames, CLI args, enum values, or status values.
- No old-data migration or compatibility wrappers.
- No live LLM calls.
- No trading signals, no orders, no position sizing, no model training.
- Commit directly on `main`.
