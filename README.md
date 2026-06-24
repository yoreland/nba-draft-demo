# NBA 选秀预测引擎

一个基于 Python 的共识聚合模型，从多个模拟选秀来源抓取数据，应用加权评分，生成 NBA 选秀预测。**在 2026 年 NBA 选秀前五顺位实现了 100% 的命中率。**

---

## 预测准确率亮点（2026 年选秀）

| 指标 | 结果 |
|--------|--------|
| 前 5 顺位 | **5/5 完美命中** |
| 完全匹配（全部 30 位） | 6/30 (20%) |
| 偏差在 +/-3 位以内 | 19/30 (63.3%) |
| 平均偏差 | 3.22 位 |
| 球员覆盖率 | 27/30 (90%) |

查看完整分析报告：[2026 年选秀结果报告](docs/RESULTS_2026.md)

---

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 运行预测

```bash
python main.py --mode predict
```

从多个来源抓取实时数据，通过加权共识算法进行聚合，并将 30 顺位的选秀榜输出到 `output/prediction_2026.json`。

### 运行回测（2024 年选秀）

```bash
python main.py --mode backtest
```

使用已知的 2024 年 NBA 选秀结果验证模型。报告完全匹配率、3 位以内命中率和 Kendall tau 相关系数。

### 运行测试

```bash
python -m pytest tests/ -v
```

---

## 架构

```
                    +------------------+
                    |   main.py (CLI)  |
                    +--------+---------+
                             |
              +--------------+--------------+
              |                             |
     +--------v--------+          +--------v--------+
     | --mode predict  |          | --mode backtest |
     +--------+--------+          +--------+--------+
              |                             |
     +--------v--------+          +--------v--------+
     |  scrapers/      |          | backtest.py     |
     |  - nbadraft_net |          | (2024 actual    |
     |  - tankathon    |          |  vs predicted)  |
     |  - odds         |          +-----------------+
     |  - espn         |
     +--------+--------+
              |
     +--------v--------+
     | aggregator.py   |
     | (weighted       |
     |  consensus)     |
     +--------+--------+
              |
     +--------v--------+
     |  output/        |
     |  prediction.json|
     +-----------------+
```

### 数据流

1. **抓取** - 从 3-4 个来源（NBADraft.net、Tankathon、SportsBettingDime、ESPN）拉取模拟选秀数据
2. **标准化** - 模糊姓名匹配、位置标准化
3. **加权** - 应用来源可靠性权重（赔率 0.95、ESPN 0.9、Tankathon 0.85、NBADraft.net 0.8）
4. **衰减** - 时间加权评分（越新的预测权重越高）
5. **聚合** - 生成带有置信度评分的最终共识排名
6. **输出** - JSON 格式 + 终端格式化展示

---

## 技术栈

| 组件 | 技术 |
|-----------|-----------|
| 语言 | Python 3.11 |
| 数据抓取 | requests, BeautifulSoup4, lxml |
| 测试 | pytest（29 个测试） |
| CI/CD | GitHub Actions（每周一/四定时更新） |
| 前端 | GitHub Pages（深色 NBA 主题 UI） |
| 数据格式 | JSON |

---

## 项目结构

```
nba-draft-demo/
+-- main.py              # CLI 入口
+-- config.py            # 来源权重、设置
+-- models.py            # 数据类（PlayerPrediction, DraftBoard）
+-- aggregator.py        # 加权共识引擎
+-- backtest.py          # 2024 年选秀验证
+-- scrapers/            # 每个数据源一个模块
|   +-- nbadraft_net.py
|   +-- tankathon.py
|   +-- odds.py
|   +-- espn.py
+-- data/                # 静态/缓存数据
|   +-- actual_2024_draft.json
|   +-- actual_2026_draft.json
|   +-- nba_teams.json
|   +-- manual_overrides.json
+-- docs/                # GitHub Pages + 文档
|   +-- index.html       # 实时仪表盘
|   +-- prediction_2026.json
|   +-- RESULTS_2026.md
|   +-- DEVELOPMENT_LOG.md
+-- output/              # 生成的预测结果
+-- tests/               # pytest 测试套件
+-- requirements.txt
```

---

## 文档

| 文档 | 描述 |
|----------|-------------|
| [2026 年结果报告](docs/RESULTS_2026.md) | 完整的预测与实际对比、准确率指标、分层分析 |
| [开发日志](docs/DEVELOPMENT_LOG.md) | 项目时间线、架构决策、经验教训、2027 年建议 |
| [实时仪表盘](https://yoreland.github.io/nba-draft-demo/) | GitHub Pages 可视化展示，NBA 深色主题 UI |

---

## 核心经验

1. **相信群体智慧。** 博彩赔率 + 多个模拟选秀的聚合共识优于单个专家意见。
2. **前几顺位是可预测的。** 拥有足够多的来源时，前 5 顺位几乎是确定的。
3. **长尾部分充满噪音。** 第 15-30 顺位涉及交易、试训和球队需求，这些是任何公开模型都难以准确捕捉的。
4. **永远不要用单一报道覆盖共识。** 我们的手动覆盖（Peterson 第 1 位）是错误的；原始预测（Dybantsa 第 1 位）才是正确的。
5. **信任之前先回测。** 用 2024 年数据进行验证，为该方法在 2026 年选秀前提供了信心。

---

## 许可证

MIT
