#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Reddit Scraper Module

根据PRD v2要求实现的Reddit异步数据抓取模块
支持从多个subreddit异步抓取数据，并返回标准化的RawPost格式
"""

import asyncio
import httpx
import time
import random
from datetime import datetime
from typing import List, Dict, Any, Optional

# 默认抓取的subreddits
DEFAULT_SUBREDDITS = ["macapps", "iphone", "chrome_extensions"]

# Reddit API配置
REDDIT_API_BASE = "https://www.reddit.com"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"

# 重试配置
MAX_RETRIES = 3
BASE_DELAY = 2  # 基础延迟秒数

class RedditScraper:
    """
    Reddit异步抓取器
    使用httpx和asyncio实现异步抓取，支持指数回退重试
    """
    
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        """
        初始化Reddit抓取器
        
        Args:
            client: 可选的httpx异步客户端，如果不提供则创建新的
        """
        self.client = client
        self.headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json"
        }
    
    async def __aenter__(self):
        if self.client is None:
            self.client = httpx.AsyncClient(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client is not None:
            await self.client.aclose()
    
    async def fetch_with_retry(self, url: str) -> Dict[str, Any]:
        """
        带有指数回退重试的异步请求
        
        Args:
            url: 请求的URL
            
        Returns:
            解析后的JSON响应
            
        Raises:
            httpx.HTTPError: 如果所有重试都失败
        """
        for attempt in range(MAX_RETRIES):
            try:
                # 添加随机延迟以避免限流
                jitter = random.uniform(0.1, 0.5)
                delay = (BASE_DELAY ** attempt) + jitter
                
                if attempt > 0:
                    await asyncio.sleep(delay)
                
                response = await self.client.get(url)
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                
                # 如果是429 Too Many Requests，增加延迟
                if getattr(e, "response", None) and e.response.status_code == 429:
                    await asyncio.sleep(delay * 2)
    
    async def fetch_subreddit_posts(self, subreddit: str, limit: int = 25, timeframe: str = "week") -> List[Dict[str, Any]]:
        """
        抓取指定subreddit的帖子
        
        Args:
            subreddit: subreddit名称
            limit: 返回的帖子数量
            timeframe: 时间范围 (hour, day, week, month, year, all)
            
        Returns:
            标准化的RawPost列表
        """
        url = f"{REDDIT_API_BASE}/r/{subreddit}/top.json?t={timeframe}&limit={limit}"
        data = await self.fetch_with_retry(url)
        
        posts = []
        for post_data in data.get("data", {}).get("children", []):
            post = post_data.get("data", {})
            
            # 转换为标准化的RawPost格式
            created_utc = post.get("created_utc")
            created_date = datetime.fromtimestamp(created_utc) if created_utc else datetime.now()
            
            raw_post = {
                "id": post.get("id", ""),
                "title": post.get("title", ""),
                "content": post.get("selftext", ""),
                "url": f"{REDDIT_API_BASE}{post.get('permalink', '')}",
                "source": f"reddit/r/{subreddit}",
                "score": post.get("score", 0),
                "created_date": created_date,
                "comment_count": post.get("num_comments", 0),
                "author": post.get("author", ""),
                "metadata": {
                    "subreddit": subreddit,
                    "is_self": post.get("is_self", False),
                    "domain": post.get("domain", ""),
                    "upvote_ratio": post.get("upvote_ratio", 0)
                }
            }
            
            posts.append(raw_post)
        
        return posts
    
    async def fetch_multiple_subreddits(self, subreddits: List[str] = None, limit: int = 25, timeframe: str = "week") -> List[Dict[str, Any]]:
        """
        并发抓取多个subreddit的帖子
        
        Args:
            subreddits: subreddit名称列表，如果为None则使用默认列表
            limit: 每个subreddit返回的帖子数量
            timeframe: 时间范围
            
        Returns:
            所有subreddit的标准化RawPost列表
        """
        if subreddits is None:
            subreddits = DEFAULT_SUBREDDITS
        
        tasks = [self.fetch_subreddit_posts(subreddit, limit, timeframe) for subreddit in subreddits]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_posts = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error fetching subreddit {subreddits[i]}: {str(result)}")
                continue
            
            all_posts.extend(result)
        
        return all_posts


async def fetch_reddit_data(subreddits: List[str] = None, limit: int = 25, timeframe: str = "week") -> List[Dict[str, Any]]:
    """
    便捷函数，用于抓取Reddit数据
    
    Args:
        subreddits: subreddit名称列表
        limit: 每个subreddit返回的帖子数量
        timeframe: 时间范围
        
    Returns:
        标准化的RawPost列表
    """
    async with RedditScraper() as scraper:
        return await scraper.fetch_multiple_subreddits(subreddits, limit, timeframe)


# 测试代码
async def main():
    posts = await fetch_reddit_data(limit=5)
    print(f"获取到 {len(posts)} 个帖子")
    for post in posts[:2]:  # 只打印前两个帖子
        print(f"标题: {post['title']}")
        print(f"分数: {post['score']}")
        print(f"URL: {post['url']}")
        print("---")


if __name__ == "__main__":
    asyncio.run(main())