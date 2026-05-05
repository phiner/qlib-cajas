# Task 068 — Define Explicit Approval Record and Minimal Real LLM Trial Boundary

## Context

Task 067 completed the real LLM integration readiness checklist.

Current readiness state:

- `tmp/validation-eurusd-real-llm-integration-readiness.json`
- readiness status: `ready_for_explicit_approval`

Important distinction:

- Readiness is not approval.
- No live LLM integration may begin until explicit user approval is recorded in a dedicated, auditable artifact.
- This task should define the approval record and minimal trial boundary.
- Do not add live LLM API calls yet unless the user explicitly provides approval for this exact task.

Current constraints:

- Work directly on `main`.
- CSV + JSONL durable storage only.
- No SQLite.
- No provider SDKs unless explicitly approved.
- No API keys committed or required.
- No trading signals, no orders, no position sizing, no model training.
- Human standard remains authoritative.
- Human labels must not be overwritten by LLM outputs.
- English runtime identifiers, Chinese semantic fields.

## Goal

Create an explicit approval record format and minimal real LLM trial boundary for future EURUSD second-review integration.

This task should make the next real integration step auditable and reversible.

## Required Design

### 1. Explicit Approval Record

Add a template/example approval artifact, for example:

- `cajas/data_examples/eurusd_real_llm_integration_approval.template.json`

It should include fields such as:

```json
{
  "approval_status": "not_approved",
  "approved_by": "",
  "approved_at_utc": "",
  "approved_scope": "eurusd_llm_second_review_trial",
  "allowed_input_artifact": "tmp/eurusd/EURUSD_15m_llm_review_samples.jsonl",
  "allowed_output_artifact": "tmp/eurusd/EURUSD_15m_llm_second_review_trial.jsonl",
  "max_samples": 10,
  "provider": "",
  "model": "",
  "live_api_calls_allowed": false,
  "human_audit_required": true,
  "overwrite_human_labels_allowed": false,
  "trading_outputs_allowed": false,
  "rollback_plan_required": true,
  "notes": ""
}
```

Default must be `not_approved`.

### 2. Minimal Trial Boundary

Document a minimal real LLM trial boundary:

- input: deterministic LLM-ready sample artifacts only
- output: second-review JSONL only
- max samples: small default, e.g. 10
- no production label mutation
- no GUI mutation unless explicitly added later
- no trading outputs
- no batch automation beyond explicit sample cap
- human audit must review all trial outputs
- any forbidden output blocks further use

### 3. Provider-Agnostic Interface Plan

Document a provider-agnostic interface, but do not implement live calls yet.

Possible future function boundary:

```python
def run_llm_second_review_trial(
    sample_artifacts_jsonl: Path,
    output_jsonl: Path,
    approval_json: Path,
    max_samples: int,
) -> TrialResult:
    ...
```

The future runner must:

- read approval artifact
- fail closed unless `approval_status=approved`
- fail closed unless `live_api_calls_allowed=true`
- cap sample count
- validate output schema
- never write human review CSV
- never emit trading actions

### 4. Approval Readiness Report

Add a report/CLI that validates approval state.

Suggested files:

- `cajas/reports/validation_eurusd_llm_trial_approval.py`
- `cajas/scripts/build_eurusd_llm_trial_approval_report.py`
- `cajas/tests/test_validation_eurusd_llm_trial_approval.py`

Suggested outputs:

- `tmp/validation-eurusd-llm-trial-approval.json`
- `tmp/validation-eurusd-llm-trial-approval.md`

Statuses:

- `not_approved`
- `approved_for_limited_trial`
- `blocked`

Expected current status should be:

- `not_approved`

because the template defaults to not approved.

### 5. Blocking Conditions

Report `blocked` if:

- approval artifact allows trading outputs
- approval artifact allows overwriting human labels
- approval artifact lacks sample cap
- approval artifact lacks human audit requirement
- approval artifact is approved but live API calls are false/inconsistent
- approval artifact references missing required readiness report
- readiness report is not `ready_for_explicit_approval`

Report `approved_for_limited_trial` only if:

- readiness report status is `ready_for_explicit_approval`
- approval artifact explicitly says `approval_status=approved`
- `live_api_calls_allowed=true`
- `trading_outputs_allowed=false`
- `overwrite_human_labels_allowed=false`
- `human_audit_required=true`
- `max_samples` is positive and at/below allowed cap
- provider/model fields are non-empty
- output artifact path is explicit

### 6. Documentation

Update docs/roadmap to state:

- real LLM integration is a separate future task
- approval template defaults to `not_approved`
- no provider/API code is introduced by this task
- limited trial approval still does not permit automation
- full automation requires later audit metrics and another explicit approval

## Implementation Targets

Inspect/update:

- `cajas/docs/eurusd_llm_second_review_protocol.md`
- `cajas/docs/eurusd_llm_review_standard_v0.md`
- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `tasks/eurusd_15m_research_end_to_end_roadmap.md`

Add as useful:

- `cajas/data_examples/eurusd_real_llm_integration_approval.template.json`
- `cajas/reports/validation_eurusd_llm_trial_approval.py`
- `cajas/scripts/build_eurusd_llm_trial_approval_report.py`
- `cajas/tests/test_validation_eurusd_llm_trial_approval.py`

## Validation Commands

Run focused tests:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python -m pytest   cajas/tests/test_validation_eurusd_llm_trial_approval.py   cajas/tests/test_validation_eurusd_real_llm_integration_readiness.py
```

Run compile and report build:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python -m py_compile   cajas/reports/validation_eurusd_llm_trial_approval.py   cajas/scripts/build_eurusd_llm_trial_approval_report.py

PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_llm_trial_approval_report.py   --readiness-json tmp/validation-eurusd-real-llm-integration-readiness.json   --approval-json cajas/data_examples/eurusd_real_llm_integration_approval.template.json   --output-json tmp/validation-eurusd-llm-trial-approval.json   --output-md tmp/validation-eurusd-llm-trial-approval.md
```

Expected report status for the default template:

- `not_approved`

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

- Explicit approval record format exists.
- Default approval state is `not_approved`.
- Minimal real LLM trial boundary is documented.
- Provider-agnostic future interface is documented but not executed.
- No live LLM API calls are added.
- No provider SDKs are added.
- No human labels are overwritten.
- No trading signals, no orders, no position sizing, no model training.
- Commit directly on `main`.
