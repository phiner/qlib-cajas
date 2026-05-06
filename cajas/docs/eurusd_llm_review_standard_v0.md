# EURUSD 15m 人工审查标准 v0

## 1. 范围与非范围

范围：

- EURUSD 15m 候选形态的人类语义审查
- `valid / invalid / uncertain` 的结构化判定
- 中文理由、反例、不确定性与上下文说明

非范围：

- 交易信号
- 入场/出场建议
- 仓位大小
- PnL 预测
- 执行指令

## 2. 语言与运行时边界

- 运行时字段、文件名、CLI、状态值保持英文。
- 语义标准、理由与示例解释以中文为权威。
- `*_zh` 字段用于连接工程稳定性与中文语义精度。
- 语言边界政策参考：`cajas/docs/eurusd_review_language_policy.md`。

## 3. 候选类型审查原则

- `candidate_type` 仅是入口标签，不等同最终结论。
- `human_label` 是对当前 `candidate_type` 的最终人工判断。
- `Local/P3/M8/M24/M128` 都是证据层，用来支持或削弱当前候选，不替代最终结论。
- 审查顺序：背景 -> 结构位置 -> 局部行为 -> 后续确认 -> 人工结论。
- 任何单一形态特征（如长影线）不得脱离背景独立判定。

## 4. valid / invalid / uncertain 判定框架

- `valid`：结构背景与后续确认一致，反证不足以推翻。
- `invalid`：核心结构条件不成立，或后续行为直接否定。
- `uncertain`：证据冲突、上下文不足、标准边界不清晰。

## 5. 影线（wick）专项指导

- 下影线/上影线必须结合前置结构和后续K线确认。
- 长影线不自动等于有效拒绝。
- 若后续快速击穿关键低点/高点，需降级为 `invalid` 或 `uncertain`。

## 6. 趋势/震荡/过渡背景指导

- 趋势中部噪声应谨慎，避免过度解释局部形态。
- 震荡区间中的“看似拒绝”常见假阳性，优先检查结构位置。
- 过渡状态可保留 `uncertain`，并明确不确定来源。

## 7. 跳空与压缩（gap/compression）注意事项

- 时间轴压缩与真实价格行为必须分开理解。
- gap 附近形态优先标注为 `uncertain` 或 `requires_human_review`，除非结构证据完整。

## 8. 常见假阳性模式

- 中段噪声中的随机长影线
- 无结构支撑的“突破后回收”
- 低波动横盘中的偶发冲刺K线

## 9. 歧义处理

- 允许输出 `uncertain`。
- 必须在 `uncertainty_reason_zh` 中给出具体原因。
- 若标准描述不足，写入 `possible_standard_gap_zh` 并进入人工复核。

## 10. 禁止输出

任何审查结果都不得包含：

- `trade_signal`
- `entry`
- `exit`
- `position_size`
- `pnl_prediction`
- `order_recommendation`
- `execution_instruction`

## 11. 示例库格式

示例库文件：

- `cajas/data_examples/eurusd_review_standard_v0_examples.jsonl`

每条示例使用英文 key + 中文语义内容，核心字段包括：

- `example_id`
- `standard_version`
- `candidate_type`
- `decision` (`valid|invalid|uncertain`)
- `confidence` (`low|medium|high`)
- `scenario_tags`
- `rationale_zh`
- `counter_observation_zh`
- `uncertainty_reason_zh`
- `context_notes_zh`
- `forbidden_trade_output_present`

## 12. 标准修订流程

1. 人工审查发现边界冲突或高频歧义。
2. 在示例库补充正例/反例/不确定例。
3. 记录 `possible_standard_gap_zh` 并提出修订候选。
4. 由人类负责人确认后更新标准版本。
5. 在离线验证中复核一致性指标，再考虑自动化级别提升。

## 13. 真实 LLM 集成准入说明

- 标准就绪不等于集成批准。
- 在真实接入前，优先提升人审质量：`human_label`、`human_confidence` 与 `_zh` 理由字段完整性应持续提高并可量化。
- 若完成审查 CSV 尚不存在，应报告为 `awaiting_review_input`（等待人工输入），而非系统阻塞。
- 仅当“真实 LLM 集成就绪报告”为 `ready_for_explicit_approval` 且用户明确批准后，才可进入真实接入任务。
- 任何真实接入前后，人工审查闸门都必须保留。
- 最小试运行边界必须记录在审批文件中（默认 `not_approved`）：
  - 输入仅限确定性样本工件
  - 输出仅限 second-review JSONL
  - 样本数量上限（默认不超过 10）
  - 禁止覆盖人类标签
  - 禁止任何交易输出
