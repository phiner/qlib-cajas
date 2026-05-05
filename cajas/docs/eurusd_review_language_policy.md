# EURUSD Review Language Boundary Policy

## Purpose

Define a stable bilingual boundary for EURUSD 15m review work:

- Chinese is authoritative for semantic review reasoning.
- English is authoritative for runtime and automation identifiers.

## English Runtime Layer (Required)

The following must remain English:

- Python modules, classes, functions
- schema keys and review field ids
- CSV/JSON/JSONL column and object keys
- filenames and script names
- CLI flags and command arguments
- test names and test ids
- status enums and report keys
- machine-facing logs and automation identifiers

Examples:

- `review_outcome`
- `review_confidence`
- `language_boundary_ready`

## Chinese Semantic Layer (Authoritative)

Chinese should be used as the primary semantic language for:

- human rationale and counterexample explanation
- uncertainty explanation
- market-structure context notes
- pattern definition text
- valid/invalid/uncertain examples
- future LLM instruction semantics
- supporting/counter observations
- standard revision explanations

Recommended semantic bridge naming:

- `human_rationale_zh`
- `human_counterexample_zh`
- `human_uncertainty_reason_zh`
- `human_context_notes_zh`
- `supporting_observations_zh`
- `counter_observations_zh`
- `uncertainty_reason_zh`

## Prohibited Direction

Do not introduce:

- Chinese schema keys
- Chinese enum values
- Chinese filenames for runtime/data artifacts
- Chinese CLI flags
- mixed-language runtime field names without convention
- English-only rationale where Chinese semantic precision is required
- treating Chinese rationale as optional debug text

## Current Project Boundary

- No trading signals, no order routing, no position sizing.
- No model training enablement in this policy step.
- CSV + JSONL durable storage remains unchanged.
