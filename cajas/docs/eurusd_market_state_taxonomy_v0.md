# EURUSD 15m Market State Taxonomy v0 (Split Micro Event + Structure)

## Windows

- `ultra_short_window_bars = 3`
- `short_window_bars = 8`
- `mid_window_bars = 24`
- `long_window_bars = 128`

## Recognition Split

- 3-bar layer (`micro_pattern_event_3`) is pattern/event recognition, not generic return/slope classification.
- 8/24/128 layers are quantitative structure recognition.
- 3-bar events qualify structure interpretation; they do not define long background alone.

## 3-Bar Micro Event Fields

- `micro_pattern_event_3`
- `micro_pattern_direction_3`
- `micro_pattern_strength_3`
- `micro_reversal_detected_3`
- `micro_rejection_detected_3`
- `micro_sweep_detected_3`
- `micro_event_rationale_zh`

Enum examples:

- `three_bar_reversal_up`
- `three_bar_reversal_down`
- `lower_sweep_reclaim`
- `upper_sweep_reject`
- `three_bar_exhaustion_up`
- `three_bar_exhaustion_down`
- `micro_pause`
- `micro_compression`
- `failed_followthrough_up`
- `failed_followthrough_down`
- `micro_noise`
- `unknown`

## 8/24/128 Structure Fields

- `short_term_state_8`
- `mid_term_state_24`
- `long_term_state_128`
- `local_structure_state`
- `structure_confidence`
- `market_state_rationale_zh`
- `market_state_rule_version = eurusd_market_state_rules_v0`

## Boundary

- Research-only labeling context.
- No trading signals/orders/position sizing.
- No Qlib core change requirement.
- No real LLM provider calls.


## Calibration Guard (Task 081)

- Add `validation-eurusd-market-state-calibration` report before GUI wiring.
- Catch-all warnings (`dominant_*`, `catch_all_micro_event_high`, `unknown_local_structure_high`, `low_confidence_dominant`) are review signals, not trading signals and not automatic blockers by default.
- Calibration report remains research-only and keeps real LLM trial status at `not_approved`.


## External 3-Bar Rule Library (Task 081 externalize)

- 3-bar micro recognition now reads versioned external rules from `cajas/data_examples/eurusd_micro_pattern_rules_v0.json`.
- Rules are evaluated by priority and are deterministic/auditable; `micro_noise` remains lowest-priority catch-all.
- These pattern events are research context labels, not trading signals.


## Micro-noise residual profiling (Task 083)

- Added deterministic `validation-eurusd-micro-noise-profile` to break `micro_noise` into reviewable diagnostic subtypes.
- Added conservative buckets (`inside_range_pause`, `micro_drift_up/down`, `micro_chop`, `wick_conflict`) above residual `micro_noise`.
- `micro_noise` remains residual catch-all; no trading semantics are introduced.


## Residual Micro-noise Review Packet (Task 084)

- Added `micro_pattern_review_packet` workflow for residual `micro_noise` inspection with deterministic sampling.
- Residual `micro_noise` remains a valid catch-all; unresolved subtypes should be refined via human-reviewed packet evidence.
- Micro-pattern semantics remain classification-only and non-trading.


## Task 085 foundation hardening bundle

- Added manual-label workflow report for micro-pattern review packet with explicit `awaiting|ready|watch|blocked` statuses.
- Added rule-candidate summary report scaffold that depends on completed manual labels and does not auto-edit rule JSON.
- Added Qlib adapter contract report and dataset quality gate prior to GUI integration.
- Added consolidated market-state bundle report to summarize readiness/watch reasons.
