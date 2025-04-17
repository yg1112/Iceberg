# 数据抓取模块

数据抓取模块负责从各种来源异步获取原始数据。所有抓取器都实现了统一的接口，并提供重试机制和速率限制保护以避免API限制。

## 统一数据格式

所有抓取器返回的数据都遵循统一的 `RawPost` 格式：

```python
{
    "id": str,                # 唯一标识符
    "title": str,             # 帖子标题
    "content": str,           # 帖子内容
    "score": int,             # 得分/点赞数
    "created_utc": int,       # 创建时间（Unix时间戳）
    "num_comments": int,      # 评论数量
    "source": str,            # 来源（reddit/producthunt/appstore/chrome_web_store）
    "url": str,               # 原始URL
    "subreddit": str,         # 子版块（仅适用于Reddit）
    "additional_data": dict   # 特定来源的额外数据
}
```

## 抓取器详情

### 1. Reddit抓取器 (`reddit_scraper.py`)

从Reddit获取数据，支持多个子版块。

#### 使用方法

```python
from src.scrapers.reddit_scraper import RedditScraper, DEFAULT_SUBREDDITS

async def fetch_reddit_data():
    async with RedditScraper() as scraper:
        # 从默认子版块获取数据
        default_posts = await scraper.fetch_subreddit_posts()
        
        # 从特定子版块获取数据
        custom_posts = await scraper.fetch_subreddit_posts("productivity", limit=50)
        
        # 从多个子版块获取数据
        all_posts = []
        for subreddit in ["macapps", "iphone", "productivity"]:
            posts = await scraper.fetch_subreddit_posts(subreddit, limit=30)
            all_posts.extend(posts)
            
        return all_posts
```

#### 配置项

- `DEFAULT_SUBREDDITS`: 默认抓取的子版块列表，包括 "macapps", "iphone", "chrome_extensions"
- 环境变量:
  - `REDDIT_CLIENT_ID`: Reddit API客户端ID
  - `REDDIT_CLIENT_SECRET`: Reddit API客户端密钥
  - `REDDIT_USER_AGENT`: 自定义用户代理

#### 注意事项

- Reddit API有每小时60次请求的限制
- 建议使用异步上下文管理器（`async with`）自动管理会话资源
- 抓取器包含重试逻辑，会在遇到限制时自动延迟和重试

### 2. ProductHunt抓取器 (`producthunt_scraper.py`)

从ProductHunt获取"Asks"类别的数据，这类数据通常包含用户的需求和问题。

#### 使用方法

```python
from src.scrapers.producthunt_scraper import ProductHuntScraper

async def fetch_producthunt_data():
    async with ProductHuntScraper() as scraper:
        # 获取默认数量（25）的请求
        posts = await scraper.fetch_asks()
        
        # 指定数量
        custom_posts = await scraper.fetch_asks(limit=50)
        
        return posts
```

#### 配置项

- 环境变量:
  - `PRODUCTHUNT_API_KEY`: ProductHunt API密钥（可选）

#### 注意事项

- ProductHunt API不需要认证也可以访问公开数据，但有速率限制
- API请求会缓存结果以提高性能和减少请求次数

### 3. App Store抓取器 (`appstore_scraper.py`)

从Apple App Store获取应用评论，特别关注负面评论中可能包含的未满足需求。

#### 使用方法

```python
from src.scrapers.appstore_scraper import AppStoreScraper

async def fetch_appstore_data():
    async with AppStoreScraper() as scraper:
        # 获取单个应用的评论
        app_id = "1232780281"  # Notion
        posts = await scraper.fetch_app_reviews(app_id)
        
        # 指定评分限制（仅获取3星及以下评论）
        filtered_posts = await scraper.fetch_app_reviews(app_id, max_rating=3)
        
        # 获取多个应用的评论
        app_ids = ["1232780281", "310633997", "1274495053"]  # Notion, Evernote, Things 3
        all_posts = []
        for app_id in app_ids:
            posts = await scraper.fetch_app_reviews(app_id, limit=10)
            all_posts.extend(posts)
            
        return all_posts
```

#### 配置项

- `DEFAULT_USER_AGENT`: 默认浏览器用户代理
- `USER_AGENT_LIST`: 用户代理池，用于轮换请求

#### 注意事项

- App Store没有官方API，使用网页爬取可能会受到限制
- 抓取器使用用户代理池和延迟请求来减少被封锁的风险
- 默认只获取英文评论，可以通过参数修改

### 4. Chrome Web Store抓取器 (`chromestore_scraper.py`)

从Chrome Web Store获取扩展数据和用户评论。

#### 使用方法

```python
from src.scrapers.chromestore_scraper import ChromeStoreScraper

async def fetch_chromestore_data():
    async with ChromeStoreScraper() as scraper:
        # 获取热门扩展列表
        extensions = await scraper.fetch_top_extensions(limit=10)
        
        # 获取特定扩展的详细信息
        extension_id = "bmnlcjabgnpnenekpadlanbbkooimhnj"  # Honey扩展
        extension_data = await scraper.fetch_extension_data(extension_id)
        
        # 将扩展数据转换为统一的RawPost格式
        post = await scraper.fetch_and_convert_to_raw_post(extension_id)
        
        return extensions, post
```

#### 配置项

- `DEFAULT_USER_AGENT`: 默认浏览器用户代理
- `USER_AGENT_LIST`: 用户代理池，用于轮换请求
- `BASE_URL`: Chrome Web Store基础URL

#### 注意事项

- Chrome Web Store没有官方API，使用网页爬取可能会受到限制
- 抓取过于频繁可能导致临时IP封锁
- 抓取器包含指数退避重试逻辑和随机延迟

## 通用抓取工具函数

模块还提供了一些通用工具函数，可以在所有抓取器中使用：

```python
from src.scrapers import utils

# 获取随机用户代理
user_agent = utils.get_random_user_agent()

# 添加随机延迟（避免请求过于频繁）
await utils.random_delay(min_seconds=1, max_seconds=3)

# 创建限速的aiohttp会话
async with utils.create_rate_limited_session() as session:
    # 使用会话进行请求
    response = await session.get("https://api.example.com/data")
```

## 添加新的数据源

要添加新的数据源，请按照以下步骤操作：

1. 在`src/scrapers/`目录下创建新的抓取器模块，例如`twitter_scraper.py`
2. 实现与其他抓取器一致的接口:
   - 创建一个支持异步上下文管理的类
   - 提供`fetch_*`方法获取数据
   - 将获取的数据转换为统一的`RawPost`格式
3. 在`__init__.py`中导出新的抓取器
4. 在`main_v2.py`中集成新的抓取器

示例模板:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
[新数据源] 抓取器
从[新数据源]获取数据并转换为统一的RawPost格式
"""

import asyncio
import aiohttp
from typing import List, Dict, Any

class NewSourceScraper:
    """[新数据源]数据抓取器"""
    
    def __init__(self):
        """初始化抓取器"""
        self.session = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    async def fetch_data(self, limit: int = 25) -> List[Dict[str, Any]]:
        """
        从[新数据源]获取数据
        
        Args:
            limit: 获取的最大数量
            
        Returns:
            转换为统一格式的帖子列表
        """
        # 实现获取数据的逻辑
        # 将数据转换为统一的RawPost格式
        # 返回结果
        pass 