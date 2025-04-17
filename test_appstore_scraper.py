#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试App Store抓取模块
"""

import asyncio
from src.scrapers.appstore_scraper import AppStoreScraper

async def test_scraper():
    print("开始测试App Store抓取器...")
    
    # 一些常用应用的ID
    app_ids = [
        "1232780281",  # Notion
        "310633997",   # Evernote
        "1274495053",  # Things 3
    ]
    
    async with AppStoreScraper() as scraper:
        # 测试1: 获取单个应用评论
        print("\n测试1: 获取单个应用评论")
        try:
            app_id = app_ids[0]  # Notion
            reviews = await scraper.fetch_app_reviews(app_id, limit=5)
            print(f"✅ 成功获取 {len(reviews)} 条Notion评论")
            
            # 打印评论信息
            for i, review in enumerate(reviews):
                print(f"\n评论 #{i+1}:")
                print(f"  标题: {review.get('title', 'N/A')}")
                print(f"  内容前100字符: {review.get('content', 'N/A')[:100]}...")
                print(f"  评分: {review.get('score', 'N/A')}")
                print(f"  作者: {review.get('author', 'N/A')}")
                print(f"  日期: {review.get('created_date', 'N/A')}")
        except Exception as e:
            print(f"❌ 获取单个应用评论失败: {str(e)}")
        
        # 测试2: 获取应用详情
        print("\n测试2: 获取应用详情")
        try:
            app_id = app_ids[1]  # Evernote
            app_details = await scraper.fetch_app_details(app_id)
            print(f"✅ 成功获取Evernote应用详情")
            
            # 打印应用详情
            print(f"\n应用详情:")
            print(f"  名称: {app_details.get('name', 'N/A')}")
            print(f"  开发者: {app_details.get('developer', 'N/A')}")
            print(f"  类别: {app_details.get('category', 'N/A')}")
            print(f"  评分: {app_details.get('rating', 'N/A')}")
            print(f"  评分数量: {app_details.get('rating_count', 'N/A')}")
            print(f"  价格: {app_details.get('price', 'N/A')}")
            print(f"  版本: {app_details.get('version', 'N/A')}")
            print(f"  大小: {app_details.get('size', 'N/A')}")
        except Exception as e:
            print(f"❌ 获取应用详情失败: {str(e)}")
        
        # 测试3: 获取评分趋势
        print("\n测试3: 获取评分趋势")
        try:
            app_id = app_ids[2]  # Things 3
            rating_trend = await scraper.fetch_app_rating_trend(app_id)
            print(f"✅ 成功获取Things 3评分趋势")
            
            # 打印评分趋势
            print(f"\n评分趋势:")
            for date, rating in rating_trend.items():
                print(f"  {date}: {rating}")
        except Exception as e:
            print(f"❌ 获取评分趋势失败: {str(e)}")
        
        # 测试4: 批量获取应用评论
        print("\n测试4: 批量获取应用评论")
        try:
            # 使用所有测试应用ID
            batch_reviews = await scraper.fetch_app_reviews_batch(app_ids, limit_per_app=2)
            print(f"✅ 成功批量获取 {len(batch_reviews)} 条评论")
            
            # 统计每个应用的评论数量
            app_counts = {}
            for review in batch_reviews:
                app_id = review.get('app_id', 'unknown')
                if app_id in app_counts:
                    app_counts[app_id] += 1
                else:
                    app_counts[app_id] = 1
            
            # 打印统计结果
            print("\n应用评论统计:")
            for app_id, count in app_counts.items():
                print(f"  应用 {app_id}: {count}条评论")
        except Exception as e:
            print(f"❌ 批量获取应用评论失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_scraper()) 