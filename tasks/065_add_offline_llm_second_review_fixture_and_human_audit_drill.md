# Task 065 — Add Offline LLM Second-Review Fixture and Human Audit Drill

## Context

Task 064 completed the offline LLM second-review protocol:

- strict JSONL schema
- Chinese semantic prompt template
- protocol-only report status: `llm_second_review_protocol_ready`
- audit metrics and conservative automation readiness gates
- no live LLM API calls

Current generated report has no LLM output rows yet:

- `tmp/validation-eurusd-llm-second-review.json`
- status: `llm_second_review_protocol_ready`
- automation readiness: `not_evaluated`

Now we need a controlled offline drill that proves the validator can handle realistic second-review outputs and produce actionable human-audit metrics, without using a real LLM.

Important boundaries:

- No live LLM API calls.
- No production fake LLM outputs pretending to be real.
- Fixtures must be test/demo-only and clearly labeled.
- No trading signals, no orders, no position sizing, no model training.
- Human labels remain authoritative.
- LLM output is second-review evidence only.

## Goal

Add a deterministic offline second-review fixture and human-audit drill that demonstrates:

1. Valid LLM second-review JSONL rows can be validated.
2. Agreement/disagreement metrics work.
3. High-confidence disagreement detection works.
4. `requires_human_review` and `possible_standard_gap_zh` are surfaced.
5. Forbidden-output violations would block readiness.
6. Automation readiness remains conservative.

## Required Design

### 1. Test/Demo Fixture

Add a small fixture under a clearly non-production path, for example:

- `cajas/data_examples/eurusd_llm_second_review.example.jsonl`

The fixture should include a few rows keyed by existing or synthetic test sample IDs used by tests. It should cover:

- one agreement sample
- one disagreement sample
- one high-confidence disagreement
- one `requires_human_review=true`
- one `possible_standard_gap_zh` non-empty
- zero forbidden trading outputs in the valid fixture

Use Chinese semantic observations, for example:

```json
{
  "artifact_version": "eurusd_llm_second_review_v0",
  "source_artifact_version": "eurusd_llm_review_sample_v0",
  "sample_id": "sample_001",
  "standard_version": "eurusd_15m_review_standard_v0",
  "llm_reviewer_role": "second_reviewer",
  "llm_pattern_validity": "uncertain",
  "llm_confidence": "high",
  "supporting_observations_zh": ["目标K线存在明显下影线"],
  "counter_observations_zh": ["前置结构更接近震荡，缺少清晰下跌后的拒绝背景"],
  "uncertainty_reason_zh": "上下文不足以确认该下影线具有结构意义",
  "requires_human_review": true,
  "possible_standard_gap_zh": "标准需要进一步说明震荡区间中的长下影线是否应降级为uncertain",
  "forbidden_trade_output_present": false,
  "raw_model_name": "fixture_offline_second_reviewer",
  "review_created_at_utc": "2026-01-01T00:00:00Z"
}
```

### 2. Fixture Validation Mode

Update or extend the validator/report CLI so it can be run with:

- sample artifact JSONL
- LLM output fixture JSONL
- output report JSON/MD

Example command:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_llm_second_review_report.py   --sample-artifacts-jsonl tmp/eurusd/EURUSD_15m_llm_review_samples.jsonl   --llm-review-jsonl cajas/data_examples/eurusd_llm_second_review.example.jsonl   --output-json tmp/validation-eurusd-llm-second-review-fixture.json   --output-md tmp/validation-eurusd-llm-second-review-fixture.md
```

If the fixture uses synthetic sample IDs, tests should build a matching temporary sample artifact file instead of relying on production `tmp/` contents.

### 3. Audit Report Requirements

Report should clearly show:

- `report_status`
- `automation_readiness_status`
- source sample count
- LLM review row count
- agreement count
- disagreement count
- high-confidence disagreement count
- requires-human-review count
- possible-standard-gap count
- forbidden-output violation count
- invalid schema row count
- unknown sample ID count
- duplicate sample ID count

### 4. Blocking Fixture Test

Add a negative test fixture in test code only, not necessarily as a committed data file, that includes a forbidden output violation or invalid schema row.

The validator should report:

- `report_status=blocked`
- `automation_readiness_status=not_ready`
- forbidden violation or invalid schema count > 0

### 5. Documentation

Update docs/roadmap to clarify:

- Fixture outputs are only protocol drills.
- They are not real LLM results.
- A real LLM integration must still be added later behind explicit approval.
- Human audit remains required before any automation increase.

## Implementation Targets

Inspect and update as appropriate:

- `cajas/reports/validation_eurusd_llm_second_review.py`
- `cajas/scripts/build_eurusd_llm_second_review_report.py`
- `cajas/tests/test_validation_eurusd_llm_second_review.py`
- `cajas/docs/eurusd_llm_second_review_protocol.md`
- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `tasks/eurusd_15m_research_end_to_end_roadmap.md`

Add if useful:

- `cajas/data_examples/eurusd_llm_second_review.example.jsonl`

## Validation Commands

Run focused tests:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python -m pytest   cajas/tests/test_validation_eurusd_llm_second_review.py   cajas/tests/test_validation_eurusd_llm_review_artifacts.py
```

Run compile:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python -m py_compile   cajas/reports/validation_eurusd_llm_second_review.py   cajas/scripts/build_eurusd_llm_second_review_report.py
```

Run protocol-only report:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_llm_second_review_report.py   --sample-artifacts-jsonl tmp/eurusd/EURUSD_15m_llm_review_samples.jsonl   --output-json tmp/validation-eurusd-llm-second-review.json   --output-md tmp/validation-eurusd-llm-second-review.md
```

Run fixture audit report if the committed example fixture is compatible with current sample artifacts, otherwise keep fixture validation in tests:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_llm_second_review_report.py   --sample-artifacts-jsonl tmp/eurusd/EURUSD_15m_llm_review_samples.jsonl   --llm-review-jsonl cajas/data_examples/eurusd_llm_second_review.example.jsonl   --output-json tmp/validation-eurusd-llm-second-review-fixture.json   --output-md tmp/validation-eurusd-llm-second-review-fixture.md
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

- Offline second-review fixture/audit drill exists.
- Validator demonstrates agreement/disagreement and high-confidence disagreement metrics.
- Blocking behavior is covered by tests.
- Fixture is clearly not real LLM production output.
- Protocol-only mode still works.
- No live LLM calls.
- No human labels overwritten.
- No trading signals, no orders, no position sizing, no model training.
- Commit directly on `main`.
