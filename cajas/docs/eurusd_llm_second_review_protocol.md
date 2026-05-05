# EURUSD Offline LLM Second-Review Protocol

## Purpose

Define a strict offline protocol for future LLM second-review on deterministic EURUSD artifacts.

- No live LLM API calls in this phase.
- Human labels and human rationale remain authoritative.
- LLM acts as second reviewer only.

## Input Boundary

LLM may read only deterministic sample artifacts:

- `artifact_version`: `eurusd_llm_review_sample_v0`
- one row per `sample_id`
- includes deterministic diagnostics, human review context, and explicit forbidden outputs

LLM must not inspect raw CSV directly and must not infer trading instructions.
LLM should follow the human-governed standard and example library first:

- `cajas/docs/eurusd_llm_review_standard_v0.md`
- `cajas/data_examples/eurusd_review_standard_v0_examples.jsonl`

## Required Output Schema

One JSONL row per `sample_id`:

- `artifact_version`: `eurusd_llm_second_review_v0`
- `source_artifact_version`: `eurusd_llm_review_sample_v0`
- `sample_id`
- `standard_version`
- `llm_reviewer_role`: `second_reviewer`
- `llm_pattern_validity`: `valid|invalid|uncertain`
- `llm_confidence`: `low|medium|high`
- `supporting_observations_zh`: list of strings
- `counter_observations_zh`: list of strings
- `uncertainty_reason_zh`: string
- `requires_human_review`: bool
- `possible_standard_gap_zh`: string
- `forbidden_trade_output_present`: must be `false`
- `raw_model_name`: string
- `review_created_at_utc`: string

Runtime keys remain English. Semantic explanatory content should be Chinese.

## Chinese Prompt Template (Documentation Only)

```text
你是 EURUSD 15m 形态审查的第二审查员（second reviewer）。
你只能读取提供的结构化样本工件，不得使用原始 CSV 或外部数据。
你必须参考中文语义标准，并结合已有的人类理由字段（如果存在）。
你的任务仅限：判断 valid / invalid / uncertain，并给出中文支持观察、反向观察、不确定原因。
如果标准不充分，请填写 possible_standard_gap_zh。
绝对禁止输出：trade signal、entry、exit、position size、PnL prediction、order recommendation、execution instruction。
必须返回严格 JSON，字段与协议完全一致。
```

## Validation and Audit Rules

- Schema must be exact and keyed by `sample_id`.
- Unknown `sample_id` rows are invalid for automation gates.
- Duplicate `sample_id` rows are invalid for automation gates.
- Any forbidden-trade output violation blocks readiness.
- LLM output never overwrites human review CSV.
- Fixture/demo outputs are protocol drills only and must not be represented as real production LLM results.

## Offline Fixture Drill

Example non-production fixture:

- `cajas/data_examples/eurusd_llm_second_review.example.jsonl`

Usage:

- protocol drill and validator behavior checks only
- human-audit metric walkthroughs (agreement/disagreement, high-confidence disagreement, requires-human-review, standard-gap)

## Automation Readiness Gate

Default when no LLM outputs:

- protocol status: `llm_second_review_protocol_ready`
- automation readiness: `not_evaluated`

Candidate gate to `ready_for_limited_trial` requires at minimum:

- zero forbidden-output violations
- zero invalid schema rows
- zero unknown sample IDs
- duplicate sample IDs equals 0
- output coverage >= configured threshold
- high-confidence disagreement rate <= configured threshold
- human-audit coverage documented (or explicitly pending)

## Real Integration Gate

- `ready_for_explicit_approval` means prerequisites are ready, but integration is still not approved.
- Real provider/API integration may start only after explicit user approval.
- Approval does not allow trading actions; human audit gate remains mandatory before any automation increase.
