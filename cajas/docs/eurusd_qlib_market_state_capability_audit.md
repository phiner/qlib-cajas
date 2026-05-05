# EURUSD Qlib Market-State Capability Audit

## Objective
Build an EURUSD 15m market-state understanding system with horizon semantics:

- short-term: 3-8 bars (current action)
- mid-term: 1-24 bars (local structure/swing)
- long-term: 1-64 bars (review-window background)

Mid/long horizons include shorter horizons. This is local 15m context, not macro daily/weekly trend.

## Qlib Fit Summary
Qlib is suitable as an offline research substrate for data pipelines, feature/label datasets, model/evaluation workflows, and event-study style analysis. Qlib is not a semantic market-state ontology system by itself.

Conclusion:

- Qlib can support market-state research.
- Qlib does not natively define the required state taxonomy semantics.
- cajas must implement taxonomy/feature/label/review contracts and adapters.

## Capability Breakdown
### Supports Directly
- offline dataset handling and time-based split workflows
- factor/feature and label ingestion for supervised tasks
- experiment recorder/reporting primitives
- model/evaluation and stability analysis loops
- event-study style outcome analysis on generated labels/features

### Supports With cajas Adapter
- single-instrument EURUSD 15m adaptation with stable symbol/index contract
- market-state feature matrix for short/mid/long horizons
- market-state labels (`long_term_state`, `mid_term_state`, `short_term_state`, `local_structure_state`, `structure_confidence`)
- state-conditioned evaluation and drift reporting

### Not Sufficient In Qlib Core Alone
- human semantic rationale governance (`*_zh` fields)
- market-state taxonomy definitions and Chinese semantic interpretation
- review-session persistence contract (CSV latest-state + JSONL audit)
- offline LLM handoff protocol boundaries

## Required cajas Layer
### A. Taxonomy v0
```json
{
  "short_horizon_bars": {"min": 3, "max": 8},
  "mid_horizon_bars": {"min": 1, "max": 24},
  "long_horizon_bars": {"min": 1, "max": 64}
}
```
Use English enum keys + Chinese semantic definitions.

### B. Feature Builder (Deterministic)
- rolling return, slope, normalized slope
- swing high/low and HH/HL/LH/LL counts
- pullback depth, rebound height
- range percentile, compression/expansion
- wick/body features
- gap count/largest gap
- impulse stats
- range position in 24/64-bar windows

No trading signal outputs.

### C. Label Builder (Versioned)
- `long_term_state`
- `mid_term_state`
- `short_term_state`
- `local_structure_state`
- `structure_confidence`
- optional numeric confidence/state scores
- optional future outcome labels for event-study only

### D. Qlib Adapter
- instrument: stable EURUSD symbol mapping
- datetime index: 15m timestamps
- deterministic feature columns
- taxonomy/event-study labels
- strict time-based split
- anti-leakage guarantee: no forward information in features

### E. Evaluation Layer
- state classification quality
- event-study by state buckets
- feature importance
- temporal stability/drift
- state-conditioned outcome analysis

No live execution.

## Suitability Matrix
| Area | Status | Notes |
|---|---|---|
| raw 15m data storage | supports_with_cajas_adapter | Qlib format/handler contract needed |
| feature engineering | supports_with_cajas_adapter | taxonomy-specific features in cajas |
| label generation | supports_with_cajas_adapter | market-state labels defined in cajas |
| supervised modeling | supports_directly | after adapter dataset prep |
| market dynamics modeling | supports_with_cajas_adapter | requires taxonomy and feature contracts |
| state taxonomy semantics | not_suitable_current_scope | belongs to cajas semantic layer |
| human review rationale | not_suitable_current_scope | outside Qlib core |
| LLM second review | not_suitable_current_scope | outside Qlib core, remains offline boundary |
| backtest/event study | supports_directly | research-only usage |
| live execution | not_suitable_current_scope | excluded in this project phase |
| broker integration | not_suitable_current_scope | explicitly excluded |

## Red Lines
- Do not modify Qlib core.
- Do not use execution/order modules.
- Do not emit buy/sell/order/position outputs.
- Do not train models in this audit phase.
- Do not introduce real LLM calls.
- Do not treat state labels as trading advice.

## Recommended Next Phase
`define_market_state_taxonomy_v0_and_feature_contract`

Reason: horizon semantics and state definitions are being finalized; taxonomy and deterministic feature/label contracts should be locked before GUI rewiring or model training.
