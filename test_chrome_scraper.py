#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Chrome Web Store抓取模块
"""

import asyncio
from src.scrapers.chromestore_scraper import ChromeStoreScraper

async def test_scraper():
    print("开始测试Chrome Web Store抓取器...")
    
    # 使用几个知名扩展的ID
    known_extension_ids = [
        "cjpalhdlnbpafiamejdnhcphjbkeiagm",  # uBlock Origin
        "mnjggcdmjocbbbhaepdhchncahnbgone",  # SponsorBlock for YouTube
        "nkbihfbeogaeaoehlefnkodbefgpgknn",  # MetaMask
    ]
    
    async with ChromeStoreScraper() as scraper:
        for ext_id in known_extension_ids:
            print(f"\n测试扩展ID: {ext_id}")
            
            # 测试1: 获取扩展详情
            print("测试1: 获取扩展详情")
            try:
                details = await scraper.fetch_extension_details(ext_id)
                print(f"✅ 成功获取扩展详情")
                
                print(f"\n扩展详情:")
                print(f"  名称: {details.get('name', 'N/A')}")
                print(f"  开发者: {details.get('developer', 'N/A')}")
                print(f"  评分: {details.get('rating', 'N/A')}")
                print(f"  用户数: {details.get('users', 'N/A')}")
                print(f"  更新日期: {details.get('updated_date', 'N/A')}")
                print(f"  描述前100字符: {details.get('description', 'N/A')[:100]}...")
                
                # 打印评论数量
                reviews = details.get('reviews', [])
                print(f"  评论数量: {len(reviews)}")
                if reviews:
                    print(f"  第一条评论: {reviews[0].get('comment', 'N/A')[:50]}...")
                
                # 测试2: 转换为RawPost格式
                print("\n测试2: 转换为RawPost格式")
                raw_post = await scraper.fetch_and_convert_to_raw_post(ext_id)
                print(f"✅ 成功转换为RawPost格式")
                
                print(f"\nRawPost数据:")
                print(f"  标题: {raw_post.get('title', 'N/A')}")
                print(f"  分数: {raw_post.get('score', 'N/A')}")
                print(f"  来源: {raw_post.get('source', 'N/A')}")
                print(f"  内容前100字符: {raw_post.get('content', 'N/A')[:100]}...")
                
                # 打印元数据
                metadata = raw_post.get('metadata', {})
                print(f"  用户数: {metadata.get('users', 'N/A')}")
                print(f"  评分: {metadata.get('rating', 'N/A')}")
                
            except Exception as e:
                print(f"❌ 测试扩展 {ext_id} 失败: {str(e)}")
            
            # 每个扩展测试后添加一些延迟，避免被限流
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(test_scraper()) 