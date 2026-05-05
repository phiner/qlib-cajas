# EURUSD 15m Market State Taxonomy v0 (3/8/24/128)

## Windows

- `ultra_short_window_bars = 3`
- `short_window_bars = 8`
- `mid_window_bars = 24`
- `long_window_bars = 128`

Nested interpretation:

- 3 bars: immediate micro-action
- 8 bars: current action
- 24 bars: local swing/structure
- 128 bars: local review-window background

128-bar long window is local 15m background, not macro daily/weekly trend.

## Chinese Semantics

- 超短期：3 根 K，捕捉最即时反转、冲高回落、下探回收、短线拒绝、微观突变。
- 短期：8 根 K，判断当前动作（急涨/急跌/小回调/小反弹/假突破/整理）。
- 中期：24 根 K，判断局部 swing 结构（顺势推进/回调/反弹/震荡/转折）。
- 长期：128 根 K，判断当前 review 窗口背景（上涨/下跌/高位整理/低位筑底/趋势放缓/转折尝试）。

## Runtime Enum Fields

- `ultra_short_state_3`
- `short_term_state_8`
- `mid_term_state_24`
- `long_term_state_128`
- `local_structure_state`
- `structure_confidence`

`market_state_rule_version = eurusd_market_state_rules_v0`

## Nuance Rules

- Long-term uptrend with 24-bar decline maps to `pullback` in mid-term, not immediate trend reversal.
- Long-term downtrend with 24-bar rise maps to `rebound` in mid-term.
- 3-bar micro reversal can coexist with trend-continuation backgrounds.

## Deterministic Rule Caveats

- v0 rules are transparent deterministic heuristics, not trained models.
- Swing counts are rolling approximations.
- Gap context is timestamp-delta based approximation.
- This output is for research labeling and review, not execution.

## Boundary

- no trading signals
- no order/position outputs
- no broker/exchange execution
- no real LLM integration
