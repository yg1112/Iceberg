import numpy as np
from datetime import datetime, timedelta

class DemandSupplyScorer:
    """
    Demand × Supply 评分引擎
    根据PRD要求实现：
    - Demand Score = (post_score × sentiment × recency)
    - Supply Score = (# existing apps × rating avg)
    - Gold‑Zone = Demand ≥ 70 & Supply ≤ 30
    """
    
    def __init__(self):
        # 标准化参数
        self.max_post_score = 1000  # 假设最高点赞数
        self.recency_days = 30      # 时间衰减窗口
        self.max_apps = 50          # 假设最大竞品数量
        self.max_rating = 5.0       # 评分满分
    
    def calculate_demand_score(self, post_score, sentiment, created_date):
        """
        计算需求分数
        params:
        - post_score: 帖子得分/点赞数
        - sentiment: 情感分析分数 (-1到1之间，1为最积极)
        - created_date: 创建日期 (datetime对象)
        """
        # 归一化点赞数 (0-100)
        normalized_score = min(100, (post_score / self.max_post_score) * 100)
        
        # 将情感分数转换为0-1范围
        normalized_sentiment = (sentiment + 1) / 2
        
        # 计算时间衰减因子 (1.0 - 0.0)
        days_old = (datetime.now() - created_date).days
        recency_factor = max(0, 1 - (days_old / self.recency_days))
        
        # 计算需求分数 (0-100)
        demand_score = normalized_score * normalized_sentiment * recency_factor
        
        return demand_score
    
    def calculate_supply_score(self, existing_apps_count, rating_avg):
        """
        计算供应分数
        params:
        - existing_apps_count: 现有应用数量
        - rating_avg: 平均评分 (通常为1-5)
        """
        # 归一化应用数量 (0-100)
        normalized_apps = min(100, (existing_apps_count / self.max_apps) * 100)
        
        # 归一化评分 (0-1)
        normalized_rating = rating_avg / self.max_rating
        
        # 计算供应分数 (0-100)
        supply_score = normalized_apps * normalized_rating
        
        return supply_score
    
    def is_gold_zone(self, demand_score, supply_score):
        """
        判断是否为黄金区域
        根据PRD: Gold‑Zone = Demand ≥ 70 & Supply ≤ 30
        """
        return demand_score >= 70 and supply_score <= 30
    
    def get_opportunity_matrix(self, ideas_list):
        """
        为想法列表生成机会矩阵
        """
        results = []
        
        for idea in ideas_list:
            # 提取必要数据
            post_score = idea.get('score', 0)
            
            # 从GPT分析中提取情感因素
            sentiment = 0.5  # 默认中性
            if 'gpt_analysis' in idea:
                analysis = idea['gpt_analysis'].lower()
                if 'unmet_need": true' in analysis:
                    sentiment = 0.8  # 提高情感分数
                if 'monetizable": true' in analysis:
                    sentiment += 0.1  # 额外加分
                sentiment = min(1.0, sentiment)  # 确保不超过1.0
            
            # 创建日期
            created_date = idea.get('created_date', datetime.now() - timedelta(days=7))
            
            # 假设的竞品数据 (实际应用中应从App Store/Chrome Store获取)
            # 这里使用简单模拟，实际实现应该连接到competitive_analysis.py
            existing_apps = np.random.randint(0, 30)  # 随机模拟竞品数量
            rating_avg = np.random.uniform(2.5, 4.8)  # 随机模拟评分
            
            # 计算分数
            demand_score = self.calculate_demand_score(post_score, sentiment, created_date)
            supply_score = self.calculate_supply_score(existing_apps, rating_avg)
            
            # 添加到结果
            idea['demand_score'] = round(demand_score, 1)
            idea['supply_score'] = round(supply_score, 1)
            idea['gold_zone'] = self.is_gold_zone(demand_score, supply_score)
            
            results.append(idea)
        
        # 按需求分数排序
        return sorted(results, key=lambda x: x['demand_score'], reverse=True)

# 示例用法
if __name__ == '__main__':
    # 测试数据
    test_ideas = [
        {
            'title': 'Need a better calendar app',
            'score': 150,
            'created_date': datetime.now() - timedelta(days=2),
            'gpt_analysis': '{"unmet_need": true, "monetizable": true}'
        },
        {
            'title': 'Looking for a note-taking app',
            'score': 75,
            'created_date': datetime.now() - timedelta(days=10),
            'gpt_analysis': '{"unmet_need": false, "monetizable": true}'
        }
    ]
    
    # 评分
    scorer = DemandSupplyScorer()
    results = scorer.get_opportunity_matrix(test_ideas)
    
    # 打印结果
    for idea in results:
        print(f"Title: {idea['title']}")
        print(f"Demand Score: {idea['demand_score']}")
        print(f"Supply Score: {idea['supply_score']}")
        print(f"Gold Zone: {'✅' if idea['gold_zone'] else '❌'}")
        print("---")