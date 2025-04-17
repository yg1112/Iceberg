#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
App Store Scraper Module

根据PRD v2要求实现的App Store异步数据抓取模块
支持从App Store获取应用评论和评分数据，并返回标准化的RawPost格式
"""

import asyncio
import httpx
import time
import random
from datetime import datetime
from typing import List, Dict, Any, Optional

# App Store API配置
APP_STORE_API_BASE = "https://itunes.apple.com"
APP_STORE_RSS_BASE = "https://itunes.apple.com/rss"

# 重试配置
MAX_RETRIES = 3
BASE_DELAY = 2  # 基础延迟秒数

class AppStoreScraper:
    """
    App Store异步抓取器
    使用httpx和asyncio实现异步抓取，支持指数回退重试
    """
    
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        """
        初始化App Store抓取器
        
        Args:
            client: 可选的httpx异步客户端，如果不提供则创建新的
        """
        self.client = client
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
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
    
    async def fetch_app_details(self, app_id: str, country: str = "us") -> Dict[str, Any]:
        """
        获取App Store应用详情
        
        Args:
            app_id: App Store应用ID
            country: 国家/地区代码
            
        Returns:
            应用详情数据
        """
        url = f"{APP_STORE_API_BASE}/lookup?id={app_id}&country={country}"
        data = await self.fetch_with_retry(url)
        
        if data.get("resultCount", 0) > 0:
            return data.get("results", [])[0]
        return {}
    
    async def fetch_app_reviews(self, app_id: str, country: str = "us", page: int = 1, sort: str = "mostRecent", limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取App Store应用评论
        
        Args:
            app_id: App Store应用ID
            country: 国家/地区代码
            page: 页码
            sort: 排序方式 (mostRecent, mostHelpful)
            limit: 返回的最大评论数量
            
        Returns:
            标准化的RawPost列表
        """
        # 使用RSS feed获取评论，因为官方API需要授权
        url = f"{APP_STORE_RSS_BASE}/customerreviews/page={page}/id={app_id}/sortBy={sort}/json?l=en&cc={country}"
        data = await self.fetch_with_retry(url)
        
        feed = data.get("feed", {})
        entries = feed.get("entry", [])
        
        # 第一个entry是应用信息，跳过
        if entries and "im:name" in entries[0]:
            entries = entries[1:]
        
        # 限制返回数量
        if limit and limit < len(entries):
            entries = entries[:limit]
        
        posts = []
        for entry in entries:
            # 提取评分
            rating = 0
            rating_node = entry.get("im:rating", {})
            if isinstance(rating_node, dict) and "label" in rating_node:
                try:
                    rating = int(rating_node["label"])
                except (ValueError, TypeError):
                    pass
            
            # 提取发布时间
            created_date = datetime.now()
            updated = entry.get("updated", {})
            if isinstance(updated, dict) and "label" in updated:
                try:
                    created_date = datetime.fromisoformat(updated["label"].replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass
            
            # 提取标题和内容
            title = ""
            title_node = entry.get("title", {})
            if isinstance(title_node, dict) and "label" in title_node:
                title = title_node["label"]
            
            content = ""
            content_node = entry.get("content", {})
            if isinstance(content_node, dict) and "label" in content_node:
                content = content_node["label"]
            
            # 提取作者
            author = ""
            author_node = entry.get("author", {}).get("name", {})
            if isinstance(author_node, dict) and "label" in author_node:
                author = author_node["label"]
            
            # 转换为标准化的RawPost格式
            raw_post = {
                "id": entry.get("id", {}).get("label", ""),
                "title": title,
                "content": content,
                "url": f"https://apps.apple.com/{country}/app/id{app_id}",
                "source": f"appstore/reviews/{app_id}",
                "score": rating,  # 使用评分作为分数
                "created_date": created_date,
                "comment_count": 0,  # App Store评论没有评论数
                "author": author,
                "metadata": {
                    "app_id": app_id,
                    "version": entry.get("im:version", {}).get("label", ""),
                    "rating": rating
                }
            }
            
            posts.append(raw_post)
        
        return posts
    
    async def fetch_app_rating_trend(self, app_id: str, country: str = "us", months: int = 6) -> Dict[str, Any]:
        """
        获取App Store应用评分趋势（最近几个月）
        
        Args:
            app_id: App Store应用ID
            country: 国家/地区代码
            months: 获取最近几个月的数据
            
        Returns:
            评分趋势数据
        """
        # 这里简化处理，实际实现可能需要更复杂的逻辑来获取历史评分
        # 可能需要使用第三方API或存储历史数据
        app_details = await self.fetch_app_details(app_id, country)
        
        current_rating = app_details.get("averageUserRating", 0)
        rating_count = app_details.get("userRatingCount", 0)
        
        # 模拟历史数据
        # 实际应用中应从数据库获取历史记录
        trend_data = {
            "current_rating": current_rating,
            "rating_count": rating_count,
            "trend": []
        }
        
        # 返回空趋势数据，实际应用中应填充真实数据
        return trend_data


async def fetch_app_reviews_batch(app_ids: List[str], country: str = "us", limit: int = 10) -> List[Dict[str, Any]]:
    """
    便捷函数，用于批量获取多个应用的评论
    
    Args:
        app_ids: App Store应用ID列表
        country: 国家/地区代码
        limit: 每个应用获取的评论数量
        
    Returns:
        标准化的RawPost列表
    """
    async with AppStoreScraper() as scraper:
        tasks = []
        for app_id in app_ids:
            # 计算需要获取的页数
            if limit <= 50:
                tasks.append(scraper.fetch_app_reviews(app_id, country, page=1, limit=limit))
            else:
                # 如果需要超过一页的数据，分页获取
                pages = (limit + 49) // 50  # 每页最多50条评论
                for page in range(1, pages + 1):
                    # 最后一页可能需要限制数量
                    if page == pages and limit % 50 != 0:
                        page_limit = limit % 50
                    else:
                        page_limit = 50
                    tasks.append(scraper.fetch_app_reviews(app_id, country, page=page, limit=page_limit))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_reviews = []
        for result in results:
            if isinstance(result, Exception):
                print(f"Error fetching app reviews: {str(result)}")
                continue
            
            all_reviews.extend(result)
        
        # 确保每个应用最多返回指定数量的评论
        return all_reviews[:limit * len(app_ids)]


# 测试代码
async def main():
    # 测试应用ID (例如: Notion, Evernote)
    app_ids = ["1352778147", "281796108"]
    
    reviews = await fetch_app_reviews_batch(app_ids, limit=3)
    print(f"获取到 {len(reviews)} 条评论")
    
    for review in reviews[:2]:  # 只打印前两条评论
        print(f"应用: {review['source']}")
        print(f"标题: {review['title']}")
        print(f"评分: {review['score']}")
        print(f"内容: {review['content'][:100]}...")
        print("---")


if __name__ == "__main__":
    asyncio.run(main())