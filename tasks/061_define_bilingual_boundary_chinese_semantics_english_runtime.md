# Task 061 — Define Bilingual Boundary: Chinese Semantics, English Runtime

## Context

We refined the language strategy for the EURUSD 15m pattern-review system.

Final principle:

- Do not fully localize the system into Chinese.
- Use Chinese only where semantic judgment, human reasoning, review standards, examples, counterexamples, and future LLM instructions benefit from native-language precision.
- Keep the runtime system fully English-facing: code, schema keys, filenames, CLI args, tests, logs, report identifiers, and machine status values should remain English.

This boundary matters because:

- Human review rationale needs maximum semantic clarity.
- Future LLM review should align with human Chinese reasoning.
- Engineering systems need stable English identifiers and predictable tooling.
- Full Chinese localization would create unnecessary code/tooling ambiguity.

Current constraints:

- Work directly on `main`.
- CSV + JSONL durable storage only.
- No SQLite.
- No old CSV/JSON compatibility or migration burden.
- No trading signals, no orders, no position sizing, no model training.
- No live LLM API calls yet unless explicitly approved.
- Prefer clean replacement over legacy wrapping.

## Goal

Create a clear bilingual boundary policy and apply it to the EURUSD review workflow.

The result should prevent accidental full localization while still making Chinese semantic content first-class.

## Required Policy

Add or update documentation with this policy:

### English Runtime Layer

The following must remain English:

- Python module names
- function names
- class names
- schema keys
- CSV column names
- JSON/JSONL keys
- CLI flags
- filenames
- test names
- status enums
- validation report keys
- machine logs
- automation/report identifiers

Examples:

```json
{
  "human_label": "uncertain",
  "human_confidence": "medium",
  "human_rationale_zh": "这里下影线明显，但前置结构并不是清晰下跌后的拒绝，更像震荡中的随机波动。",
  "standard_version": "eurusd_15m_review_standard_v0"
}
```

### Chinese Semantic Layer

The following should use Chinese as authoritative semantic content:

- human review rationale
- human counterexample explanation
- uncertainty reason
- market context notes
- pattern definition text
- valid/invalid/uncertain examples
- future LLM instructions
- future LLM supporting/counter observations
- standard revision explanations

Chinese semantic fields should use explicit `_zh` suffix where useful, for example:

- `human_rationale_zh`
- `human_counterexample_zh`
- `human_uncertainty_reason_zh`
- `human_context_notes_zh`
- `supporting_observations_zh`
- `counter_observations_zh`
- `uncertainty_reason_zh`

### Prohibited Direction

Avoid:

- Chinese schema keys
- Chinese filenames for code or data artifacts
- Chinese CLI flags
- Chinese enum values
- mixed-language field names without convention
- English-only human rationale that loses semantic precision
- treating Chinese rationale as optional debug text

## Implementation Targets

Inspect and update as appropriate:

- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `cajas/docs/eurusd_review_language_policy.md` if present
- `cajas/docs/eurusd_llm_review_standard_v0.md` if present
- `tasks/eurusd_15m_research_end_to_end_roadmap.md`
- `cajas/research/eurusd_pattern_review_gui.py`
- `cajas/apps/eurusd_pattern_review_app.py`
- `cajas/reports/validation_eurusd_pattern_review_gui.py`
- `cajas/tests/test_validation_eurusd_pattern_review_gui.py`

Add or update validation if useful:

- `cajas/reports/validation_eurusd_language_boundary.py`
- `cajas/scripts/build_eurusd_language_boundary_report.py`
- `cajas/tests/test_validation_eurusd_language_boundary.py`

## Validation Report

Generate a report that confirms:

- English runtime policy is documented.
- Chinese semantic policy is documented.
- `_zh` field convention is documented.
- Forbidden full-localization directions are documented.
- Machine-facing identifiers remain English.
- Status: `language_boundary_ready` or `blocked`.

Suggested outputs:

- `tmp/validation-eurusd-language-boundary.json`
- `tmp/validation-eurusd-language-boundary.md`

## Validation Commands

Run focused tests:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python -m pytest   cajas/tests/test_validation_eurusd_language_boundary.py   cajas/tests/test_validation_eurusd_pattern_review_gui.py
```

Run compile and hygiene:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python -m py_compile   cajas/reports/validation_eurusd_language_boundary.py   cajas/scripts/build_eurusd_language_boundary_report.py

git diff --check

PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Run fast validation if implementation changes are non-trivial:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py   --tier fast   --timing-json tmp/fast_validation_latest.json
```

## Expected Final State

- Chinese is authoritative only for semantic human/LLM review content.
- English remains authoritative for runtime, code, schema, tests, and automation.
- `_zh` fields are the bridge between engineering stability and Chinese semantic precision.
- No full Chinese localization of the runtime system.
- No trading signals, no orders, no position sizing, no model training.
- Commit directly on `main`.
