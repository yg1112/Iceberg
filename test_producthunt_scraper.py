#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试ProductHunt抓取模块
"""

import asyncio
from src.scrapers.producthunt_scraper import ProductHuntScraper

async def test_scraper():
    print("开始测试ProductHunt抓取器...")
    
    async with ProductHuntScraper() as scraper:
        # 测试: 获取论坛讨论
        print("\n测试: 获取论坛讨论")
        try:
            posts = await scraper.fetch_asks(limit=5)
            print(f"✅ 成功获取 {len(posts)} 个讨论")
            
            # 打印讨论信息
            for i, post in enumerate(posts):
                print(f"\n讨论 #{i+1}:")
                print(f"  标题: {post.get('title', 'N/A')}")
                print(f"  内容前100字符: {post.get('content', 'N/A')[:100]}...")
                print(f"  分数: {post.get('score', 'N/A')}")
                print(f"  作者: {post.get('author', 'N/A')}")
                print(f"  URL: {post.get('url', 'N/A')}")
                print(f"  创建日期: {post.get('created_date', 'N/A')}")
        except Exception as e:
            print(f"❌ 获取论坛讨论失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_scraper()) 