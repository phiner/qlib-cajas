# Task 064 — Define Offline LLM Second-Review Protocol for EURUSD Artifacts

## Context

Task 061 established the bilingual boundary:

- English runtime identifiers.
- Chinese-authoritative semantic reasoning.

Task 062 made Chinese rationale fields first-class:

- `human_rationale_zh`
- `human_counterexample_zh`
- `human_uncertainty_reason_zh`
- `human_context_notes_zh`

Task 063 added deterministic LLM-ready sample artifact export:

- `tmp/eurusd/EURUSD_15m_llm_review_samples.jsonl`
- report status: `llm_review_artifacts_ready`

Now we need the next layer: define how a future LLM second reviewer must respond to those artifacts, without adding live LLM API calls yet.

Important boundaries:

- No live LLM API calls in this task.
- No trading signals, no orders, no position sizing, no model training.
- LLM is a second reviewer only, not final authority.
- Human labels and human rationale remain authoritative.
- Deterministic code must validate LLM outputs before they can be used for audit.

## Goal

Create an offline LLM second-review protocol that defines:

1. The future LLM reviewer role.
2. The exact input artifact boundary.
3. The required output schema.
4. Forbidden outputs.
5. Validation rules for LLM output JSONL.
6. Human audit comparison metrics.
7. Automation readiness gates.

This task should produce docs, schema helpers, validation/reporting, and tests, but no live model integration.

## Required LLM Output Schema

Define a strict JSONL output row shape, one row per reviewed sample:

```json
{
  "artifact_version": "eurusd_llm_second_review_v0",
  "source_artifact_version": "eurusd_llm_review_sample_v0",
  "sample_id": "...",
  "standard_version": "eurusd_15m_review_standard_v0",
  "llm_reviewer_role": "second_reviewer",
  "llm_pattern_validity": "valid|invalid|uncertain",
  "llm_confidence": "low|medium|high",
  "supporting_observations_zh": [],
  "counter_observations_zh": [],
  "uncertainty_reason_zh": "",
  "requires_human_review": true,
  "possible_standard_gap_zh": "",
  "forbidden_trade_output_present": false,
  "raw_model_name": "",
  "review_created_at_utc": ""
}
```

Rules:

- Keys must remain English.
- Semantic explanatory values should be Chinese.
- `llm_pattern_validity` must not contain trading actions.
- `forbidden_trade_output_present` must be false for valid output.
- Empty arrays/strings are allowed only where documented.
- Output must be keyed by `sample_id`.
- Do not overwrite human labels.

## Future LLM Prompt Template

Add a Chinese semantic prompt template in documentation only.

It should tell the model:

- You are an EURUSD 15m pattern second reviewer.
- Read only the provided deterministic sample artifact.
- Use the Chinese review standard and human rationale if present.
- Judge only whether the candidate pattern is valid, invalid, or uncertain.
- Provide supporting and counter observations in Chinese.
- Flag uncertainty and standard gaps.
- Never produce trading signals, entries, exits, position sizes, PnL predictions, or execution instructions.
- Return strict JSON matching the schema.

Suggested doc:

- `cajas/docs/eurusd_llm_second_review_protocol.md`

## Validator / Report

Add a validator/report for offline LLM review outputs.

Suggested files:

- `cajas/reports/validation_eurusd_llm_second_review.py`
- `cajas/scripts/build_eurusd_llm_second_review_report.py`
- `cajas/tests/test_validation_eurusd_llm_second_review.py`

The validator should accept:

- input sample artifact JSONL
- optional LLM review output JSONL
- output JSON report
- output Markdown report

If LLM output JSONL is absent, the report should still pass as protocol-ready but indicate no LLM review rows yet.

Suggested statuses:

- `llm_second_review_protocol_ready`
- `llm_second_review_outputs_ready`
- `blocked`

Report fields:

- protocol version
- source artifact row count
- LLM review row count
- missing output row count
- duplicate `sample_id` count
- invalid schema row count
- forbidden-output violation count
- unknown sample_id count
- agreement count with human labels where available
- disagreement count
- high-confidence disagreement count
- requires-human-review count
- possible-standard-gap count
- automation readiness status:
  - `not_evaluated`
  - `not_ready`
  - `watch`
  - `ready_for_limited_trial`

## Human Audit Metrics

If both sample artifacts and LLM outputs are present, compare:

- human label vs. `llm_pattern_validity`
- confidence distribution
- high-confidence disagreements
- samples requiring human review
- standard-gap notes
- forbidden-output violations

Do not mutate or overwrite human review CSV.

## Automation Readiness Gate

Document and implement conservative gate logic.

Minimum conditions for `ready_for_limited_trial` should include:

- zero forbidden-output violations
- zero invalid schema rows
- zero unknown sample IDs
- duplicate sample IDs = 0
- LLM output coverage above a configured threshold
- high-confidence disagreement rate below a configured threshold
- human audit coverage documented or explicitly pending

Default status should remain `not_evaluated` or `not_ready` when no LLM output exists.

## Optional Fixture

Add a tiny deterministic fixture JSONL in tests only that simulates LLM second-review output.

It should include:

- one agreement sample
- one disagreement sample
- one `requires_human_review`
- one possible standard gap
- no trading output

Do not put fake production LLM outputs into `tmp/` as real results unless clearly generated by tests.

## Implementation Targets

Inspect and update as appropriate:

- `cajas/reports/validation_eurusd_llm_review_artifacts.py`
- `cajas/docs/eurusd_review_language_policy.md`
- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `tasks/eurusd_15m_research_end_to_end_roadmap.md`

Add as useful:

- `cajas/docs/eurusd_llm_second_review_protocol.md`
- `cajas/reports/validation_eurusd_llm_second_review.py`
- `cajas/scripts/build_eurusd_llm_second_review_report.py`
- `cajas/tests/test_validation_eurusd_llm_second_review.py`

## Validation Commands

Run focused tests:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python -m pytest   cajas/tests/test_validation_eurusd_llm_second_review.py   cajas/tests/test_validation_eurusd_llm_review_artifacts.py
```

Run compile and report build:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python -m py_compile   cajas/reports/validation_eurusd_llm_second_review.py   cajas/scripts/build_eurusd_llm_second_review_report.py

PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_llm_second_review_report.py   --sample-artifacts-jsonl tmp/eurusd/EURUSD_15m_llm_review_samples.jsonl   --output-json tmp/validation-eurusd-llm-second-review.json   --output-md tmp/validation-eurusd-llm-second-review.md
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

- Offline LLM second-review protocol is documented.
- Strict LLM output schema is defined and validated.
- Future LLM prompt boundary exists in Chinese semantic form.
- Validator can run with no LLM outputs and report protocol-ready.
- Validator can compare simulated LLM outputs against human labels in tests.
- Automation readiness gate is conservative and measurable.
- No live LLM calls.
- No human labels overwritten.
- No trading signals, no orders, no position sizing, no model training.
- Commit directly on `main`.
