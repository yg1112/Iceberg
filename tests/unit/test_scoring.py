#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
评分引擎单元测试

测试评分引擎的核心功能，包括：
1. 需求分数计算
2. 供应分数计算 
3. 机会分数计算
4. 黄金区域识别
"""

import unittest
import sys
import os
import math

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.scoring import ScoringEngine

class TestScoringEngine(unittest.TestCase):
    """测试评分引擎的功能"""
    
    def setUp(self):
        """设置测试环境"""
        self.scoring_engine = ScoringEngine()
        
        # 创建测试数据
        self.test_post = {
            "title": "Test Opportunity",
            "post_score": 100,
            "sentiment": 0.8,
            "velocity": 2.5,
            "app_count": 3,
            "avg_rating": 4.2
        }
    
    def test_demand_score_calculation(self):
        """测试需求分数计算公式"""
        # 根据公式: DemandScore = log10(post_score+1)*10 + sentiment*10 + velocity*20
        expected_score = math.log10(self.test_post["post_score"]+1)*10 + self.test_post["sentiment"]*10 + self.test_post["velocity"]*20
        actual_score = self.scoring_engine.calculate_demand_score(self.test_post)
        
        self.assertAlmostEqual(expected_score, actual_score, places=1)
    
    def test_supply_score_calculation(self):
        """测试供应分数计算公式"""
        # 根据公式: SupplyScore = app_count*5 + avg_rating*2
        expected_score = self.test_post["app_count"]*5 + self.test_post["avg_rating"]*2
        actual_score = self.scoring_engine.calculate_supply_score(self.test_post)
        
        self.assertAlmostEqual(expected_score, actual_score, places=1)
    
    def test_opportunity_score_calculation(self):
        """测试机会分数计算（需求分数-供应分数）"""
        demand_score = self.scoring_engine.calculate_demand_score(self.test_post)
        supply_score = self.scoring_engine.calculate_supply_score(self.test_post)
        expected_opportunity = demand_score - supply_score
        
        actual_opportunity = self.scoring_engine.calculate_opportunity_score(self.test_post)
        
        self.assertAlmostEqual(expected_opportunity, actual_opportunity, places=1)
    
    def test_gold_zone_identification(self):
        """测试黄金区域识别"""
        # 创建符合黄金区域条件的帖子
        gold_post = {
            "title": "Gold Zone Post",
            "demand_score": 80,
            "supply_score": 5,
            "opportunity_score": 75
        }
        
        # 创建不符合黄金区域条件的帖子
        non_gold_posts = [
            {
                "title": "Low Demand Post",
                "demand_score": 45,  # 低于50
                "supply_score": 5,
                "opportunity_score": 40
            },
            {
                "title": "High Supply Post",
                "demand_score": 80,
                "supply_score": 35,  # 高于30
                "opportunity_score": 45
            },
            {
                "title": "Low Opportunity Post",
                "demand_score": 75,
                "supply_score": 10,
                "opportunity_score": 65  # 低于70
            }
        ]
        
        # 测试黄金区域帖子应该被正确识别
        self.assertTrue(self.scoring_engine.is_gold_zone(gold_post))
        
        # 测试非黄金区域帖子应该被正确排除
        for post in non_gold_posts:
            self.assertFalse(self.scoring_engine.is_gold_zone(post))
    
    def test_scoring_pipeline(self):
        """测试完整评分流程"""
        # 创建原始帖子列表
        posts = [self.test_post]
        
        # 运行评分流程
        scored_posts = self.scoring_engine.score_posts(posts)
        
        # 验证必要的字段已添加
        self.assertIn("demand_score", scored_posts[0])
        self.assertIn("supply_score", scored_posts[0])
        self.assertIn("opportunity_score", scored_posts[0])
        self.assertIn("is_gold_zone", scored_posts[0])

if __name__ == "__main__":
    unittest.main() 