# EURUSD Market State Recognition Logic v0

## Pipeline

`Raw OHLC -> 3-bar micro event -> 8/24/128 structure -> combiner -> rationale`

## Layer A: 3-Bar Pattern/Event

Primary logic uses local candle sequence and range interaction:

- relative highs/lows and break/reclaim/reject behavior
- wick/body context
- failure to follow through after attempted break

This layer outputs categorical micro events and flags, and should not be interpreted as trading signals.

## Layer B: 8/24/128 Quantitative Structure

Quantitative inputs include:

- returns and slopes by window
- range width/position/compression
- swing approximation counts
- gap caveat counts

Outputs are short/mid/long structure states and confidence.

## Layer C: Combiner

Micro events qualify structure context (examples):

- pullback in uptrend + `three_bar_reversal_up` supports stabilization context
- rebound in downtrend + `lower_sweep_reclaim` supports local reclaim context
- high-level consolidation + `upper_sweep_reject` may map to exhaustion risk

## Qlib Adapter Boundary

Future Qlib adapter should consume:

- 8/24/128 quantitative features
- 3-bar micro-event categorical fields
- human-corrected labels after review

No Qlib core modification is required for this phase.


## Calibration Diagnostics (Task 081)

- Added calibration report layer to quantify micro/structure concentration before GUI integration.
- Added reason-code distributions for micro event, local structure, and confidence assignment to improve deterministic explainability.
- Over-dominant catch-all classes trigger warnings and manual review priority lists; they do not create trade actions.


## Rule Library Runtime

- Added rule loader/validator/evaluator flow for 3-bar micro events.
- Market-state report exposes `micro_pattern_rule_version`, `micro_pattern_rules_loaded`, and `micro_pattern_rule_count`.
- If rule file is missing/invalid, runtime uses deterministic fallback `micro_noise` rule to avoid nondeterministic behavior.


## Noise-to-bucket workflow

- Workflow is now: profile micro-noise -> identify dominant subtypes -> add minimal stable rule buckets -> re-run calibration.
- Rule additions are conservative and deterministic; stronger sweep/reversal/exhaustion rules keep higher priority.
- GUI wiring should remain deferred until micro-event distribution is sufficiently interpretable.


## Packet-driven refinement loop

- Residual-noise refinement now follows: profile -> conservative rule split -> review packet sampling -> human semantic review -> next rule update.
- Added review packet fields include 3-bar OHLC context and blank human semantic fields for later labeling.
- Avoid blind threshold tuning; prioritize subtype evidence from review packet.


## Pre-GUI hardening sequence

- Sequence now enforced: review packet -> manual labels -> rule candidates -> qlib adapter contract -> dataset quality gate -> bundle report.
- GUI wiring is deferred until this foundation stack is stable and watch reasons are understood.
- Real LLM remains unapproved and no Qlib core changes are required.

## Dedicated micro-pattern labeling tool

- Manual labeling for residual 3-bar packet now runs in a dedicated app:
  - `PYTHONPATH=. ./.venv-qlib313/bin/python -m streamlit run cajas/apps/eurusd_micro_pattern_review_app.py`
  - or `./scripts/run_eurusd_micro_pattern_review_gui.sh`
- Persistence semantics:
  - latest-state CSV keyed by `sample_id`: `tmp/eurusd/EURUSD_15m_micro_pattern_review_packet_completed_template.csv`
  - append-only audit JSONL: `tmp/eurusd/EURUSD_15m_micro_pattern_review_events.jsonl`
- Runtime identifiers remain English, rationale/suggestion semantics stay in `_zh` fields.
- This tool is research labeling only and does not add trading semantics or real LLM calls.

## Four-layer inspection packet workflow

- Build compact inspection packet from sample export for manual semantic review:
  - `pattern_3` event correctness
  - `market_8/24/128` state correctness
  - `local_structure_state` combiner correctness
- Human feedback uses English runtime correction identifiers and `_zh` rationale fields.
- Completed feedback is validated and summarized into definition-gap signals.
- This workflow is inspection-only; no GUI wiring, no auto rule edits, no LLM/trading scope changes.
