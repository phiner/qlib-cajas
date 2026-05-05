# Task 052 — EURUSD 15m 五层形态研究体系重构计划

## 1. 背景与问题

当前 EURUSD 15m 候选系统已经具备稳定的数据流与审查基础，但核心问题是：

- 当前 `candidate_type` 混合了不同抽象层级（单K几何、趋势段、波动状态、假突破启发式）。
- 同一时间点可能被多个 candidate 命中，标签重叠重，审查语义不统一。
- 人审字段目前更偏“结果填写”，缺少统一的“结构化分层语义框架”。
- 若直接扩大 GUI 人审规模，可能先积累大量异质标签，后续难以沉淀高一致性研究结论。

因此需要从“单标签候选池”升级为“五层结构化研究体系”，但必须分阶段进行，不能一次性重构。

## 2. 最终目标

最终目标不是新增更多 `candidate_type`，而是将现有候选作为**入口锚点**，在人审阶段沉淀五层结构化信息：

1. `market_context`（背景）
2. `structure_location`（结构位置）
3. `local_behavior`（局部行为）
4. `confirmation_result`（确认/失败）
5. `review_outcome`（人审结论）

最终输出语义：

- 一个“有研究价值的形态样本” = 背景 + 位置 + 局部行为 + 确认/失败 + 人审结论
- 现有 `candidate_type` 仅作为样本入口和检索标签，不再等同于最终形态定义。

## 3. 五层体系定义

### 3.1 market_context 背景层

定义：样本所处市场环境。

建议字段（受控词表）：

- `trend`
- `range`
- `transition`
- `high_volatility`
- `low_volatility`
- `event_driven`（可选，中期）
- `unclear`

用途：约束同一局部行为在不同背景下的解释差异。

### 3.2 structure_location 结构位置层

定义：样本在局部/段内结构中的位置。

建议字段（第一版偏人工）：

- `segment_mid`
- `segment_tail`
- `near_local_extreme`
- `break_level_zone`
- `retest_zone`
- `unclear`

用途：解决“同样是长影线，发生在何处”这个关键问题。

### 3.3 local_behavior 局部行为层

定义：对当前候选触发行为的抽象归类。

建议字段：

- `wick_rejection`
- `doji_indecision`
- `volatility_compression`
- `volatility_expansion`
- `false_breakout_like`
- `trend_continuation_like`
- `unclear`

用途：承接当前 candidate 的启发式含义，但统一为跨候选可比的行为语义。

### 3.4 confirmation_result 确认/失败层

定义：样本在后续可视上下文中的结构结果（研究可视，不是交易信号）。

建议字段：

- `confirmed`
- `failed`
- `mixed`
- `insufficient_followthrough`
- `unclear`

用途：把“看起来像”与“后续结构是否支持”区分开。

### 3.5 review_outcome 人审结论层

定义：人工最终标签与质量判断。

建议沿用并扩展现有字段：

- `human_pattern_label`
- `structure_quality`
- `follow_through_quality`
- `review_confidence`
- `review_notes`

用途：作为后续误判分析、规则改进优先级排序的核心依据。

## 4. 当前 10 类 candidate 的新角色映射

| current candidate_type | new layer/family | role | keep/change | notes |
|---|---|---|---|---|
| short_trend_up_candidate | local_behavior / trend family | 趋势段入口锚点 | keep（入口） | 不作为最终“形态定义” |
| short_trend_down_candidate | local_behavior / trend family | 趋势段入口锚点 | keep（入口） | 继续使用 tail-bias 过滤 |
| mid_trend_up_candidate | market_context + local_behavior | 中期趋势背景提示 | keep（入口） | 需和 structure_location 联合解释 |
| mid_trend_down_candidate | market_context + local_behavior | 中期趋势背景提示 | keep（入口） | 同上 |
| lower_wick_rejection_candidate | local_behavior / wick family | 局部拒绝行为入口 | keep（入口） | 需补结构位置，否则误报偏多 |
| upper_wick_rejection_candidate | local_behavior / wick family | 局部拒绝行为入口 | keep（入口） | 同上 |
| possible_false_breakout_candidate | local_behavior + confirmation_result | 假突破候选入口 | keep（入口） | 需重点审查误报类型 |
| doji_indecision_candidate | local_behavior / indecision | 犹豫行为入口 | keep（入口） | 单独价值有限，需背景层 |
| compression_candidate | market_context / volatility | 波动收缩状态入口 | keep（入口） | 更像状态标签，不是终态形态 |
| expansion_candidate | market_context / volatility | 波动扩张状态入口 | keep（入口） | 需区分事件噪声与结构扩张 |

结论：10 类 candidate 全部保留为入口，不直接删除；其“最终解释权”迁移到五层标签组合。

## 5. 推荐分阶段实施计划

### Phase A — 设计冻结与文档化

目标：冻结五层术语、字段名、受控词表、边界说明。

### Phase B — Review schema 扩展

目标：在 schema 中新增五层字段（先 defaults+allowed values，不改 GUI）

### Phase C — Reviewer guide 与 GUI 文案更新

目标：先更新说明体系，降低审查员歧义。

### Phase D — GUI 表单字段接入与 CSV/JSONL 持久化

目标：将五层字段纳入 GUI 输入与持久化（保持 CSV 权威）。

### Phase E — Progress/report/audit 支持新字段

目标：完成进度与审计报表对新字段的覆盖与一致性检查。

### Phase F — Review batch 按 family 拆分

目标：从“10类平均”转为“family-aware 批次策略”（例如 wick/trend/volatility/breakout）。

### Phase G — 小样本专项 review 闭环

目标：20~30 样本/家族的小闭环，验证字段可用性与审查一致性。

### Phase H — False-positive taxonomy 报告

目标：输出误判类型分类报告，形成可执行规则改进候选清单。

### Phase I — 候选规则小幅改进（可选，最后做）

目标：仅在前述证据完备后，做小幅阈值/条件优化。

## 6. 每个 phase 的 Codex CLI 任务拆分

### Phase A

- objective: 设计冻结，避免后续返工。
- files likely changed:
  - `tasks/052...md`（已完成）
  - `cajas/docs/eurusd_pattern_research_kickoff.md`
  - `cajas/README.md`
- exact deliverables:
  - 五层术语与词表草案
  - 不做代码改动
- validation commands:
  - `git diff --check`
- risk: 术语歧义导致后续 GUI 字段反复修改。
- rollback plan: 仅文档回滚，成本低。
- what not to do: 不改 candidate 逻辑与阈值。

### Phase B

- objective: schema 可表达五层字段。
- files likely changed:
  - `cajas/reports/validation_eurusd_pattern_label_schema.py`
  - 对应脚本与测试
- exact deliverables:
  - 新字段 defaults/allowed values
  - schema 测试通过
- validation commands:
  - 相关 pytest + schema build 命令
- risk: 与旧 completed CSV 兼容性冲突。
- rollback plan: 新字段降级为 optional 并保留旧兼容读取。
- what not to do: 不接 GUI。

### Phase C

- objective: 先让审查流程语义统一。
- files likely changed:
  - `cajas/reports/validation_eurusd_pattern_review_guide.py`
  - `cajas/docs/eurusd_pattern_research_kickoff.md`
- exact deliverables:
  - 五层审查操作手册
- validation commands:
  - guide/report build + markdown diff 检查
- risk: 指南与 GUI 字段不一致。
- rollback plan: 文案回滚，保持旧指南。
- what not to do: 不改持久化结构。

### Phase D

- objective: GUI + CSV/JSONL 接入五层字段。
- files likely changed:
  - `cajas/apps/eurusd_pattern_review_app.py`
  - `cajas/research/eurusd_pattern_review_gui.py`
  - GUI/保存相关测试
- exact deliverables:
  - 新字段可填写、可保存、可恢复
- validation commands:
  - GUI 测试 + progress 报表重建
- risk: 保存兼容问题造成 progress blocked。
- rollback plan: feature flag 或字段降级 optional。
- what not to do: 不改候选生成。

### Phase E

- objective: 报表与审计支持新字段质量检查。
- files likely changed:
  - `cajas/reports/validation_eurusd_completed_review_progress.py`
  - `cajas/reports/validation_eurusd_candidate_audit.py`
  - 对应测试
- exact deliverables:
  - 缺失率/枚举合法性/层间一致性检查
- validation commands:
  - completed progress + candidate audit + pytest
- risk: 规则过严导致误阻塞。
- rollback plan: 区分 warning 与 blocking 门槛。
- what not to do: 不调阈值。

### Phase F

- objective: family-aware 批次策略。
- files likely changed:
  - `cajas/reports/validation_eurusd_pattern_review_batch.py`
  - 批次脚本与测试
- exact deliverables:
  - 按 family 分层采样策略
- validation commands:
  - batch 构建 + overlap/diversity 审计
- risk: 分层后样本覆盖失衡。
- rollback plan: 保留混合策略开关。
- what not to do: 不删现有 candidate_type。

### Phase G

- objective: 小样本闭环验证流程可用性。
- files likely changed:
  - 主要是 `tmp/` 产物，不强制 tracked 改动
- exact deliverables:
  - 20~30 样本真实审查结果
  - 五层字段填充可读性反馈
- validation commands:
  - completed progress + candidate audit
- risk: 审查员理解成本高。
- rollback plan: 缩减字段必填集合。
- what not to do: 不做大规模人审。

### Phase H

- objective: 误判类型分类报告。
- files likely changed:
  - 新增 `cajas/reports/...false_positive_taxonomy...py`（建议）
  - 对应脚本/测试
- exact deliverables:
  - 按 family + 五层字段的误判报告
- validation commands:
  - taxonomy report build + tests
- risk: 分类维度过多导致报告不可读。
- rollback plan: 先输出 top-k 误判类型。
- what not to do: 不直接改候选规则。

### Phase I

- objective: 基于证据的小幅规则优化（可选最后）
- files likely changed:
  - `cajas/research/eurusd_pattern_candidates.py`
  - 相关测试与说明
- exact deliverables:
  - 有证据支撑的微调 patch
- validation commands:
  - 候选/批次/审计全链路回归
- risk: 过拟合近期样本。
- rollback plan: 单独 commit，必要时 revert。
- what not to do: 不引入交易导向指标。

## 7. 推荐最小推进顺序

1. 仅提交设计计划（本任务）。
2. 扩展 schema 常量/default/allowed values（不接 GUI）。
3. 更新 reviewer guide 与报告文案。
4. 接入 GUI 表单与 CSV/JSONL 持久化。
5. 扩展 progress/audit 对五层字段支持。
6. 增加 family-specific batch 策略（可开关）。
7. 本地做 20–30 样本 smoke review。
8. 输出 false-positive taxonomy 报告。
9. 最后才讨论 candidate 规则小幅改进。

## 8. What should remain unchanged for now

以下内容在当前阶段必须保持不变：

- 当前 candidate 生成逻辑
- 当前阈值配置
- 原始数据文件
- Qlib core
- 存储后端：仅 CSV + JSONL
- 不引入交易/建模/执行逻辑

## 9. Open design questions for user

1. 五层字段每层的最终 allowed values 是否按“严格固定词表”执行？
2. `structure_location` 第一阶段是否完全人工填写，还是允许系统预填候选提示值？
3. `confirmation_result` 是否仅由人眼在可视前瞻窗口判断，还是允许附加计算辅助字段（只读）？
4. 批次策略是否改为 family 分批（例如先 wick 专项），还是保持 mixed 但按 family 优先级采样？
5. GUI 中是否保留 `candidate_type` 作为“入口标签”长期显示？
6. 五层字段中哪些应为必填，哪些可选（尤其在早期 smoke review）？

## 10. Recommended next Codex task after this plan

推荐下一任务：

- **Phase A 收尾 + Phase B 启动**：
  - 固化五层词表与字段命名决议；
  - 仅做 schema 扩展（defaults + allowed values + tests）；
  - 不改 GUI、不改候选逻辑。

---

实施原则：这是一次大型重构，应拆成多个小任务逐步推进；不要在单个 Codex 任务内一次做完。
