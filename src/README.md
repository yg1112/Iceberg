# 源代码目录结构

本目录包含市场需求雷达的核心实现模块。每个模块负责特定功能，遵循单一职责原则设计。

## 模块结构与职责

### 1. 数据收集模块 (`scrapers/`)

数据收集模块负责从各种来源获取原始数据。所有抓取器都实现了统一的异步接口。

- **`reddit_scraper.py`**: 从Reddit获取数据，支持多个子版块。
  - 主要函数: `fetch_subreddit_posts(subreddit, limit=25)`
  - 使用PRAW API实现，具有速率限制保护

- **`producthunt_scraper.py`**: 从Product Hunt获取"Asks"类别的数据。
  - 主要函数: `fetch_asks(limit=25)`
  - 使用ProductHunt公开API获取数据

- **`appstore_scraper.py`**: 从Apple App Store获取应用评论。
  - 主要函数: `fetch_app_reviews(app_id, limit=25)`
  - 支持按时间和评分过滤

- **`chromestore_scraper.py`**: 从Chrome Web Store获取扩展数据。
  - 主要函数: `fetch_top_extensions(limit=25)`
  - 使用网页爬取获取数据，包含用户代理池和延迟保护

### 2. LLM提取器 (`extractor.py`)

LLM提取器使用OpenAI GPT模型分析文本内容，提取结构化的机会信息。

- **主要函数**:
  - `extract_from_post(post)`: 对单个帖子进行分析
  - `batch_extract(posts)`: 批处理多个帖子，优化API调用
  
- **输出数据格式**:
  ```json
  {
    "title": "机会标题",
    "pain_summary": "痛点摘要",
    "unmet_need": true/false,
    "solo_doable": true/false,
    "monetizable": true/false,
    "tags": ["tag1", "tag2"]
  }
  ```

### 3. 评分引擎 (`scoring.py`)

评分引擎根据PRD定义的公式计算需求分数、供应分数和机会分数。

- **主要函数**:
  - `calculate_demand_score(post)`: 计算需求分数
  - `calculate_supply_score(post)`: 计算供应分数
  - `calculate_opportunity_score(post)`: 计算机会分数
  - `is_gold_zone(post)`: 判断是否为黄金区域机会
  - `score_posts(posts)`: 对多个帖子进行评分
  - `get_gold_zone_posts(posts)`: 筛选黄金区域帖子

- **评分公式**:
  - `DemandScore = log10(post_score+1)*10 + sentiment*10 + velocity*20`
  - `SupplyScore = app_count*5 + avg_rating*2`
  - `Opportunity = DemandScore - SupplyScore`

- **黄金区域条件**:
  - `Opportunity ≥ 70`
  - `DemandScore ≥ 50`
  - `SupplyScore ≤ 30`

### 4. 竞争分析器 (`competitive.py`)

竞争分析器获取和分析市场上现有竞品的数据。

- **主要函数**:
  - `fetch_competitive_data(keyword)`: 获取竞争数据
  - `enrich_post(post)`: 为单个帖子添加竞争数据
  - `batch_enrich_posts(posts)`: 批量为多个帖子添加竞争数据

- **数据来源**:
  - App Store评分趋势（6个月）
  - Chrome Store用户数和评分
  - 竞品价格和更新频率

### 5. 报告生成器 (`report.py`)

报告生成器将分析结果转换为格式化的Markdown报告。

- **主要函数**:
  - `generate_exec_summary(posts)`: 生成执行摘要
  - `generate_top_opportunities(posts)`: 生成热门机会详情
  - `generate_opportunity_details(post)`: 生成单个机会详情
  - `generate_report(posts, output_file)`: 生成完整报告

- **报告结构**:
  - 执行摘要（≤120字）
  - Top 5机会详情
  - 详细数据表
  - 附录（市场趋势图表）

### 6. 电子邮件摘要 (`email_digest.py`)

电子邮件摘要模块负责生成和发送周期性的电子邮件摘要。

- **主要函数**:
  - `generate_email_content(posts)`: 生成电子邮件HTML内容
  - `send_digest_email(recipients, content)`: 发送摘要邮件
  - `schedule_weekly_digest()`: 设置每周定时发送

- **发送配置**:
  - 发送时间: 每周一08:00 UTC
  - 内容: 执行摘要 + Top 5 + "Start-Building" CTA

## 数据流

整个系统的数据流如下:

```
数据收集 -> LLM提取 -> 竞争分析 -> 评分计算 -> 机会筛选 -> 报告生成/仪表板展示/邮件发送
```

## 使用示例

```python
# 数据收集示例
async with RedditScraper() as scraper:
    posts = await scraper.fetch_subreddit_posts("macapps", limit=25)

# LLM分析示例
extractor = LLMExtractor()
processed_posts = await extractor.batch_extract(posts)

# 评分计算示例
scorer = ScoringEngine()
scored_posts = scorer.score_posts(processed_posts)

# 黄金区域筛选示例
gold_zone_posts = scorer.get_gold_zone_posts(scored_posts)

# 报告生成示例
builder = ReportBuilder()
report_path = builder.generate_report(scored_posts, "market_report.md")
``` 