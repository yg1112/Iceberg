#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试散点图生成功能（使用新版本的ReportBuilder）
"""

from src.report import ReportBuilder

# 测试数据
test_posts = [
    {
        'opportunity': {'title': '智能日程规划助手', 'pain_summary': '用户需要一个能自动规划日程并根据优先级调整的智能助手'},
        'title': '智能日程规划助手',
        'url': 'https://www.reddit.com/r/productivity/1',
        'source': 'productivity',
        'created_str': '2025-04-15',
        'demand_score': 85,
        'supply_score': 25,
        'opportunity_score': 80,
        'gold_zone': True,
        'competitive_data': {'app_count': 3, 'avg_rating': 3.2}
    },
    {
        'opportunity': {'title': '多语言学习平台', 'pain_summary': '学习者需要一个整合多种语言学习方法的平台'},
        'title': '多语言学习平台',
        'url': 'https://www.reddit.com/r/languagelearning/2',
        'source': 'languagelearning',
        'created_str': '2025-04-10',
        'demand_score': 78,
        'supply_score': 45,
        'opportunity_score': 66,
        'gold_zone': True,
        'competitive_data': {'app_count': 8, 'avg_rating': 4.1}
    }
]

# 生成改进后的散点图
report_builder = ReportBuilder()
output_path = report_builder.generate_demand_supply_plot(test_posts, 'demand_supply_plot_improved.png')
print(f"生成的图表路径: {output_path}")

# 如果需要生成交互式散点图
try:
    interactive_path = report_builder.generate_plotly_demand_supply_chart(test_posts, 'demand_supply_matrix_interactive.html')
    print(f"生成的交互式图表路径: {interactive_path}")
except Exception as e:
    print(f"生成交互式图表时出错: {e}")