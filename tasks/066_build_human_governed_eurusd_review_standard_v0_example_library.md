# Task 066 — Build Human-Governed EURUSD Review Standard v0 Example Library

## Context

Tasks 061–065 established the LLM handoff foundation:

- Task 061: bilingual boundary policy (`language_boundary_ready`)
- Task 062: first-class Chinese rationale fields (`zh_rationale_fields_ready`)
- Task 063: deterministic LLM-ready sample artifact export (`llm_review_artifacts_ready`)
- Task 064: offline LLM second-review protocol (`llm_second_review_protocol_ready`)
- Task 065: offline fixture/audit drill (`llm_second_review_outputs_ready` for drill fixture, automation not ready)

The next bottleneck is not tooling. The bottleneck is human-governed semantic standard quality.

Before any real LLM integration, we need a versioned Chinese review standard v0 with examples and counterexamples. This standard is what future LLM second reviewers must follow.

Important boundaries:

- No live LLM API calls.
- No trading signals, no orders, no position sizing, no model training.
- Human standard remains authoritative.
- Examples are semantic review examples, not trade setups.
- English runtime identifiers remain unchanged.
- Chinese is authoritative for rationale, examples, and standard explanation.

## Goal

Create a human-governed EURUSD 15m pattern review standard v0 example library.

The library should define and validate example/counterexample entries that can later be referenced by:

- human reviewers
- future LLM second-review prompts
- audit reports
- standard revision workflows

## Required Standard Document

Add or update:

- `cajas/docs/eurusd_llm_review_standard_v0.md`

The document should include:

1. Scope and non-scope
2. Language/runtime boundary reminder
3. Candidate type review principles
4. Valid / invalid / uncertain criteria
5. Wick-specific review guidance
6. Trend/chop/transition context guidance
7. Gap-compression caveats
8. False-positive patterns
9. Ambiguity handling
10. Forbidden outputs
11. Example library format
12. Standard revision process

All semantic explanations should be Chinese.

Machine-facing field names and enum values should remain English.

## Example Library

Add a structured example library, preferably JSONL or JSON, for example:

- `cajas/data_examples/eurusd_review_standard_v0_examples.jsonl`

Each row should use English keys and Chinese semantic values:

```json
{
  "example_id": "std_v0_lower_wick_valid_001",
  "standard_version": "eurusd_15m_review_standard_v0",
  "candidate_type": "lower_wick_rejection_candidate",
  "decision": "valid",
  "confidence": "medium",
  "rationale_zh": "目标K线出现明显下影线，且前置结构存在向下试探后的拒绝，后续K线没有立即跌破低点。",
  "counter_observation_zh": "如果后续快速跌破目标K线低点，则该样本应降级为invalid或uncertain。",
  "uncertainty_reason_zh": "",
  "context_notes_zh": "该例用于说明下影线必须结合前置下探和后续确认，而不是只看影线长度。",
  "forbidden_trade_output_present": false
}
```

Include at minimum:

- valid example
- invalid example
- uncertain example
- false-positive example
- wick-specific example
- trend/chop context example
- gap-compression caveat example

The examples may be synthetic semantic examples at first if no approved sample IDs exist yet. If sample IDs are referenced, they must be optional and clearly marked.

## Validation / Report

Add a standard/example validation report.

Suggested files:

- `cajas/reports/validation_eurusd_review_standard_v0.py`
- `cajas/scripts/build_eurusd_review_standard_v0_report.py`
- `cajas/tests/test_validation_eurusd_review_standard_v0.py`

Suggested outputs:

- `tmp/validation-eurusd-review-standard-v0.json`
- `tmp/validation-eurusd-review-standard-v0.md`

Report should validate:

- standard document exists
- language boundary is referenced
- forbidden trading/execution outputs are listed
- example library exists
- required example decisions are covered: `valid`, `invalid`, `uncertain`
- required scenario types are covered: wick, trend/chop, gap caveat, false positive
- all keys are English
- Chinese rationale fields are present
- no forbidden trading outputs are present
- status: `review_standard_v0_ready|blocked`

## Integration

Update docs/roadmap so the pipeline order is explicit:

1. Human standard v0
2. LLM-ready deterministic artifact export
3. Offline LLM second-review protocol
4. Fixture/audit drill
5. Real LLM integration only after explicit approval
6. Human audit gate before any automation increase

## Implementation Targets

Inspect and update as appropriate:

- `cajas/docs/eurusd_llm_second_review_protocol.md`
- `cajas/docs/eurusd_review_language_policy.md`
- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `tasks/eurusd_15m_research_end_to_end_roadmap.md`
- `cajas/reports/validation_eurusd_llm_second_review.py`

Add as useful:

- `cajas/docs/eurusd_llm_review_standard_v0.md`
- `cajas/data_examples/eurusd_review_standard_v0_examples.jsonl`
- `cajas/reports/validation_eurusd_review_standard_v0.py`
- `cajas/scripts/build_eurusd_review_standard_v0_report.py`
- `cajas/tests/test_validation_eurusd_review_standard_v0.py`

## Validation Commands

Run focused tests:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python -m pytest   cajas/tests/test_validation_eurusd_review_standard_v0.py   cajas/tests/test_validation_eurusd_llm_second_review.py
```

Run compile and report build:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python -m py_compile   cajas/reports/validation_eurusd_review_standard_v0.py   cajas/scripts/build_eurusd_review_standard_v0_report.py

PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_review_standard_v0_report.py   --output-json tmp/validation-eurusd-review-standard-v0.json   --output-md tmp/validation-eurusd-review-standard-v0.md
```

Run hygiene:

```bash
git diff --check

PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py

find cajas -path '*/init.py' -print
```

Run fast validation if practical, but do not block this task on the already-known unrelated 6 legacy failures. Clearly report whether failures are unchanged or new:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py   --tier fast   --timing-json tmp/fast_validation_latest.json
```

## Expected Final State

- Human-governed EURUSD review standard v0 exists.
- Chinese semantic examples and counterexamples are first-class.
- Example library is structured and validated.
- Future LLM reviewers have a concrete standard to follow.
- No live LLM calls.
- No human labels overwritten.
- No trading signals, no orders, no position sizing, no model training.
- Commit directly on `main`.
