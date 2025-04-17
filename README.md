# Market Demand Radar (V2)

![发布状态](https://img.shields.io/badge/状态-开发中-brightgreen)
![版本](https://img.shields.io/badge/版本-v2.0-blue)

## 概述
市场需求雷达（Market Demand Radar）是一个高级市场机会分析工具，它能够从多个数据源（Reddit、Product Hunt、App Store、Chrome Web Store）收集数据，使用人工智能分析未满足的用户需求，并提供经过评分的产品机会推荐。系统提供交互式仪表板和电子邮件摘要，是独立开发者、投资者和产品经理发现有价值机会的理想工具。

## 🔑 核心功能
- **多源数据收集**：异步从Reddit、Product Hunt、应用商店等获取数据
- **AI驱动分析**：使用GPT-3.5-turbo提取用户痛点和机会
- **需求供应评分**：使用复合算法计算机会价值（Demand×Supply gap）
- **黄金区域识别**：自动识别高需求低竞争的机会
- **交互式仪表板**：使用Streamlit构建，支持多维过滤和可视化
- **电子邮件摘要**：自动发送高价值机会的每周摘要

## 📊 项目结构

```
market_demand_radar/
├── src/                      # 主要源代码
│   ├── scrapers/             # 数据收集模块
│   │   ├── reddit_scraper.py    # Reddit数据抓取
│   │   ├── producthunt_scraper.py # ProductHunt数据抓取
│   │   ├── appstore_scraper.py  # App Store评论抓取
│   │   └── chromestore_scraper.py # Chrome商店数据抓取
│   ├── extractor.py          # LLM分析器，提取机会
│   ├── scoring.py            # 评分引擎，计算机会价值
│   ├── competitive.py        # 竞争分析，获取竞品数据
│   ├── report.py             # 报告生成器，生成分析报告
│   ├── email_digest.py       # 电子邮件摘要生成器
│   └── config.py             # 配置文件
├── dashboard.py              # Streamlit仪表板应用
├── main_v2.py                # 主程序入口点
├── main.py                   # 旧版主程序入口点
├── tests/                    # 测试套件
│   ├── unit/                 # 单元测试
│   └── integration/          # 集成测试
├── prompts/                  # LLM提示词模板
│   └── opportunity_v2.txt    # 机会提取提示词
├── reports/                  # 生成的报告存储
├── PRDs/                     # 产品需求文档
│   ├── V1                    # V1产品需求
│   └── V2                    # V2产品需求
├── tools/                    # 工具目录
│   └── update_scratchpad.py  # 项目状态追踪工具
├── .cursorscratchpad         # 项目状态跟踪文件
├── requirements.txt          # 项目依赖
└── README.md                 # 项目文档
```

## 🚀 安装指南

```bash
# 克隆仓库
git clone https://github.com/yourusername/market_demand_radar.git
cd market_demand_radar

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export OPENAI_API_KEY="your_openai_api_key"
# 或创建.env文件并添加您的API密钥
```

## 💻 使用方法

### 运行完整分析流程
```bash
# 使用默认参数运行
python main_v2.py

# 自定义参数
python main_v2.py --subreddits macapps apple productivity --limit 50 --output custom_report.md
```

### 可用参数选项
- `--subreddits`, `-s`: 要搜索的Reddit子论坛（默认：macapps, iphone, chrome_extensions）
- `--limit`, `-l`: 每个数据源获取的最大帖子数（默认：25）
- `--output`, `-o`: 输出报告的文件名
- `--no-gpt`: 跳过GPT分析
- `--no-competitive`: 跳过竞争分析
- `--gold-only`: 仅处理黄金区域机会

### 启动仪表板
```bash
# 启动Streamlit仪表板
streamlit run dashboard.py
```

## 📋 模块说明

### 数据收集 (`src/scrapers/`)
- 所有数据收集器都实现了标准的异步接口
- 抓取的数据使用统一的 `RawPost` 格式进行规范化
- 包含多级重试机制和速率限制以避免API限制

### LLM提取器 (`src/extractor.py`)
- 使用GPT-3.5-turbo模型分析文本内容
- 实现了批处理逻辑以优化成本和速度
- 采用精心设计的提示词（见 `prompts/opportunity_v2.txt`）

### 评分引擎 (`src/scoring.py`)
- 实现了PRD中定义的评分公式
  - DemandScore = log10(post_score+1)*10 + sentiment*10 + velocity*20
  - SupplyScore = app_count*5 + avg_rating*2
  - Opportunity = DemandScore - SupplyScore
- 黄金区域条件：Opportunity ≥ 70, DemandScore ≥ 50, SupplyScore ≤ 30

### 报告生成器 (`src/report.py`)
- 生成带有视觉支持的Markdown格式报告
- 包含执行摘要、Top 5机会详细信息、附录

### 仪表板 (`dashboard.py`)
- 使用Streamlit构建交互式仪表板
- 支持过滤：时间范围、需求分数、标签、数据源
- 显示黄金区域机会、趋势图表和详细信息

## 🧪 开发指南

### 添加新数据源
1. 在 `src/scrapers/` 中创建新的抓取器模块
2. 实现异步接口与 `fetch_*` 方法
3. 将数据转换为统一的 `RawPost` 格式
4. 在 `main_v2.py` 中集成新的抓取器

### 修改评分逻辑
1. 在 `src/scoring.py` 中更新相关公式
2. 确保 `ScoringEngine` 类的接口保持不变
3. 如果添加新特征，更新视图层相应显示

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/unit/test_scoring.py
```

## 📈 项目状态

### 模块状态
- ✅ 数据源集成 (Reddit, ProductHunt, AppStore, ChromeWebStore)
- ✅ LLM提取器实现（使用GPT-3.5-turbo）
- ✅ 评分引擎实现
- ✅ 竞争分析数据获取
- ✅ 报告生成器（Markdown + 视觉支持）
- ✅ Streamlit仪表板
- ✅ 命令行界面参数支持
- ⚠️ 电子邮件摘要（部分实现）
- ⚠️ 测试覆盖率不全

### 已知问题
1. 部分行业数据可能需要更新，尤其是快速变化的技术领域
2. 报告之间的数据格式尚未完全统一，可能需要标准化处理

## 📄 授权
MIT

## 🤝 贡献
欢迎提交问题和拉取请求！请参阅[贡献指南](CONTRIBUTING.md)了解详情。

## 快速开始

### 本地开发

1. **克隆仓库**
   ```bash
   git clone https://github.com/yourusername/market_demand_radar.git
   cd market_demand_radar
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```
   
3. **配置环境变量**
   创建`.env`文件并根据`.env.example`设置必要的API密钥

4. **运行仪表板**
   ```bash
   streamlit run dashboard.py
   ```

### Streamlit Cloud部署

本项目可以轻松部署到[Streamlit Community Cloud](https://streamlit.io/cloud)：

1. 将代码推送到GitHub仓库
2. 登录Streamlit Cloud
3. 点击"New app"并连接您的GitHub仓库
4. 选择main分支和dashboard.py作为主文件
5. 点击"Deploy!"

访问[仪表板使用指南](docs/dashboard_guide.md)获取更多详细信息。

## 数据源

- Reddit讨论
- Product Hunt新产品
- App Store评论
- Chrome Web Store扩展