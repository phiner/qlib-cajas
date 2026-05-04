# Phase 2 Prompt: Qlib Integration Mapping for EURUSD 15m Market Recognition

你现在接手 `qlib-cajas` 项目的 Phase 2。

## 当前状态

仓库：`qlib-cajas`

当前分支：

```bash
cajas/market-recognition-phase-0
```

任务 prompt 目录约定：

```text
taskDocs/
  codex_tasks/
```

注意：`taskDocs/` 已被 `.gitignore` 忽略，prompt 文档不提交。

Phase 0 已完成：

- 新增 `AGENTS.md`
- 新增 `.gitignore` 规则
- 新增 `cajas/` 研究层
- 新增 `cajas/scripts/prepare_fx_dataset.py`
- 新增 `cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml`
- 新增 `cajas/data_examples/README.md`
- 不修改 `qlib/` core

Phase 1 已完成：

- 真实 EURUSD 15m CSV 已跑通
- 输出目录：

```text
tmp/cajas/eurusd_15m_phase1/
  prepared_dataset.csv
  dataset_manifest.json
```

数据摘要：

```text
raw rows: 24904
output rows: 24896
time range: 2025-01-01 22:00:00 to 2025-12-31 19:45:00
future_direction_8 distribution: up=12690, down=12100, flat=106
duplicate datetime count: 0
sorted by datetime: yes
```

Phase 1 commit：

```text
7ec5eab2 feat: validate phase 1 EURUSD dataset preparation
```

## 本阶段目标

Phase 2 的目标是：

> 在不修改 Qlib core 的前提下，调研并记录 prepared EURUSD dataset 如何接入 Qlib 的 Dataset / DataHandler / Model / Workflow 流程，并补充一个最小 cajas 配置草案或文档化接入方案。

本阶段仍然是研究接入层，不做正式训练，不做收益分析，不做交易策略，不做自动下单。

## 工作边界

必须遵守：

1. 不修改 `qlib/` core。
2. 不修改官方 `examples/` 的既有逻辑。
3. 不提交原始 CSV。
4. 不提交 `tmp/` 生成文件。
5. 不把 `future_direction_8` 描述为买入/卖出信号。
6. 不做实盘、不做自动下单、不做交易建议。
7. 优先新增或修改：
   - `cajas/README.md`
   - `cajas/configs/`
   - `cajas/data_examples/README.md`
   - `cajas/docs/` 如需要
   - `cajas/scripts/` 如确有必要
8. 如果需要新增文档，优先放在：

```text
cajas/docs/
```

## 需要完成的任务

### 1. 检查当前状态

执行：

```bash
git status
git branch --show-current
```

确认当前分支是：

```bash
cajas/market-recognition-phase-0
```

确认没有 staged 或 tracked 的：

```text
taskDocs/
.codex/
tmp/
原始 CSV
```

### 2. 阅读 Phase 1 输出结构

查看 manifest：

```bash
cat tmp/cajas/eurusd_15m_phase1/dataset_manifest.json
```

查看 prepared dataset 头部：

```bash
head -5 tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv
```

记录：

- datetime column
- symbol column
- feature columns
- label column
- row count
- label distribution

不要提交这些生成文件。

### 3. 调研 Qlib 官方 workflow / dataset / handler 示例

只读查看以下目录，不要修改官方文件：

```bash
find examples -maxdepth 3 -type f | head -100
find qlib -maxdepth 4 -type f | grep -E "data|dataset|handler|workflow|model" | head -120
```

重点寻找：

- Qlib YAML 配置格式
- DatasetH / DataHandlerLP / DataHandler 相关用法
- LightGBM model config 示例
- workflow_by_code / workflow_by_config 示例
- 用户自定义 handler 是否可以在外部路径定义
- 是否存在从 CSV 或自定义数据源接入的轻量路径

可以使用：

```bash
grep -R "DatasetH" -n examples qlib | head -50
grep -R "DataHandler" -n examples qlib | head -80
grep -R "LightGBM" -n examples qlib | head -80
grep -R "workflow" -n examples | head -80
```

### 4. 新增 Qlib 接入调研文档

新增：

```text
cajas/docs/qlib_integration_notes.md
```

文档内容至少包含：

```markdown
# Qlib Integration Notes for cajas EURUSD 15m Research

## Current prepared dataset

- Input local output:
  - tmp/cajas/eurusd_15m_phase1/prepared_dataset.csv
  - tmp/cajas/eurusd_15m_phase1/dataset_manifest.json
- Label:
  - future_direction_8
- Important warning:
  - This label is for market recognition research only.
  - It is not a trading signal.

## Qlib components reviewed

列出查看过的 examples / qlib 文件路径，并简述用途。

## Candidate integration paths

至少比较 2 条路径：

### Path A: Qlib native provider format

说明：
- 是否需要把 prepared CSV 转成 Qlib provider 格式
- 可能优点
- 可能缺点
- 下一步需要什么

### Path B: Custom external DataHandler / Dataset

说明：
- 是否可以在 `cajas/` 下定义自定义 handler
- 如何避免修改 qlib core
- 可能优点
- 可能缺点
- 下一步需要什么

## Recommended next step

给出 Phase 3 推荐路线。

建议优先选择“最小外部接入层”，不要立即改 Qlib core。
```

### 5. 更新或细化实验配置草案

检查现有：

```text
cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
```

如果当前配置只是占位，可以做轻量完善，但不要让它假装已经完全可运行。

要求：

- 明确标注为 draft / research config。
- 写清楚数据来源是 Phase 1 prepared CSV。
- 写清楚 label 是 `future_direction_8`。
- 写清楚当前配置是 market recognition research，不是交易策略。
- 如不确定 Qlib 字段，添加 TODO，而不是编造。
- 不要引入自动下单、回测收益、position sizing 等内容。

可以增加注释：

```yaml
# Draft only. This config documents the intended Qlib integration shape.
# It may require a custom DataHandler under cajas/ before it can run.
```

### 6. 更新 cajas README

在 `cajas/README.md` 追加 Phase 2 说明：

- Phase 1 已生成 prepared dataset
- Phase 2 开始调研 Qlib Dataset/DataHandler 接入
- 文档位置：

```text
cajas/docs/qlib_integration_notes.md
```

- 仍然不改 qlib core
- 仍然不做训练和交易

### 7. 可选：新增最小目录占位

如有必要，可以新增：

```text
cajas/docs/
```

不要新增大型代码框架。Phase 2 以文档化调研和配置草案为主。

## 验证要求

执行：

```bash
git status
```

如果修改了 Python 脚本，则执行：

```bash
python -m py_compile cajas/scripts/prepare_fx_dataset.py
```

如果没有修改 Python 脚本，不需要强行运行。

检查文档中不要出现：

- 买入建议
- 卖出建议
- 实盘下单
- 自动交易
- 收益承诺

检查 Git 不包含：

```text
tmp/
taskDocs/
.codex/
原始 CSV
```

## 提交规范

推荐 commit：

```bash
git add cajas/README.md cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml cajas/docs/qlib_integration_notes.md
git commit -m "docs: map qlib integration path for cajas EURUSD research"
git push
```

如果只新增文档，没有修改 config，则：

```bash
git add cajas/README.md cajas/docs/qlib_integration_notes.md
git commit -m "docs: add qlib integration notes for cajas EURUSD research"
git push
```

## 完成后的汇报格式

请按下面格式汇报：

```text
Phase 2 completed.

Branch:
- cajas/market-recognition-phase-0

Changed files:
- ...

Qlib components reviewed:
- ...

Integration paths compared:
- Path A:
- Path B:

Recommended Phase 3:
- ...

Validation commands run:
- ...

Git:
- commit:
- push: done/not done

Notes:
- ...
```

## 禁止事项

不要做以下事情：

- 不要修改 `qlib/` core
- 不要训练模型
- 不要做回测收益分析
- 不要创建交易策略
- 不要添加自动下单逻辑
- 不要提交 `tmp/`
- 不要提交 `taskDocs/`
- 不要提交 `.codex/`
- 不要提交原始 CSV
- 不要把 `future_direction_8` 解释成交易信号
