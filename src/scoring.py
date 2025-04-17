#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scoring Engine Module

根据PRD v2要求实现的评分引擎模块
计算需求分数和供应分数，并识别黄金区域机会
"""

import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

class ScoringEngine:
    """
    评分引擎
    根据PRD v2要求实现：
    DemandScore = log10(post_score+1)*10 + sentiment*10 + velocity*20
    SupplyScore = app_count*5 + avg_rating*2
    Opportunity = DemandScore - SupplyScore
    """
    
    def __init__(self):
        # 黄金区域规则
        self.gold_zone_min_opportunity = 70
        self.gold_zone_min_demand = 50
        self.gold_zone_max_supply = 30
    
    def calculate_demand_score(self, post_score: int, sentiment: float, velocity: float) -> float:
        """
        计算需求分数
        
        Args:
            post_score: 帖子得分/点赞数
            sentiment: 情感分析分数 (0到1之间)
            velocity: 速度因子 (0到1之间)
            
        Returns:
            需求分数
        """
        # 根据PRD公式: log10(post_score+1)*10 + sentiment*10 + velocity*20
        log_score = math.log10(post_score + 1) * 10
        sentiment_score = sentiment * 10
        velocity_score = velocity * 20
        
        demand_score = log_score + sentiment_score + velocity_score
        return round(demand_score, 1)
    
    def calculate_supply_score(self, app_count: int, avg_rating: float) -> float:
        """
        计算供应分数
        
        Args:
            app_count: 现有应用数量
            avg_rating: 平均评分 (通常为1-5)
            
        Returns:
            供应分数
        """
        # 根据PRD公式: app_count*5 + avg_rating*2
        app_score = app_count * 5
        rating_score = avg_rating * 2
        
        supply_score = app_score + rating_score
        return round(supply_score, 1)
    
    def calculate_opportunity_score(self, demand_score: float, supply_score: float) -> float:
        """
        计算机会分数
        
        Args:
            demand_score: 需求分数
            supply_score: 供应分数
            
        Returns:
            机会分数
        """
        # 根据PRD公式: Opportunity = DemandScore - SupplyScore
        opportunity_score = demand_score - supply_score
        return round(opportunity_score, 1)
    
    def is_gold_zone(self, demand_score: float, supply_score: float, opportunity_score: float) -> bool:
        """
        判断是否为黄金区域
        根据PRD规则:
        Opportunity ≥ 70
        DemandScore ≥ 50
        SupplyScore ≤ 30
        
        Args:
            demand_score: 需求分数
            supply_score: 供应分数
            opportunity_score: 机会分数
            
        Returns:
            是否为黄金区域
        """
        return (opportunity_score >= self.gold_zone_min_opportunity and
                demand_score >= self.gold_zone_min_demand and
                supply_score <= self.gold_zone_max_supply)
    
    def extract_sentiment_from_opportunity(self, opportunity: Dict[str, Any]) -> float:
        """
        从机会数据中提取情感分数
        
        Args:
            opportunity: 机会数据
            
        Returns:
            情感分数 (0到1之间)
        """
        # 基础分数
        sentiment = 0.5
        
        # 根据unmet_need调整
        if opportunity.get("unmet_need", False):
            sentiment += 0.3
        
        # 根据monetizable调整
        if opportunity.get("monetizable", False):
            sentiment += 0.2
        
        # 确保不超过1.0
        return min(1.0, sentiment)
    
    def calculate_velocity(self, created_at: datetime, comments_count: int = 0) -> float:
        """
        计算速度因子
        
        Args:
            created_at: 创建时间
            comments_count: 评论数量
            
        Returns:
            速度因子 (0到1之间)
        """
        # 计算帖子年龄（天）
        age_days = (datetime.now() - created_at).days
        
        # 时间衰减因子 (1.0 - 0.0)，30天内的帖子有较高权重
        recency_factor = max(0, 1 - (age_days / 30))
        
        # 评论活跃度因子
        activity_factor = min(1.0, comments_count / 20)  # 20条评论视为最高活跃度
        
        # 综合计算速度因子
        velocity = (recency_factor * 0.7) + (activity_factor * 0.3)
        return velocity
    
    def score_post(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """
        为单个帖子评分
        
        Args:
            post: 帖子数据，包含score, created_at, opportunity等字段
            
        Returns:
            添加了评分信息的帖子数据
        """
        # 提取必要数据
        post_score = post.get("score", 0)
        created_at = post.get("created_at", datetime.now() - timedelta(days=7))
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except:
                created_at = datetime.now() - timedelta(days=7)
        
        comments_count = post.get("comments_count", 0)
        opportunity = post.get("opportunity", {})
        
        # 从竞品数据中提取应用数量和评分
        competitive_data = post.get("competitive_data", {})
        app_count = competitive_data.get("app_count", 1)  # 默认至少有1个应用
        avg_rating = competitive_data.get("avg_rating", 3.0)  # 默认平均评分3.0
        
        # 提取情感分数
        sentiment = self.extract_sentiment_from_opportunity(opportunity)
        
        # 计算速度因子
        velocity = self.calculate_velocity(created_at, comments_count)
        
        # 计算需求分数和供应分数
        demand_score = self.calculate_demand_score(post_score, sentiment, velocity)
        supply_score = self.calculate_supply_score(app_count, avg_rating)
        
        # 计算机会分数
        opportunity_score = self.calculate_opportunity_score(demand_score, supply_score)
        
        # 判断是否为黄金区域
        is_gold = self.is_gold_zone(demand_score, supply_score, opportunity_score)
        
        # 添加评分信息
        post["demand_score"] = demand_score
        post["supply_score"] = supply_score
        post["opportunity_score"] = opportunity_score
        post["gold_zone"] = is_gold
        post["scoring_factors"] = {
            "post_score": post_score,
            "sentiment": sentiment,
            "velocity": velocity,
            "app_count": app_count,
            "avg_rating": avg_rating
        }
        
        return post
    
    def score_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量为帖子评分
        
        Args:
            posts: 帖子列表
            
        Returns:
            添加了评分信息的帖子列表
        """
        scored_posts = [self.score_post(post) for post in posts]
        
        # 按机会分数降序排序
        scored_posts.sort(key=lambda x: x.get("opportunity_score", 0), reverse=True)
        
        return scored_posts
    
    def get_gold_zone_posts(self, posts: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取黄金区域帖子
        
        Args:
            posts: 帖子列表
            limit: 返回的最大数量
            
        Returns:
            黄金区域帖子列表
        """
        # 确保所有帖子都有评分
        scored_posts = [post if "opportunity_score" in post else self.score_post(post) for post in posts]
        
        # 筛选黄金区域帖子
        gold_zone_posts = [post for post in scored_posts if post.get("gold_zone", False)]
        
        # 按机会分数降序排序
        gold_zone_posts.sort(key=lambda x: x.get("opportunity_score", 0), reverse=True)
        
        return gold_zone_posts[:limit]

# 使用示例
def main():
    # 测试数据
    test_posts = [
        {
            "title": "Need a better calendar app",
            "score": 150,
            "created_at": datetime.now() - timedelta(days=2),
            "comments_count": 25,
            "opportunity": {
                "title": "Cross-platform calendar integration app",
                "unmet_need": True,
                "monetizable": True
            },
            "competitive_data": {
                "app_count": 3,
                "avg_rating": 3.2
            }
        },
        {
            "title": "Looking for a note-taking app",
            "score": 80,
            "created_at": datetime.now() - timedelta(days=10),
            "comments_count": 12,
            "opportunity": {
                "title": "AI-powered note organization",
                "unmet_need": False,
                "monetizable": True
            },
            "competitive_data": {
                "app_count": 8,
                "avg_rating": 4.1
            }
        }
    ]
    
    scoring_engine = ScoringEngine()
    scored_posts = scoring_engine.score_posts(test_posts)
    
    for post in scored_posts:
        print(f"标题: {post['title']}")
        print(f"需求分数: {post['demand_score']}")
        print(f"供应分数: {post['supply_score']}")
        print(f"机会分数: {post['opportunity_score']}")
        print(f"黄金区域: {'是' if post['gold_zone'] else '否'}")
        print("---")
    
    gold_zone_posts = scoring_engine.get_gold_zone_posts(scored_posts)
    print(f"黄金区域帖子数量: {len(gold_zone_posts)}")

if __name__ == "__main__":
    main()