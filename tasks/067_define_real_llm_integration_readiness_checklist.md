# Task 067 — Define Real LLM Integration Readiness Checklist for EURUSD Second Review

## Context

Tasks 061–066 established the full offline foundation for future LLM-assisted EURUSD review:

- Task 061: bilingual boundary policy (`language_boundary_ready`)
- Task 062: first-class Chinese rationale fields (`zh_rationale_fields_ready`)
- Task 063: deterministic LLM-ready sample artifact export (`llm_review_artifacts_ready`)
- Task 064: offline LLM second-review protocol (`llm_second_review_protocol_ready`)
- Task 065: fixture/audit drill (`llm_second_review_outputs_ready` for drill fixture, automation not ready)
- Task 066: human-governed review standard v0 and example library (`review_standard_v0_ready`)

Now define what must be true before any real LLM provider/API integration can be approved.

Important boundaries:

- Do not add live LLM API calls in this task.
- Do not add provider SDKs.
- Do not add API keys or environment variable requirements for providers yet.
- No trading signals, no orders, no position sizing, no model training.
- Human standard remains authoritative.
- Real LLM integration requires explicit future approval after this readiness checklist.

## Goal

Create a real LLM integration readiness checklist/report that verifies all prerequisites are present before online LLM second-review integration.

This report should answer:

- Is the human-governed standard ready?
- Is the deterministic artifact export ready?
- Is the second-review schema/protocol ready?
- Is the audit drill ready?
- Are forbidden-output boundaries present?
- Are human audit gates documented?
- Are automation-readiness gates conservative?
- Is the system still offline-only?
- What remains before real LLM integration?

## Required Readiness Report

Add a report/CLI that reads existing reports/docs/artifacts and summarizes readiness.

Suggested files:

- `cajas/reports/validation_eurusd_real_llm_integration_readiness.py`
- `cajas/scripts/build_eurusd_real_llm_integration_readiness_report.py`
- `cajas/tests/test_validation_eurusd_real_llm_integration_readiness.py`

Suggested outputs:

- `tmp/validation-eurusd-real-llm-integration-readiness.json`
- `tmp/validation-eurusd-real-llm-integration-readiness.md`

Suggested statuses:

- `not_ready`
- `ready_for_explicit_approval`
- `blocked`

Default should be conservative.

Since no real LLM call is allowed yet, the best current state should usually be:

- `ready_for_explicit_approval`

only if all offline prerequisites are present and no online integration is detected.

## Inputs to Check

The readiness report should check for:

1. Language boundary
   - `tmp/validation-eurusd-language-boundary.json`
   - expected status: `language_boundary_ready`

2. Chinese rationale fields
   - `tmp/validation-eurusd-zh-rationale-fields.json`
   - expected status: `zh_rationale_fields_ready`

3. LLM-ready artifacts
   - `tmp/validation-eurusd-llm-review-artifacts.json`
   - expected status: `llm_review_artifacts_ready`
   - artifact JSONL exists

4. Second-review protocol
   - `tmp/validation-eurusd-llm-second-review.json`
   - expected status: `llm_second_review_protocol_ready`

5. Fixture/audit drill
   - if fixture report exists, confirm it is drill-only and not automation-ready
   - do not require fixture report if tests already cover it, but surface status if present

6. Review standard v0
   - `tmp/validation-eurusd-review-standard-v0.json`
   - expected status: `review_standard_v0_ready`

7. Offline-only boundary
   - verify docs state no live LLM call yet
   - optionally scan relevant project files for obvious provider/API integration markers
   - do not overreach; this is a boundary reminder, not a security scanner

8. Human audit gate
   - verify docs mention human audit before automation increase

9. Forbidden outputs
   - verify trading/execution forbidden outputs are documented

## Readiness Logic

Report `ready_for_explicit_approval` only if:

- all required prerequisite reports exist and have expected statuses
- review standard v0 is ready
- deterministic artifact export is ready
- second-review protocol is ready
- no live LLM integration is detected in project files touched by this workflow
- forbidden-output boundary is present
- human audit gate is documented

Report `not_ready` if:

- optional drill is missing but all core prerequisites are present
- generated reports are missing but docs exist
- some prerequisite is pending but not broken

Report `blocked` if:

- required prerequisite report exists with blocked status
- forbidden-output boundary is missing
- live LLM integration is detected before approval
- human audit gate is missing

## Markdown Summary

The Markdown report should include:

- Current readiness status
- Prerequisite table
- Offline-only boundary statement
- Explicit approval requirement
- Remaining work before real LLM integration
- Risks and non-goals

## Documentation Updates

Update docs/roadmap to include a clear gate:

> Real LLM integration may only begin after the readiness report is `ready_for_explicit_approval` and the user explicitly approves the integration task.

Keep this explicit:

- readiness is not approval
- readiness is not automation
- readiness does not allow trading actions

## Implementation Targets

Inspect and update as appropriate:

- `cajas/docs/eurusd_llm_second_review_protocol.md`
- `cajas/docs/eurusd_llm_review_standard_v0.md`
- `cajas/docs/eurusd_review_language_policy.md`
- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `tasks/eurusd_15m_research_end_to_end_roadmap.md`

Add as useful:

- `cajas/reports/validation_eurusd_real_llm_integration_readiness.py`
- `cajas/scripts/build_eurusd_real_llm_integration_readiness_report.py`
- `cajas/tests/test_validation_eurusd_real_llm_integration_readiness.py`

## Validation Commands

Run prerequisite report builds first if needed:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_language_boundary_report.py   --output-json tmp/validation-eurusd-language-boundary.json   --output-md tmp/validation-eurusd-language-boundary.md

PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_zh_rationale_fields_report.py   --output-json tmp/validation-eurusd-zh-rationale-fields.json   --output-md tmp/validation-eurusd-zh-rationale-fields.md

PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_llm_review_artifacts.py   --output-json tmp/validation-eurusd-llm-review-artifacts.json   --output-md tmp/validation-eurusd-llm-review-artifacts.md   --output-jsonl tmp/eurusd/EURUSD_15m_llm_review_samples.jsonl

PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_llm_second_review_report.py   --sample-artifacts-jsonl tmp/eurusd/EURUSD_15m_llm_review_samples.jsonl   --output-json tmp/validation-eurusd-llm-second-review.json   --output-md tmp/validation-eurusd-llm-second-review.md

PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_review_standard_v0_report.py   --output-json tmp/validation-eurusd-review-standard-v0.json   --output-md tmp/validation-eurusd-review-standard-v0.md
```

Run focused tests:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python -m pytest   cajas/tests/test_validation_eurusd_real_llm_integration_readiness.py   cajas/tests/test_validation_eurusd_review_standard_v0.py   cajas/tests/test_validation_eurusd_llm_second_review.py
```

Run compile and readiness report build:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python -m py_compile   cajas/reports/validation_eurusd_real_llm_integration_readiness.py   cajas/scripts/build_eurusd_real_llm_integration_readiness_report.py

PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_real_llm_integration_readiness_report.py   --output-json tmp/validation-eurusd-real-llm-integration-readiness.json   --output-md tmp/validation-eurusd-real-llm-integration-readiness.md
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

- Real LLM integration readiness is measurable.
- Current expected state is `ready_for_explicit_approval` only if all offline prerequisites are green.
- Readiness does not equal approval.
- No live LLM API calls are added.
- No provider SDKs or API keys are introduced.
- No human labels are overwritten.
- No trading signals, no orders, no position sizing, no model training.
- Commit directly on `main`.
