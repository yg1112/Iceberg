#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Reddit抓取模块
"""

import asyncio
from src.scrapers.reddit_scraper import RedditScraper, DEFAULT_SUBREDDITS

async def test_scraper():
    print("开始测试Reddit抓取器...")
    
    async with RedditScraper() as scraper:
        # 测试1: 从默认subreddit抓取
        print("\n测试1: 从默认subreddit抓取")
        try:
            # 使用DEFAULT_SUBREDDITS中的第一个
            subreddit = DEFAULT_SUBREDDITS[0]
            posts = await scraper.fetch_subreddit_posts(subreddit, limit=5)
            print(f"✅ 成功从r/{subreddit}获取 {len(posts)} 个帖子")
            
            # 打印帖子信息
            for i, post in enumerate(posts):
                print(f"\n帖子 #{i+1}:")
                print(f"  标题: {post.get('title', 'N/A')}")
                print(f"  分数: {post.get('score', 'N/A')}")
                print(f"  评论数: {post.get('comment_count', 'N/A')}")
                print(f"  子版块: {post.get('subreddit', 'N/A')}")
                print(f"  URL: {post.get('url', 'N/A')}")
        except Exception as e:
            print(f"❌ 从默认subreddit抓取失败: {str(e)}")
        
        # 测试2: 从指定subreddit抓取
        print("\n测试2: 从指定subreddit抓取")
        try:
            subreddit = "apple"  # 使用一个热门子版块
            posts = await scraper.fetch_subreddit_posts(subreddit, limit=5)
            print(f"✅ 成功从r/{subreddit}获取 {len(posts)} 个帖子")
            
            # 打印帖子信息
            for i, post in enumerate(posts):
                print(f"\n帖子 #{i+1}:")
                print(f"  标题: {post.get('title', 'N/A')}")
                print(f"  分数: {post.get('score', 'N/A')}")
                print(f"  评论数: {post.get('comment_count', 'N/A')}")
                print(f"  子版块: {post.get('subreddit', 'N/A')}")
                print(f"  URL: {post.get('url', 'N/A')}")
        except Exception as e:
            print(f"❌ 从指定subreddit抓取失败: {str(e)}")
        
        # 测试3: 从多个subreddit抓取
        print("\n测试3: 从多个subreddit抓取")
        try:
            # 使用DEFAULT_SUBREDDITS中的前两个
            subreddits = DEFAULT_SUBREDDITS[:2]
            # 检查fetch_multiple_subreddits的参数
            try:
                posts = await scraper.fetch_multiple_subreddits(subreddits, limit_per_subreddit=3)
            except TypeError:
                # 如果上面的调用失败，尝试不同的参数名
                posts = await scraper.fetch_multiple_subreddits(subreddits, limit=3)
            
            print(f"✅ 成功从多个子版块获取 {len(posts)} 个帖子")
            
            # 统计每个子版块的帖子数量
            subreddit_counts = {}
            for post in posts:
                subreddit = post.get('subreddit', 'unknown')
                if subreddit in subreddit_counts:
                    subreddit_counts[subreddit] += 1
                else:
                    subreddit_counts[subreddit] = 1
            
            # 打印统计结果
            print("\n子版块统计:")
            for subreddit, count in subreddit_counts.items():
                print(f"  r/{subreddit}: {count}个帖子")
        except Exception as e:
            print(f"❌ 从多个subreddit抓取失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_scraper()) 