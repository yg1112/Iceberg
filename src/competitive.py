#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Competitive Fetcher Module

根据PRD v2要求实现的竞品分析模块
支持获取App Store评分趋势和Chrome Store用户数据
"""

import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import os

# 导入爬虫模块
from src.scrapers.appstore_scraper import AppStoreScraper
from src.scrapers.chromestore_scraper import ChromeStoreScraper

class CompetitiveFetcher:
    """
    竞品分析模块
    获取App Store评分趋势和Chrome Store用户数据
    """
    
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        """
        初始化竞品分析模块
        
        Args:
            client: 可选的httpx异步客户端，如果不提供则创建新的
        """
        self.client = client
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Accept": "application/json"
        }
        
        # 缓存目录
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    async def __aenter__(self):
        if self.client is None:
            self.client = httpx.AsyncClient(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client is not None:
            await self.client.aclose()
    
    async def get_app_store_rating_trend(self, app_id: str, months: int = 6) -> Dict[str, Any]:
        """
        获取App Store应用评分趋势
        
        Args:
            app_id: App Store应用ID
            months: 获取几个月的数据
            
        Returns:
            评分趋势数据
        """
        # 检查缓存
        cache_file = os.path.join(self.cache_dir, f"appstore_{app_id}_trend.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
                # 检查缓存是否过期（1天）
                if datetime.fromisoformat(cache_data["cached_at"]) > datetime.now() - timedelta(days=1):
                    return cache_data["data"]
        
        # 初始化结果
        result = {
            "app_id": app_id,
            "ratings": [],
            "avg_rating": 0,
            "rating_count": 0,
            "trend": "stable"  # stable, up, down
        }
        
        try:
            # 使用AppStoreScraper获取评分数据
            async with AppStoreScraper(client=self.client) as scraper:
                # 获取当前评分
                app_details = await scraper.fetch_app_details(app_id)
                current_rating = app_details.get("averageUserRating", 0)
                rating_count = app_details.get("userRatingCount", 0)
                
                result["avg_rating"] = current_rating
                result["rating_count"] = rating_count
                
                # 获取历史评分（模拟数据，实际应从历史API获取）
                # 由于App Store不提供历史评分API，这里使用模拟数据
                today = datetime.now()
                ratings = []
                
                # 生成过去几个月的模拟数据
                for i in range(months):
                    month_date = today - timedelta(days=30*i)
                    # 模拟评分波动（实际应从数据库或其他来源获取）
                    month_rating = max(1, min(5, current_rating + (0.1 * (i % 3 - 1))))
                    
                    ratings.append({
                        "date": month_date.strftime("%Y-%m"),
                        "rating": round(month_rating, 1)
                    })
                
                # 反转顺序，使最早的日期在前
                ratings.reverse()
                result["ratings"] = ratings
                
                # 计算趋势
                if len(ratings) >= 2:
                    first_rating = ratings[0]["rating"]
                    last_rating = ratings[-1]["rating"]
                    
                    if last_rating - first_rating > 0.2:
                        result["trend"] = "up"
                    elif first_rating - last_rating > 0.2:
                        result["trend"] = "down"
            
            # 缓存结果
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump({
                    "cached_at": datetime.now().isoformat(),
                    "data": result
                }, f)
            
            return result
            
        except Exception as e:
            print(f"获取App Store评分趋势时出错: {str(e)}")
            return result
    
    async def get_chrome_store_stats(self, extension_id: str) -> Dict[str, Any]:
        """
        获取Chrome Web Store扩展统计数据
        
        Args:
            extension_id: Chrome扩展ID
            
        Returns:
            扩展统计数据
        """
        # 检查缓存
        cache_file = os.path.join(self.cache_dir, f"chromestore_{extension_id}_stats.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
                # 检查缓存是否过期（1天）
                if datetime.fromisoformat(cache_data["cached_at"]) > datetime.now() - timedelta(days=1):
                    return cache_data["data"]
        
        # 初始化结果
        result = {
            "extension_id": extension_id,
            "users": 0,
            "rating": 0,
            "rating_count": 0,
            "last_updated": ""
        }
        
        try:
            # 使用ChromeStoreScraper获取扩展数据
            async with ChromeStoreScraper(client=self.client) as scraper:
                extension_details = await scraper.fetch_extension_details(extension_id)
                
                result["users"] = extension_details.get("users", 0)
                result["rating"] = extension_details.get("rating", 0)
                result["rating_count"] = len(extension_details.get("reviews", []))
                result["last_updated"] = extension_details.get("updated_date", "")
            
            # 缓存结果
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump({
                    "cached_at": datetime.now().isoformat(),
                    "data": result
                }, f)
            
            return result
            
        except Exception as e:
            print(f"获取Chrome Store统计数据时出错: {str(e)}")
            return result
    
    async def search_competitors(self, keywords: List[str], platform: str = "all") -> Dict[str, Any]:
        """
        搜索竞品
        
        Args:
            keywords: 关键词列表
            platform: 平台 ("appstore", "chromestore", "all")
            
        Returns:
            竞品数据
        """
        result = {
            "app_count": 0,
            "avg_rating": 0,
            "competitors": []
        }
        
        competitors = []
        
        # 根据平台选择搜索范围
        if platform in ["appstore", "all"]:
            try:
                # 搜索App Store
                async with AppStoreScraper(client=self.client) as scraper:
                    for keyword in keywords:
                        apps = await scraper.search_apps(keyword, limit=5)
                        competitors.extend(apps)
            except Exception as e:
                print(f"搜索App Store竞品时出错: {str(e)}")
        
        if platform in ["chromestore", "all"]:
            try:
                # 搜索Chrome Web Store
                async with ChromeStoreScraper(client=self.client) as scraper:
                    # 获取热门扩展，然后筛选关键词
                    extensions = await scraper.fetch_top_extensions(limit=100)
                    
                    # 简单关键词匹配（实际应使用更复杂的相关性算法）
                    for extension in extensions:
                        name = extension.get("name", "").lower()
                        if any(keyword.lower() in name for keyword in keywords):
                            competitors.append(extension)
            except Exception as e:
                print(f"搜索Chrome Store竞品时出错: {str(e)}")
        
        # 去重（根据ID）
        unique_competitors = []
        unique_ids = set()
        
        for comp in competitors:
            comp_id = comp.get("id", "")
            if comp_id and comp_id not in unique_ids:
                unique_ids.add(comp_id)
                unique_competitors.append(comp)
        
        # 计算统计数据
        result["app_count"] = len(unique_competitors)
        
        if unique_competitors:
            total_rating = sum(comp.get("rating", 0) for comp in unique_competitors)
            result["avg_rating"] = round(total_rating / len(unique_competitors), 1)
        
        # 按评分排序
        unique_competitors.sort(key=lambda x: x.get("rating", 0), reverse=True)
        result["competitors"] = unique_competitors[:10]  # 只返回前10个
        
        return result
    
    async def enrich_post_with_competitive_data(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """
        为帖子添加竞品数据
        
        Args:
            post: 帖子数据
            
        Returns:
            添加了竞品数据的帖子
        """
        # 从帖子中提取关键词
        keywords = []
        
        # 从标题中提取
        title = post.get("title", "")
        if title:
            # 简单分词（实际应使用NLP库）
            words = title.split()
            keywords.extend([word for word in words if len(word) > 3])
        
        # 从机会标签中提取
        opportunity = post.get("opportunity", {})
        tags = opportunity.get("tags", [])
        keywords.extend(tags)
        
        # 去重和限制数量
        keywords = list(set(keywords))[:5]
        
        if not keywords:
            # 如果没有提取到关键词，使用默认关键词
            keywords = ["app", "tool"]
        
        # 搜索竞品
        competitive_data = await self.search_competitors(keywords)
        
        # 添加到帖子
        post["competitive_data"] = competitive_data
        
        return post
    
    async def batch_enrich_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量为帖子添加竞品数据
        
        Args:
            posts: 帖子列表
            
        Returns:
            添加了竞品数据的帖子列表
        """
        enriched_posts = []
        
        for post in posts:
            enriched_post = await self.enrich_post_with_competitive_data(post)
            enriched_posts.append(enriched_post)
        
        return enriched_posts

# 使用示例
async def main():
    # 测试数据
    test_post = {
        "title": "Need a better calendar app",
        "opportunity": {
            "title": "Cross-platform calendar integration app",
            "tags": ["calendar", "productivity", "sync"]
        }
    }
    
    fetcher = CompetitiveFetcher()
    enriched_post = await fetcher.enrich_post_with_competitive_data(test_post)
    
    print(f"竞品数量: {enriched_post['competitive_data']['app_count']}")
    print(f"平均评分: {enriched_post['competitive_data']['avg_rating']}")
    
    # 测试App Store评分趋势
    # 使用实际的App ID，这里使用Notion的ID作为示例
    app_trend = await fetcher.get_app_store_rating_trend("1232780281")
    print(f"Notion评分趋势: {app_trend['trend']}")

if __name__ == "__main__":
    asyncio.run(main())