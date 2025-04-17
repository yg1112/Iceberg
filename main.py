#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
市场需求雷达主程序 

自动抓取Reddit、Product Hunt等平台数据，
使用GPT分析市场需求和机会，并基于供需分析打分，
生成市场需求报告
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime
from typing import Dict, Any, List

# 导入项目模块
from src.scrapers.reddit_scraper import RedditScraper, DEFAULT_SUBREDDITS
from src.scrapers.producthunt_scraper import fetch_producthunt_data
from src.scrapers.appstore_scraper import AppStoreScraper
from src.scrapers.chromestore_scraper import ChromeStoreScraper
from src.extractor import LLMExtractor
from src.scoring import ScoringEngine
from src.competitive import CompetitiveFetcher
from src.report import ReportBuilder

# Set up command line arguments
def parse_args():
    parser = argparse.ArgumentParser(description="Market Demand Radar V2 - Discover unfulfilled digital product needs")
    parser.add_argument("-s", "--subreddits", nargs="+", help="List of subreddits to search")
    parser.add_argument("-l", "--limit", type=int, default=25, help="Limit of posts to search from each data source")
    parser.add_argument("-o", "--output", help="Output report filename")
    parser.add_argument("--no-gpt", action="store_true", help="Skip GPT analysis")
    parser.add_argument("--no-competitive", action="store_true", help="Skip competitive analysis")
    parser.add_argument("--gold-only", action="store_true", help="Only process golden zone opportunities")
    return parser.parse_args()

# Main function
async def main():
    args = parse_args()
    
    # Use command line arguments or default values
    subreddits = args.subreddits or DEFAULT_SUBREDDITS
    post_limit = args.limit
    output_file = args.output
    skip_gpt = args.no_gpt
    skip_competitive = args.no_competitive
    gold_only = args.gold_only
    
    print(f"🔍 Market Demand Radar V2 starting...")
    print(f"📱 Will fetch data from {len(subreddits)} subreddits, with a limit of {post_limit} posts each")
    
    # Collect raw posts
    raw_posts = []
    
    # 1. Fetch data from Reddit
    print("🔄 Fetching data from Reddit...")
    async with RedditScraper() as reddit_scraper:
        for subreddit_name in subreddits:
            try:
                print(f"  📥 Scraping r/{subreddit_name}...")
                posts = await reddit_scraper.fetch_subreddit_posts(subreddit_name, limit=post_limit)
                print(f"  ✅ Retrieved {len(posts)} posts from r/{subreddit_name}")
                raw_posts.extend(posts)
            except Exception as e:
                print(f"  ❌ Error scraping r/{subreddit_name}: {str(e)}")
    
    # 2. Fetch data from Product Hunt
    print("🔄 Fetching data from Product Hunt...")
    try:
        ph_posts = await fetch_producthunt_data(limit=post_limit)
        print(f"  ✅ Retrieved {len(ph_posts)} posts from Product Hunt")
        raw_posts.extend(ph_posts)
    except Exception as e:
        print(f"  ❌ Error scraping Product Hunt: {str(e)}")
    
    # 3. Fetch review data from App Store
    print("🔄 Fetching review data from App Store...")
    try:
        async with AppStoreScraper() as app_scraper:
            # Configure the list of app IDs to scrape
            app_ids = ["1232780281", "310633997", "1274495053"]  # Examples: Notion, Evernote, Things 3
            for app_id in app_ids:
                app_reviews = await app_scraper.fetch_app_reviews(app_id, limit=post_limit//len(app_ids))
                print(f"  ✅ Retrieved {len(app_reviews)} reviews from App ID {app_id}")
                raw_posts.extend(app_reviews)
    except Exception as e:
        print(f"  ❌ Error scraping App Store reviews: {str(e)}")
    
    # 4. Fetch data from Chrome Web Store
    print("🔄 Fetching data from Chrome Web Store...")
    try:
        async with ChromeStoreScraper() as chrome_scraper:
            # Get popular extensions
            extensions = await chrome_scraper.fetch_top_extensions(limit=10)
            print(f"  ✅ Retrieved {len(extensions)} popular extensions")
            
            # Get extension reviews
            for extension in extensions[:5]:  # Only process the top 5 extensions
                extension_id = extension["id"]
                extension_post = await chrome_scraper.fetch_and_convert_to_raw_post(extension_id)
                raw_posts.append(extension_post)
    except Exception as e:
        print(f"  ❌ Error scraping Chrome Web Store data: {str(e)}")
    
    if not raw_posts:
        print("❌ No posts found, please check data source configuration")
        return
    
    print(f"📊 Collected a total of {len(raw_posts)} raw posts, starting processing...")
    
    # 5. Use LLM to extract opportunity information
    if not skip_gpt:
        print("🧠 Using GPT-3.5-turbo to analyze and extract opportunity information...")
        extractor = LLMExtractor()
        processed_posts = await extractor.batch_extract(raw_posts)
        print(f"  ✅ Successfully analyzed {len(processed_posts)} posts")
    else:
        print("⏩ Skipping GPT analysis")
        processed_posts = raw_posts
    
    # 6. Add competitive data
    if not skip_competitive:
        print("🔍 Fetching competitive data...")
        fetcher = CompetitiveFetcher()
        enriched_posts = await fetcher.batch_enrich_posts(processed_posts)
        print(f"  ✅ Successfully added competitive data")
    else:
        print("⏩ Skipping competitive analysis")
        enriched_posts = processed_posts
    
    # 7. Calculate scores
    print("🧮 Calculating Demand×Supply scores...")
    scorer = ScoringEngine()
    scored_posts = scorer.score_posts(enriched_posts)
    print(f"  ✅ Successfully calculated scores")
    
    # 8. Filter golden zone opportunities
    gold_zone_posts = scorer.get_gold_zone_posts(scored_posts)
    print(f"  🥇 Discovered {len(gold_zone_posts)} golden zone opportunities")
    
    # 9. Generate report
    print("📝 Generating report...")
    builder = ReportBuilder()
    
    if not output_file:
        today = datetime.now().strftime("%Y-%m-%d")
        output_file = f"market_report_{today}.md"
    
    # Choose which posts to include in the report based on parameters
    report_posts = gold_zone_posts if gold_only else scored_posts
    
    report_path = builder.generate_report(report_posts, output_file)
    print(f"  ✅ Report generated: {report_path}")
    
    print("✨ Processing complete!")
    print(f"🏆 Number of golden zone opportunities: {len(gold_zone_posts)}")
    print(f"📊 Report path: {report_path}")

if __name__ == "__main__":
    asyncio.run(main())