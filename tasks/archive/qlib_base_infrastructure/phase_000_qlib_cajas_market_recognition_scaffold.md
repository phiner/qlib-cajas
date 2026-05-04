# Phase 0 Prompt: qlib-cajas Market Recognition Scaffold

你现在接手 `qlib-cajas` fork 的第一阶段开发工作。

当前仓库状态：

- 仓库：`qlib-cajas`
- 分支：`cajas/market-recognition-phase-0`
- upstream 已设置为 Microsoft Qlib 原仓库
- 当前目标不是改造 Qlib core，而是在 fork 中新增一个独立的 `cajas/` 研究层
- 本阶段只做 Phase 0 scaffold + EURUSD 15m 数据准备脚本

## 核心原则

1. **不要修改 Qlib core**
   - 不要改 `qlib/` 目录下的核心代码。
   - 不要改 Qlib 原有训练、回测、交易逻辑。
   - 不要引入实盘交易、自动下单、broker 对接。

2. **本阶段只做行情识别研究 scaffold**
   - 目标是：Qlib-based Market Recognition Research。
   - 研究对象是 EURUSD 15m K 线数据。
   - 第一版只准备最小数据集和配置草案。
   - 不做收益分析。
   - 不做交易策略。
   - 不做自动交易。
   - 不做模型效果承诺。

3. **新增内容应集中在 `cajas/` 下**
   - `cajas/` 是本 fork 的自定义研究层。
   - 后续 forex / K-line / market recognition 相关代码优先放这里。
   - 尽量保持与 upstream Qlib 的 core 解耦。

4. **任务文档目录 `taskDocs/` 不纳入 git**
   - 本地任务 prompt / 阶段文档会放在 `taskDocs/`。
   - 请修改 `.gitignore`，确保 `taskDocs/` 被忽略。
   - 不要提交 `taskDocs/` 内的文档。

## 已准备的数据文件

用户已经准备好 EURUSD 15m CSV：

```text
~/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv
```

文件头部示例：

```csv
Time (UTC),Open,High,Low,Close,Volume 
2025.01.01 22:00:00,1.03503,1.03519,1.03483,1.03485,91.44
2025.01.01 22:15:00,1.03485,1.03546,1.03485,1.03543,240.6
2025.01.01 22:30:00,1.03542,1.03573,1.03526,1.03566,572.56
2025.01.01 22:45:00,1.03561,1.03577,1.0355,1.0355,538.62
2025.01.01 23:00:00,1.0355,1.03563,1.03501,1.03536,1378.86
2025.01.01 23:15:00,1.03536,1.03543,1.03513,1.03513,1007.01
2025.01.01 23:30:00,1.03515,1.03517,1.03462,1.03491,1128.51
2025.01.01 23:45:00,1.03491,1.03531,1.03491,1.03507,932.99
2025.01.02 00:00:00,1.03508,1.03518,1.03491,1.03493,850.72
```

注意：

- 时间列名是 `Time (UTC)`。
- Volume 列名可能带尾部空格：`Volume `。
- 时间格式是：`YYYY.MM.DD HH:MM:SS`。
- 数据周期是 15m。
- 当前只针对 EURUSD Bid 数据。

## 本阶段需要新增的文件

请新增以下文件和目录：

```text
cajas/
  README.md
  scripts/
    prepare_fx_dataset.py
  configs/
    fx_eurusd_15m_lightgbm_future_direction_8.yaml
  data_examples/
    README.md
```

并更新：

```text
.gitignore
```

确保包含：

```gitignore
taskDocs/
```

## 文件 1：cajas/README.md

请写一份简洁但清晰的说明，内容包括：

- 项目名称：`cajas` research layer for qlib-cajas
- 目标：Qlib-based Market Recognition Research
- 当前研究方向：EURUSD 15m K-line / FX market recognition
- 当前不是交易系统
- 当前不涉及：
  - live trading
  - automatic order placement
  - broker integration
  - profit prediction promises
  - production investment advice
- 当前 Phase 0 目标：
  - 建立独立研究目录
  - 准备最小 FX 数据集
  - 生成基础 K 线特征
  - 生成 `future_direction_8` 标签
  - 提供第一版 Qlib/LightGBM 实验配置草案

建议 README 包含一个目录结构说明，例如：

```text
cajas/
  scripts/       # data preparation and research utilities
  configs/       # draft experiment configs
  data_examples/ # expected input/output schema notes
```

## 文件 2：cajas/data_examples/README.md

请说明输入 CSV 格式和输出数据格式。

输入 CSV 需要说明：

- 必要列：
  - `Time (UTC)`
  - `Open`
  - `High`
  - `Low`
  - `Close`
  - `Volume` 或 `Volume `
- 时间格式：`YYYY.MM.DD HH:MM:SS`
- 周期：15m
- symbol：默认 `EURUSD`

输出数据建议说明为一个普通 research dataset CSV，不强行假设已经是完整 Qlib binary 格式。

输出字段至少包括：

- `datetime`
- `symbol`
- `open`
- `high`
- `low`
- `close`
- `volume`
- 基础特征字段
- `future_return_8`
- `future_direction_8`

请说明 `future_direction_8` 的临时定义：

- 使用未来 8 根 15m K 线后的 close 计算未来收益。
- `future_return_8 = close.shift(-8) / close - 1`
- 第一版标签可用三分类：
  - `up`
  - `down`
  - `flat`
- flat 阈值允许通过参数配置，默认建议 `0.0002` 或类似保守值。

注意：这是研究标签，不是交易信号。

## 文件 3：cajas/scripts/prepare_fx_dataset.py

请实现一个 Python CLI 脚本，用于读取用户的 EURUSD 15m CSV，清洗字段，生成基础 K 线特征和 `future_direction_8` 标签。

### CLI 要求

脚本应支持：

```bash
python cajas/scripts/prepare_fx_dataset.py \
  --input "~/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv" \
  --output-dir tmp/cajas/fx_eurusd_15m_phase0 \
  --symbol EURUSD \
  --horizon 8 \
  --flat-threshold 0.0002
```

参数：

- `--input`：必填，原始 CSV 路径，支持 `~` 展开。
- `--output-dir`：必填，输出目录。
- `--symbol`：默认 `EURUSD`。
- `--horizon`：默认 `8`。
- `--flat-threshold`：默认 `0.0002`。

### 输出要求

输出目录中至少生成：

```text
prepared_dataset.csv
dataset_manifest.json
```

其中：

- `prepared_dataset.csv` 是清洗和特征生成后的数据集。
- `dataset_manifest.json` 记录输入路径、输出路径、symbol、horizon、flat_threshold、行数、开始时间、结束时间、生成字段列表等。

### 数据清洗要求

脚本需要：

1. 读取 CSV。
2. 对列名做 strip，处理 `Volume ` 这种尾部空格。
3. 将列名标准化为小写：
   - `Time (UTC)` -> `datetime`
   - `Open` -> `open`
   - `High` -> `high`
   - `Low` -> `low`
   - `Close` -> `close`
   - `Volume` -> `volume`
4. 解析时间：
   - 格式：`%Y.%m.%d %H:%M:%S`
   - 输出 `datetime` 建议保存为 ISO-like 字符串，或 pandas 标准 datetime 字符串。
5. 检查必要列是否存在。
6. 按 `datetime` 排序。
7. 去除完全重复行。
8. 对 OHLCV 转换为 numeric。
9. 对明显无法解析的行给出错误或丢弃，并在 manifest 中记录。

### 基础特征要求

请生成一组轻量、可解释、面向 K 线识别的基础特征。

建议至少包含：

- `return_1`
- `log_return_1`
- `hl_range`
- `body_size`
- `upper_shadow`
- `lower_shadow`
- `body_ratio`
- `close_position_in_range`
- `range_pct`
- `volume_change_1`
- rolling 特征：
  - `return_mean_4`
  - `return_mean_8`
  - `return_mean_16`
  - `return_std_8`
  - `return_std_16`
  - `range_mean_8`
  - `range_mean_16`

实现时注意除零保护，必要时用 `NaN`，最后可以保留 NaN 或 drop 掉无法形成标签/基础特征的首尾行。

### 标签要求

生成：

```python
future_return_8 = close.shift(-8) / close - 1
```

然后：

- `future_return_8 > flat_threshold` => `up`
- `future_return_8 < -flat_threshold` => `down`
- 其他 => `flat`

如果 horizon 参数不是 8，则字段名应随 horizon 变化：

- `future_return_{horizon}`
- `future_direction_{horizon}`

默认 horizon=8，所以默认输出就是：

- `future_return_8`
- `future_direction_8`

最后几行因为未来数据不足，应删除或标记为无标签；第一版建议删除无标签行，并在 manifest 记录删除数量。

### 代码质量要求

- 使用 `argparse`。
- 使用 `pathlib.Path`。
- 使用 `pandas` 和 `numpy`。
- 有清晰函数拆分，例如：
  - `parse_args()`
  - `load_raw_csv()`
  - `standardize_columns()`
  - `add_features()`
  - `add_future_direction_label()`
  - `write_manifest()`
  - `main()`
- CLI 运行完成后 print 输出关键路径和行数。
- 对缺失列给出清楚错误信息。
- 不要依赖仓库外的私有模块。

## 文件 4：cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml

请新增第一版实验配置草案。

注意：这只是 draft config，不要求本阶段已经完整接入 Qlib trainer。

配置中应表达：

- experiment name
- symbol: EURUSD
- timeframe: 15m
- task: market recognition / future direction classification
- label: future_direction_8
- horizon: 8
- flat_threshold: 0.0002
- dataset path placeholder: `tmp/cajas/fx_eurusd_15m_phase0/prepared_dataset.csv`
- model family: LightGBM
- objective: multiclass classification
- feature columns placeholder / list
- train/valid/test split 草案，例如：
  - train: 2025-01-01 to 2025-08-31
  - valid: 2025-09-01 to 2025-10-31
  - test: 2025-11-01 to 2025-12-31
- 明确说明：
  - this is a research config draft
  - not a trading strategy
  - not a production signal

## .gitignore 更新要求

请检查 `.gitignore`，如果没有 `taskDocs/`，则追加：

```gitignore
# Local task prompts and planning docs
/taskDocs/
taskDocs/
```

不要提交 `taskDocs/` 中的任何文档。

## 验证要求

完成后请执行以下检查：

```bash
git status --short
python cajas/scripts/prepare_fx_dataset.py \
  --input "$HOME/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv" \
  --output-dir tmp/cajas/fx_eurusd_15m_phase0 \
  --symbol EURUSD \
  --horizon 8 \
  --flat-threshold 0.0002

head tmp/cajas/fx_eurusd_15m_phase0/prepared_dataset.csv
cat tmp/cajas/fx_eurusd_15m_phase0/dataset_manifest.json
```

如果环境中有格式化工具，也可以运行适当的格式检查；但不要因为缺少额外工具而阻塞本阶段。

## 期望最终变更摘要

最终应该看到类似变更：

```text
M .gitignore
A cajas/README.md
A cajas/scripts/prepare_fx_dataset.py
A cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml
A cajas/data_examples/README.md
```

生成的临时数据输出位于：

```text
tmp/cajas/fx_eurusd_15m_phase0/
```

该输出目录通常不需要提交。

## 提交建议

通过验证后提交：

```bash
git add .gitignore cajas/README.md cajas/scripts/prepare_fx_dataset.py cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml cajas/data_examples/README.md

git commit -m "feat: add cajas market recognition phase 0 scaffold"
```

## 本阶段不要做的事

- 不要改 `qlib/` core。
- 不要接入实盘交易。
- 不要写自动下单逻辑。
- 不要做收益回测结论。
- 不要把 `future_direction_8` 描述成交易信号。
- 不要把配置草案包装成完整可生产系统。
- 不要提交原始 EURUSD CSV 数据文件。
- 不要提交 `taskDocs/`。

