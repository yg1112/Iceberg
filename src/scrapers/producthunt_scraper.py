#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Product Hunt Scraper Module

根据PRD v2要求实现的Product Hunt抓取模块
支持从Product Hunt论坛页面抓取数据，并返回标准化的RawPost格式
"""

import asyncio
import httpx
import time
import random
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

# Product Hunt URL配置
PH_WEB_URL = "https://www.producthunt.com"
PH_FORUM_URL = "https://www.producthunt.com/p/general" # 使用通用讨论区

# 重试配置
MAX_RETRIES = 3
BASE_DELAY = 2  # 基础延迟秒数

class ProductHuntScraper:
    """
    Product Hunt异步抓取器
    使用httpx和asyncio实现异步抓取，支持指数回退重试
    直接从网页抓取内容，无需API认证
    """
    
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        """
        初始化Product Hunt抓取器
        
        Args:
            client: 可选的httpx异步客户端，如果不提供则创建新的
        """
        self.client = client
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.producthunt.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
    
    async def __aenter__(self):
        if self.client is None:
            self.client = httpx.AsyncClient(headers=self.headers, follow_redirects=True)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client is not None:
            await self.client.aclose()
    
    async def fetch_with_retry(self, url: str) -> str:
        """
        带有指数回退重试的异步HTML请求
        
        Args:
            url: 请求的URL
            
        Returns:
            HTML响应内容
            
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
                return response.text
                
            except httpx.HTTPError as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                
                # 如果是429 Too Many Requests，增加延迟
                if getattr(e, "response", None) and e.response.status_code == 429:
                    await asyncio.sleep(delay * 2)
    
    async def extract_discussions_from_json(self, html: str) -> List[Dict[str, Any]]:
        """
        从HTML中提取包含讨论信息的JSON数据
        
        Args:
            html: 页面HTML内容
            
        Returns:
            讨论列表
        """
        # 尝试提取讨论列表的JSON数据
        discussions = []
        
        # 查找JSON格式的讨论数据
        pattern = r'\"@type\"\s*:\s*\"DiscussionForumPosting\".*?\"url\"\s*:\s*\"([^\"]+)\"'
        matches = re.finditer(pattern, html, re.DOTALL)
        
        for match in matches:
            start_idx = html.rfind('{', 0, match.start())
            if start_idx == -1:
                continue
                
            # 计算嵌套的JSON括号
            nested_level = 1
            end_idx = match.end()
            
            while nested_level > 0 and end_idx < len(html):
                if html[end_idx] == '{':
                    nested_level += 1
                elif html[end_idx] == '}':
                    nested_level -= 1
                end_idx += 1
            
            if nested_level == 0:
                json_str = html[start_idx:end_idx]
                try:
                    data = json.loads(json_str)
                    if data.get('@type') == 'DiscussionForumPosting':
                        discussions.append(data)
                except json.JSONDecodeError:
                    pass
        
        return discussions[:25]  # 最多返回25个讨论
        
    async def fetch_asks(self, limit: int = 25) -> List[Dict[str, Any]]:
        """
        从Product Hunt论坛页面抓取讨论内容
        
        Args:
            limit: 返回的帖子数量上限
            
        Returns:
            标准化的RawPost列表
        """
        html = await self.fetch_with_retry(PH_FORUM_URL)
        
        # 从HTML中提取讨论数据
        discussion_data = await self.extract_discussions_from_json(html)
        
        # 转换为标准RawPost格式
        posts = []
        for discussion in discussion_data[:limit]:
            # 提取创建日期
            created_at = discussion.get('dateCreated')
            try:
                created_date = datetime.fromisoformat(created_at.replace("Z", "+00:00")) if created_at else datetime.now()
            except (ValueError, AttributeError):
                created_date = datetime.now()
            
            # 提取作者信息
            author_info = discussion.get('author', {})
            author_name = author_info.get('name', '')
            
            # 提取URL和ID
            url = discussion.get('url', '')
            discussion_id = url.split('/')[-1] if url else ''
            
            # 提取点赞数
            interactions = discussion.get('interactionStatistic', [])
            votes = 0
            for interaction in interactions:
                if interaction.get('interactionType') == 'https://schema.org/LikeAction':
                    votes = interaction.get('userInteractionCount', 0)
                    break
            
            # 转换为标准格式
            raw_post = {
                "id": discussion_id,
                "title": discussion.get('headline', ''),
                "content": discussion.get('text', ''),
                "url": url,
                "source": "producthunt/discussions",
                "score": votes,
                "created_date": created_date,
                "comment_count": 0,  # 无法从JSON数据中直接获取评论数
                "author": author_name,
                "metadata": {
                    "author_name": author_name,
                    "topics": []  # 无法从JSON数据中直接获取主题标签
                }
            }
            
            posts.append(raw_post)
        
        return posts


async def fetch_producthunt_data(limit: int = 25) -> List[Dict[str, Any]]:
    """
    便捷函数，用于抓取Product Hunt数据
    
    Args:
        limit: 返回的帖子数量
        
    Returns:
        标准化的RawPost列表
    """
    async with ProductHuntScraper() as scraper:
        return await scraper.fetch_asks(limit)


# 测试代码
async def main():
    posts = await fetch_producthunt_data(limit=5)
    print(f"获取到 {len(posts)} 个帖子")
    for post in posts[:2]:  # 只打印前两个帖子
        print(f"标题: {post['title']}")
        print(f"分数: {post['score']}")
        print(f"URL: {post['url']}")
        print("---")


if __name__ == "__main__":
    asyncio.run(main())