# Phase 1 Prompt: Run EURUSD 15m Dataset Preparation and Validate Outputs

你现在接手 `qlib-cajas` 项目的 Phase 1。

## 当前仓库状态

- 仓库：`qlib-cajas`
- 当前分支：`cajas/market-recognition-phase-0`
- Phase 0 已完成：
  - 新增 `AGENTS.md`
  - 新增 `.gitignore` 规则，忽略 `taskDocs/`、`.codex/`、`tmp/` 等本地文件
  - 新增 `cajas/` 研究层
  - 新增 `cajas/scripts/prepare_fx_dataset.py`
  - 新增 `cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml`
  - 新增 `cajas/data_examples/README.md`
  - 不修改 `qlib/` core

## 本阶段目标

Phase 1 的目标是：

> 使用真实 EURUSD 15m CSV 跑通 `prepare_fx_dataset.py`，验证输出数据、字段、标签分布和基础质量，并补充最小文档。

本阶段只做数据准备与验收，不做模型训练，不做交易策略，不做实盘，不做自动下单。

## 输入数据

真实数据文件已经存在于本机：

```bash
~/projects/research/data/EURUSD_15\ Mins_Bid_2025.01.01_2025.12.31.csv
```

CSV 示例：

```csv
Time (UTC),Open,High,Low,Close,Volume 
2025.01.01 22:00:00,1.03503,1.03519,1.03483,1.03485,91.44
2025.01.01 22:15:00,1.03485,1.03546,1.03485,1.03543,240.6
2025.01.01 22:30:00,1.03542,1.03573,1.03526,1.03566,572.56
```

注意：
- 原始数据文件不要提交到 Git。
- 生成输出默认写入 `tmp/`，不要提交到 Git。
- CSV header 里 `Volume ` 可能带尾随空格，需要脚本稳健处理。

## 工作边界

必须遵守：

1. 不修改 `qlib/` core。
2. 不修改官方 examples 的既有逻辑。
3. 只允许修改或新增：
   - `cajas/`
   - `.gitignore` 如确有必要
   - `AGENTS.md` 如确有必要
4. 不提交原始数据。
5. 不提交 `tmp/` 输出。
6. 不引入重型依赖，优先使用 Python 标准库；如 Phase 0 脚本已依赖 pandas，则保持一致，不额外扩大依赖。
7. 不做训练、不做收益分析、不做交易建议。

## 需要完成的任务

### 1. 检查当前 Git 状态

执行：

```bash
git status
```

确认当前分支是：

```bash
cajas/market-recognition-phase-0
```

确认没有误跟踪：
- `.codex/`
- `taskDocs/`
- `tmp/`
- 原始 CSV 数据

如果发现这些被 Git 跟踪或 staged，需要先修正。

### 2. 静态检查数据准备脚本

执行：

```bash
python -m py_compile cajas/scripts/prepare_fx_dataset.py
```

如果失败，修复语法错误。

### 3. 使用真实数据运行脚本

执行：

```bash
python cajas/scripts/prepare_fx_dataset.py \
  --input ~/projects/research/data/EURUSD_15\ Mins_Bid_2025.01.01_2025.12.31.csv \
  --output-dir tmp/cajas/eurusd_15m_phase1 \
  --symbol EURUSD \
  --timeframe 15m
```

如果脚本当前参数名不同，请先阅读脚本 `--help`，在不破坏 Phase 0 设计的前提下保持 CLI 清晰：

```bash
python cajas/scripts/prepare_fx_dataset.py --help
```

### 4. 验证输出文件

检查输出目录：

```bash
find tmp/cajas/eurusd_15m_phase1 -maxdepth 2 -type f -print
```

需要确认至少有一个主数据文件，推荐但不强制的输出包括：

```text
tmp/cajas/eurusd_15m_phase1/
  eurusd_15m_features.csv
  dataset_manifest.json
```

如果当前脚本还没有 manifest，建议新增一个轻量 manifest，记录：

```json
{
  "symbol": "EURUSD",
  "timeframe": "15m",
  "label": "future_direction_8",
  "input_path": "...",
  "row_count_raw": 0,
  "row_count_output": 0,
  "start_time": "...",
  "end_time": "...",
  "feature_columns": [],
  "label_distribution": {},
  "created_by": "cajas/scripts/prepare_fx_dataset.py"
}
```

注意 manifest 可以写入 `tmp/`，但不要提交生成结果。

### 5. 检查输出数据字段

主输出数据至少应包含：

```text
datetime
symbol
timeframe
open
high
low
close
volume
return_1
range
body
upper_shadow
lower_shadow
future_close_8
future_return_8
future_direction_8
```

如果 Phase 0 已定义了更多字段，可以保留。

`future_direction_8` 建议语义：

```text
up      future_return_8 > 0
down    future_return_8 < 0
flat    future_return_8 == 0
```

不要引入交易阈值，不要解释为买卖信号。

### 6. 做最小数据质量检查

用 Python 或 shell 检查：

- 输出行数
- 时间范围
- 是否有重复 datetime
- 是否按 datetime 升序
- OHLC 是否能转成数值
- `future_direction_8` 分布
- 最后 8 行是否因为没有未来 close 而被合理丢弃或标空

可以临时使用命令，但不要提交临时检查脚本，除非你认为有必要把它纳入 `cajas/scripts/`。

### 7. 更新文档

更新 `cajas/README.md`，新增 Phase 1 使用说明，至少包含：

```bash
python cajas/scripts/prepare_fx_dataset.py \
  --input ~/projects/research/data/EURUSD_15\ Mins_Bid_2025.01.01_2025.12.31.csv \
  --output-dir tmp/cajas/eurusd_15m_phase1 \
  --symbol EURUSD \
  --timeframe 15m
```

并说明：

- 原始数据不提交
- 输出目录在 `tmp/`
- `future_direction_8` 是研究标签，不是交易信号
- 当前阶段只验证数据准备，不训练模型

如有必要，更新 `cajas/data_examples/README.md`，补充真实 CSV header 兼容说明：

```text
Time (UTC),Open,High,Low,Close,Volume 
```

其中 `Volume ` 可能带尾随空格。

### 8. 提交规范

提交前执行：

```bash
git status
git diff
```

确认没有提交：
- 原始 CSV
- `tmp/`
- `.codex/`
- `taskDocs/`

建议 commit message：

```bash
git add cajas/README.md cajas/data_examples/README.md cajas/scripts/prepare_fx_dataset.py
git commit -m "feat: validate phase 1 EURUSD dataset preparation"
```

如果只是文档更新，没有脚本变更，则使用：

```bash
git commit -m "docs: document phase 1 EURUSD dataset preparation"
```

然后推送：

```bash
git push
```

## 完成后的汇报格式

请按下面格式汇报：

```text
Phase 1 completed.

Branch:
- cajas/market-recognition-phase-0

Changed files:
- ...

Validation commands run:
- python -m py_compile cajas/scripts/prepare_fx_dataset.py
- python cajas/scripts/prepare_fx_dataset.py ...

Generated local outputs:
- tmp/cajas/eurusd_15m_phase1/...

Dataset summary:
- raw rows:
- output rows:
- time range:
- future_direction_8 distribution:
- duplicate datetime count:
- sorted by datetime: yes/no

Git:
- commit:
- push: done/not done

Notes:
- ...
```

## 禁止事项

不要做以下事情：

- 不要修改 `qlib/` core
- 不要训练 LightGBM
- 不要创建交易策略
- 不要做收益分析
- 不要提交原始 CSV
- 不要提交 `tmp/`
- 不要把 `future_direction_8` 描述为买入/卖出信号
