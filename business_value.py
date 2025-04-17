import numpy as np
from sklearn.preprocessing import MinMaxScaler

class ValueAssessor:
    def __init__(self):
        self.scaler = MinMaxScaler()
        
    def tech_feasibility(self, dev_skills, api_dependencies, complexity):
        """
        技术可行性评估
        params:
        - dev_skills: 团队现有技术栈匹配度 (0-1)
        - api_dependencies: 第三方API依赖数量
        - complexity: 功能复杂度评分 (1-5)
        """
        weights = np.array([0.6, -0.25, -0.15])
        features = np.array([[dev_skills, api_dependencies, complexity]])
        return np.dot(features, weights).item()

    def market_saturation(self, competitor_count, growth_rate, churn_rate):
        """
        市场饱和度计算
        params:
        - competitor_count: 直接竞品数量
        - growth_rate: 市场月增长率 (%)
        - churn_rate: 用户流失率 (%)
        """
        return (competitor_count * 0.4 + 
               (1 - growth_rate/100) * 0.3 + 
               churn_rate/100 * 0.3)

    def monetization_potential(self, user_ltv, conversion_rate, support_cost):
        """
        变现潜力模型
        params:
        - user_ltv: 用户生命周期价值 ($)
        - conversion_rate: 免费转付费率 (%)
        - support_cost: 每用户支持成本 ($)
        """
        return (user_ltv * conversion_rate/100) - support_cost

    def build_matrix(self, features_dict):
        """
        生成三维评估矩阵
        features_dict: 包含所有评估参数的字典
        """
        tech = self.tech_feasibility(**features_dict['tech'])
        market = self.market_saturation(**features_dict['market'])
        revenue = self.monetization_potential(**features_dict['revenue'])
        
        matrix = np.zeros((3,3))
        matrix[0] = [tech, 0, 0]  # 技术维度
        matrix[1] = [0, market, 0]  # 市场维度
        matrix[2] = [0, 0, revenue]  # 收益维度
        
        # 标准化处理
        return self.scaler.fit_transform(matrix)

    def interpret_results(self, matrix):
        """
        矩阵结果解读与商业建议生成
        """
        tech_strength = matrix[0,0]
        market_opportunity = 1 - matrix[1,1]
        revenue_potential = matrix[2,2]
        
        if tech_strength > 0.7 and market_opportunity > 0.6:
            return {"建议": "蓝海机会", "行动项": ["快速MVP开发", "申请技术专利"]}
        elif revenue_potential > 0.8:
            return {"建议": "变现优先", "行动项": ["优化转化漏斗", "推出付费墙功能"]}
        else:
            return {"建议": "需重新评估", "行动项": ["竞品深度分析", "用户调研"]}
            
    def enrich_with_value_analysis(self, ideas_list):
        """
        为想法列表添加商业价值评估
        """
        for idea in ideas_list:
            # 简单模拟评估，实际应用中应该基于GPT分析结果进行更复杂的评估
            if 'gpt_analysis' in idea and idea['gpt_analysis']:
                # 提取关键词判断商业价值
                analysis = idea['gpt_analysis'].lower()
                
                # 简单评估逻辑
                if 'true' in analysis and ('monetizable' in analysis or 'solo_doable' in analysis):
                    idea['value_insight'] = "⭐⭐⭐⭐ 高商业价值，建议优先开发"
                elif 'false' in analysis and 'monetizable' in analysis:
                    idea['value_insight'] = "⭐⭐ 变现难度大，可作为开源项目"
                else:
                    idea['value_insight'] = "⭐⭐⭐ 中等商业价值，需进一步市场调研"
            else:
                idea['value_insight'] = "❓ 无法评估，缺少GPT分析数据"
                
        return ideas_list