#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
市场需求雷达 Pipeline 集成测试

测试整个处理流程的集成，包括：
1. 数据抓取
2. LLM分析
3. 评分计算
4. 报告生成
"""

import unittest
import sys
import os
import asyncio
from unittest.mock import patch, MagicMock

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.scrapers.reddit_scraper import RedditScraper
from src.extractor import LLMExtractor
from src.scoring import ScoringEngine
from src.competitive import CompetitiveFetcher
from src.report import ReportBuilder

class TestDataPipeline(unittest.TestCase):
    """测试数据处理流水线的集成功能"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建模拟数据
        self.mock_raw_posts = [
            {
                "id": "post1",
                "title": "I need a better calendar app that syncs between my devices",
                "content": "I'm looking for a calendar app that can sync between my Mac, iPhone and iPad seamlessly. Current solutions have sync delays or missing features.",
                "score": 45,
                "created_utc": 1650000000,
                "num_comments": 12,
                "subreddit": "macapps",
                "url": "https://www.reddit.com/r/macapps/comments/post1"
            },
            {
                "id": "post2",
                "title": "Need a good note-taking app with AI features",
                "content": "Looking for recommendations on note apps that can use AI to organize and summarize my notes automatically.",
                "score": 78,
                "created_utc": 1650010000,
                "num_comments": 23,
                "subreddit": "productivity",
                "url": "https://www.reddit.com/r/productivity/comments/post2"
            }
        ]
        
        self.mock_processed_posts = [
            {
                "id": "post1",
                "title": "Cross-platform calendar with reliable sync",
                "pain_summary": "用户需要在Mac、iPhone和iPad之间可靠同步的日历应用",
                "unmet_need": True,
                "solo_doable": True,
                "monetizable": True,
                "tags": ["calendar", "sync", "productivity", "ios", "macos"],
                "score": 45,
                "created_utc": 1650000000,
                "num_comments": 12,
                "subreddit": "macapps",
                "url": "https://www.reddit.com/r/macapps/comments/post1"
            },
            {
                "id": "post2",
                "title": "AI-powered note organization app",
                "pain_summary": "用户需要具有AI组织和总结功能的笔记应用",
                "unmet_need": True,
                "solo_doable": True,
                "monetizable": True,
                "tags": ["notes", "ai", "productivity"],
                "score": 78,
                "created_utc": 1650010000,
                "num_comments": 23,
                "subreddit": "productivity",
                "url": "https://www.reddit.com/r/productivity/comments/post2"
            }
        ]
        
        # 创建评分后的数据
        self.mock_scored_posts = [post.copy() for post in self.mock_processed_posts]
        self.mock_scored_posts[0].update({
            "post_score": 45,
            "sentiment": 0.8,
            "velocity": 2.5,
            "app_count": 3,
            "avg_rating": 4.2,
            "demand_score": 75.4,
            "supply_score": 23.4,
            "opportunity_score": 52.0,
            "is_gold_zone": False
        })
        self.mock_scored_posts[1].update({
            "post_score": 78,
            "sentiment": 0.9,
            "velocity": 3.2,
            "app_count": 2,
            "avg_rating": 3.8,
            "demand_score": 88.9,
            "supply_score": 17.6,
            "opportunity_score": 71.3,
            "is_gold_zone": True
        })
    
    @patch('src.scrapers.reddit_scraper.RedditScraper')
    @patch('src.extractor.LLMExtractor')
    @patch('src.scoring.ScoringEngine')
    @patch('src.competitive.CompetitiveFetcher')
    @patch('src.report.ReportBuilder')
    def test_full_pipeline_integration(self, mock_report_builder, mock_competitive, mock_scoring, mock_extractor, mock_reddit):
        """测试完整流水线集成"""
        # 设置模拟对象的行为
        mock_reddit_instance = MagicMock()
        mock_reddit.return_value.__aenter__.return_value = mock_reddit_instance
        mock_reddit_instance.fetch_subreddit_posts.return_value = self.mock_raw_posts
        
        mock_extractor_instance = MagicMock()
        mock_extractor.return_value = mock_extractor_instance
        mock_extractor_instance.batch_extract = AsyncMock(return_value=self.mock_processed_posts)
        
        mock_competitive_instance = MagicMock()
        mock_competitive.return_value = mock_competitive_instance
        mock_competitive_instance.batch_enrich_posts = AsyncMock(return_value=self.mock_processed_posts)
        
        mock_scoring_instance = MagicMock()
        mock_scoring.return_value = mock_scoring_instance
        mock_scoring_instance.score_posts.return_value = self.mock_scored_posts
        mock_scoring_instance.get_gold_zone_posts.return_value = [self.mock_scored_posts[1]]
        
        mock_report_instance = MagicMock()
        mock_report_builder.return_value = mock_report_instance
        mock_report_instance.generate_report.return_value = "report.md"
        
        # 模拟运行 main 函数中的主要流程
        async def run_pipeline():
            # 1. 获取数据
            async with RedditScraper() as scraper:
                raw_posts = await scraper.fetch_subreddit_posts("macapps")
            
            # 2. LLM分析
            extractor = LLMExtractor()
            processed_posts = await extractor.batch_extract(raw_posts)
            
            # 3. 添加竞争数据
            fetcher = CompetitiveFetcher()
            enriched_posts = await fetcher.batch_enrich_posts(processed_posts)
            
            # 4. 计算评分
            scorer = ScoringEngine()
            scored_posts = scorer.score_posts(enriched_posts)
            
            # 5. 筛选黄金区域
            gold_zone_posts = scorer.get_gold_zone_posts(scored_posts)
            
            # 6. 生成报告
            builder = ReportBuilder()
            report_path = builder.generate_report(scored_posts, "report.md")
            
            return {
                "raw_posts": raw_posts,
                "processed_posts": processed_posts,
                "enriched_posts": enriched_posts,
                "scored_posts": scored_posts,
                "gold_zone_posts": gold_zone_posts,
                "report_path": report_path
            }
        
        # 运行测试流水线
        results = asyncio.run(run_pipeline())
        
        # 验证流水线输出
        self.assertEqual(len(results["raw_posts"]), 2)
        self.assertEqual(len(results["processed_posts"]), 2)
        self.assertEqual(len(results["scored_posts"]), 2)
        self.assertEqual(len(results["gold_zone_posts"]), 1)
        self.assertEqual(results["gold_zone_posts"][0]["title"], "AI-powered note organization app")
        self.assertEqual(results["report_path"], "report.md")
        
        # 验证每个步骤都被调用
        mock_reddit_instance.fetch_subreddit_posts.assert_called_once()
        mock_extractor_instance.batch_extract.assert_called_once()
        mock_competitive_instance.batch_enrich_posts.assert_called_once()
        mock_scoring_instance.score_posts.assert_called_once()
        mock_scoring_instance.get_gold_zone_posts.assert_called_once()
        mock_report_instance.generate_report.assert_called_once()

# 用于异步模拟的帮助类
class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)

if __name__ == "__main__":
    unittest.main() 