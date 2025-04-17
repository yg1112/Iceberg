#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Market Demand Radar - 市场需求雷达

根据PRD要求实现的市场需求分析工具，用于发现和评估未满足的数字产品需求。
主要功能：
1. 从Reddit等来源抓取数据
2. 使用GPT分析提取机会
3. 计算Demand×Supply评分
4. 生成报告并保存
"""

import os
import sys
from datetime import datetime
import argparse

# 导入项目模块
from analysis import analyze_post_with_gpt, save_to_markdown, reddit, KEYWORDS, SUBREDDITS
from business_value import ValueAssessor
from scoring_engine import DemandSupplyScorer
from competitive_analysis import CompetitorAnalyzer

# 设置命令行参数
def parse_args():
    parser = argparse.ArgumentParser(description="Market Demand Radar - 发现未满足的数字产品需求")
    parser.add_argument("-k", "--keywords", nargs="+", help="要搜索的关键词列表")
    parser.add_argument("-s", "--subreddits", nargs="+", help="要搜索的subreddit列表")
    parser.add_argument("-l", "--limit", type=int, default=100, help="每个subreddit搜索的帖子数量限制")
    parser.add_argument("-o", "--output", help="输出报告的文件名")
    parser.add_argument("--no-gpt", action="store_true", help="跳过GPT分析")
    return parser.parse_args()

# 主函数
def main():
    args = parse_args()
    
    # 使用命令行参数或默认值
    keywords = args.keywords or KEYWORDS
    subreddits = args.subreddits or SUBREDDITS
    post_limit = args.limit
    output_file = args.output
    skip_gpt = args.no_gpt
    
    print(f"🔍 开始搜索 {len(subreddits)} 个subreddit的 {len(keywords)} 个关键词...")
    
    # 收集想法
    ideas = []
    
    for subreddit_name in subreddits:
        try:
            subreddit = reddit.subreddit(subreddit_name)
            print(f"📱 正在搜索 r/{subreddit_name}...")
            
            # 搜索热门帖子
            for post in subreddit.hot(limit=post_limit):
                title = post.title.lower()
                
                # 检查是否包含关键词
                if any(keyword.lower() in title for keyword in keywords):
                    created_date = datetime.fromtimestamp(post.created_utc)
                    created_str = created_date.strftime("%Y-%m-%d")
                    
                    idea = {
                        "title": post.title,
                        "url": f"https://www.reddit.com{post.permalink}",
                        "subreddit": subreddit_name,
                        "score": post.score,
                        "created_date": created_date,
                        "created_str": created_str
                    }
                    
                    # GPT分析
                    if not skip_gpt:
                        print(f"🧠 GPT分析: {post.title[:40]}...")
                        gpt_result = analyze_post_with_gpt(post.title, subreddit_name, idea["url"])
                        idea["gpt_analysis"] = gpt_result
                    
                    ideas.append(idea)
                    print(f"✅ 找到想法: {post.title[:60]}... (👍 {post.score})")
        
        except Exception as e:
            print(f"❌ 搜索 r/{subreddit_name} 时出错: {str(e)}")
    
    if not ideas:
        print("❌ 未找到符合条件的想法，请尝试其他关键词或subreddit")
        return
    
    print(f"📊 找到 {len(ideas)} 个想法，开始评估...")
    
    # 商业价值评估
    value_assessor = ValueAssessor()
    ideas = value_assessor.enrich_with_value_analysis(ideas)
    
    # Demand × Supply 评分
    scorer = DemandSupplyScorer()
    scored_ideas = scorer.get_opportunity_matrix(ideas)
    
    # 生成报告
    if not output_file:
        today = datetime.today().strftime("%Y-%m-%d")
        output_file = f"top_ideas_{today}.md"
    
    # 确保reports目录存在
    reports_dir = "reports"
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    
    output_path = os.path.join(reports_dir, output_file)
    save_to_markdown(scored_ideas, output_path)
    
    print(f"✨ 分析完成! 报告已保存到: {output_path}")
    print(f"🏆 黄金区域想法数量: {sum(1 for idea in scored_ideas if idea.get('gold_zone', False))}")

if __name__ == "__main__":
    main()