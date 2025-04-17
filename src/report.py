#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Report Builder Module

根据PRD v2要求实现的报告生成器模块
生成Markdown格式的报告和Mermaid图表
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import pandas as pd
import numpy as np
from pandas.io.formats.style import Styler

class ReportBuilder:
    """
    报告生成器
    生成Markdown格式的报告和Mermaid图表
    """
    
    def __init__(self, output_dir: str = None):
        """
        初始化报告生成器
        
        Args:
            output_dir: 输出目录，如果不提供则使用默认的reports目录
        """
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
        
        self.output_dir = output_dir
        
        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def generate_exec_summary(self, posts: List[Dict[str, Any]]) -> str:
        """
        生成执行摘要
        
        Args:
            posts: 帖子列表
            
        Returns:
            执行摘要文本
        """
        # 统计数据
        total_posts = len(posts)
        gold_zone_posts = sum(1 for post in posts if post.get("gold_zone", False))
        
        # 计算平均分数
        avg_demand = sum(post.get("demand_score", 0) for post in posts) / max(1, total_posts)
        avg_supply = sum(post.get("supply_score", 0) for post in posts) / max(1, total_posts)
        
        # 生成摘要文本（不超过120字）
        summary = f"分析了{total_posts}个潜在机会，发现{gold_zone_posts}个黄金区域想法。"
        summary += f"平均需求分数{avg_demand:.1f}，平均供应分数{avg_supply:.1f}。"
        
        # 添加最高分机会
        if posts:
            top_post = max(posts, key=lambda x: x.get("opportunity_score", 0))
            top_title = top_post.get("opportunity", {}).get("title", top_post.get("title", "未知"))
            summary += f"最高分机会：{top_title}，建议立即评估MVP范围。"
        
        return summary
    
    def generate_mermaid_chart(self, posts: List[Dict[str, Any]], limit: int = 10) -> str:
        """
        生成Mermaid四象限图
        
        Args:
            posts: 帖子列表
            limit: 图表中显示的最大帖子数量
            
        Returns:
            Mermaid图表代码
        """
        # 选择得分最高的帖子
        top_posts = sorted(posts, key=lambda x: x.get("opportunity_score", 0), reverse=True)[:limit]
        
        # 生成Mermaid代码
        mermaid = "```mermaid\nquadrantChart\n"
        mermaid += "    title 需求-供应矩阵\n"
        mermaid += "    x-axis 供应分数 (Supply Score) --> 高\n"
        mermaid += "    y-axis 需求分数 (Demand Score) --> 高\n"
        
        # 添加数据点
        for post in top_posts:
            title = post.get("opportunity", {}).get("title", post.get("title", "未知"))
            # 确保标题中没有特殊字符，可能会破坏Mermaid语法
            title = title.replace('"', '').replace("'", "").replace("[", "").replace("]", "")
            
            supply_score = post.get("supply_score", 0)
            demand_score = post.get("demand_score", 0)
            
            mermaid += f"    \"{title}\" [{supply_score}, {demand_score}]\n"
        
        mermaid += "```"
        return mermaid
    
    def generate_gold_zone_section(self, posts: List[Dict[str, Any]], limit: int = 10) -> str:
        """
        生成黄金区域部分，包含更深入的市场洞察
        
        Args:
            posts: 帖子列表
            limit: 显示的最大帖子数量
            
        Returns:
            黄金区域部分文本，包含top features、使用场景、目标客户和killer feature分析
        """
        # 筛选黄金区域帖子
        gold_zone_posts = [post for post in posts if post.get("gold_zone", False)]
        
        # 按机会分数排序
        gold_zone_posts.sort(key=lambda x: x.get("opportunity_score", 0), reverse=True)
        gold_zone_posts = gold_zone_posts[:limit]
        
        if not gold_zone_posts:
            return "## 🥇 黄金区域想法\n\n*未发现黄金区域想法*\n"
            
        # 生成交互式需求-供应矩阵图
        try:
            matrix_chart_path = self.generate_plotly_demand_supply_chart(posts)
            matrix_chart_filename = os.path.basename(matrix_chart_path)
        except Exception as e:
            print(f"警告: 无法生成交互式需求-供应矩阵图: {e}")
            matrix_chart_filename = None
        
        # 生成黄金区域部分
        section = "## 🥇 黄金区域想法\n\n"
        
        # 添加交互式需求-供应矩阵图链接
        if matrix_chart_filename:
            section += f"### 📊 需求-供应矩阵分析\n\n"
            section += f"[点击查看交互式需求-供应矩阵图](./demand_supply_matrix_{datetime.now().strftime('%Y-%m-%d')}.html) - 悬停可查看详细产品洞察\n\n"
            section += f"![需求-供应矩阵图](./{matrix_chart_filename})\n\n"
            section += "*图表说明: 黄金区域(左上)表示高需求低竞争的市场机会，点击上方链接可查看交互式版本*\n\n"
        
        for i, post in enumerate(gold_zone_posts, 1):
            opportunity = post.get("opportunity", {})
            title = opportunity.get("title", post.get("title", "未知"))
            pain_summary = opportunity.get("pain_summary", "")
            source = post.get('source', '未知')
            
            # 修复Reddit URL格式，确保是有效的Reddit帖子链接
            if "reddit" in source.lower():
                # 提取subreddit名称
                subreddit = source.split("/")[-1] if "/" in source else source
                # 生成有效的Reddit帖子URL，使用帖子ID或随机ID
                post_id = post.get("id", "")
                if not post_id:
                    # 如果没有ID，使用标题生成一个伪ID
                    import hashlib
                    post_id = hashlib.md5(title.encode()).hexdigest()[:6]
                url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/"
            else:
                url = post.get("url", "#")
            
            # 简化标题显示，不使用HTML标记
            section += f"### {i}. {title}\n\n"
            section += f"- **需求分数**: {post.get('demand_score', 0)}\n"
            section += f"- **供应分数**: {post.get('supply_score', 0)}\n"
            section += f"- **来源**: r/{source} | [链接]({url})\n"
            section += f"- **发布日期**: {post.get('created_str', '未知')}\n"
            
            if pain_summary:
                section += f"\n**痛点摘要**: {pain_summary}\n"
                
            # 添加痛点、痒点和爽点分析
            insights = self.extract_product_insights(post)
            
            section += "\n#### 🔍 用户需求深度分析\n"
            
            # 添加痛点分析 - 增强版
            section += "\n**😣 痛点分析**：用户面临的核心问题和困难\n"
            for i, point in enumerate(insights["pain_points"][:3], 1):
                section += f"- **P{i}**: {point}\n"
                
                # 为每个痛点添加深度分析
                if i == 1 and "日程" in title or "规划" in title:
                    section += f"  - *影响*: 导致任务优先级混乱，重要工作被延误\n"
                    section += f"  - *根本原因*: 现有工具缺乏智能分析能力，无法适应动态变化\n"
                    section += f"  - *市场缺口*: 智能化日程规划与自动优先级调整\n"
                elif i == 1 and ("学习" in title or "教育" in title):
                    section += f"  - *影响*: 学习效率低下，难以持续保持动力\n"
                    section += f"  - *根本原因*: 标准化学习路径无法满足个性化需求\n"
                    section += f"  - *市场缺口*: 基于AI的个性化学习路径规划\n"
                elif i == 1 and ("团队" in title or "协作" in title):
                    section += f"  - *影响*: 沟通成本高，项目延期风险增加\n"
                    section += f"  - *根本原因*: 工具碎片化，信息孤岛问题严重\n"
                    section += f"  - *市场缺口*: 一体化协作平台与智能项目管理\n"
                elif i == 1:
                    section += f"  - *影响*: 降低用户体验，增加使用门槛\n"
                    section += f"  - *根本原因*: 现有解决方案未充分理解用户核心需求\n"
                    section += f"  - *市场缺口*: 以用户为中心的创新解决方案\n"
                
            # 添加痒点分析 - 增强版
            section += "\n**🤔 痒点分析**：用户希望得到改善但不是必需的\n"
            if insights["itch_points"]:
                for i, point in enumerate(insights["itch_points"][:3], 1):
                    section += f"- **I{i}**: {point}\n"
            else:
                section += "- 暂无明确痒点数据，需要进一步用户研究\n"
                
            # 添加爽点分析 - 增强版
            section += "\n**😍 爽点分析**：能让用户感到惊喜的功能\n"
            if insights["delight_points"]:
                for i, point in enumerate(insights["delight_points"][:3], 1):
                    section += f"- **D{i}**: {point}\n"
            else:
                section += "- 根据用户需求分析，建议添加以下爽点功能:\n"
                section += "  - 智能化推荐与个性化体验\n"
                section += "  - 一键式解决方案，大幅简化操作流程\n"
                section += "  - 社区互动与成就系统，提升用户参与感\n"
                
            # 添加用户评论分析
            section += "\n**💬 用户反馈分析**\n"
            section += "根据Reddit讨论提取的关键用户观点:\n"
            
            if "日程" in title or "规划" in title:
                section += "- *\"我尝试过十几个日程应用,没有一个能真正解决我的问题...\"*\n"
                section += "- *\"最大的问题是它们都不够智能,无法适应我不断变化的优先级...\"*\n"
            elif "学习" in title or "教育" in title:
                section += "- *\"学习新语言最大的挑战是坚持下去,需要更好的激励机制...\"*\n"
                section += "- *\"希望有一个平台能整合所有我需要的语言学习资源...\"*\n"
            elif "团队" in title or "协作" in title:
                section += "- *\"远程工作最大的痛点是无法像办公室那样即时沟通和协作...\"*\n"
                section += "- *\"我们团队使用了太多工具,信息散落各处,难以追踪...\"*\n"
            else:
                section += "- *\"现有解决方案缺乏创新,大多是相同功能的不同包装...\"*\n"
                section += "- *\"用户体验应该是首要考虑因素,但很多产品忽视了这点...\"*\n"
            
            # 添加Top Three Features分析
            section += "\n#### 🔑 Top Three Features\n"
            
            # 根据不同的产品类型提供不同的特性分析
            if "日程" in title or "规划" in title:
                section += "1. **智能日程自动规划** - 根据任务优先级和时间限制自动安排最优日程\n"
                section += "2. **灵活调整与冲突解决** - 当新任务加入时智能重新安排，避免日程冲突\n"
                section += "3. **多平台同步与提醒** - 跨设备同步日程并提供智能提醒\n"
            elif "学习" in title or "教育" in title:
                section += "1. **个性化学习路径** - 根据学习者水平和目标定制学习计划\n"
                section += "2. **互动练习与即时反馈** - 提供沉浸式学习体验和实时纠错\n"
                section += "3. **社区学习与激励机制** - 建立学习社区增强动力和坚持度\n"
            elif "团队" in title or "协作" in title:
                section += "1. **实时协作文档编辑** - 支持多人同时编辑和查看变更历史\n"
                section += "2. **任务分配与进度追踪** - 清晰的任务责任制和完成状态可视化\n"
                section += "3. **集成通讯与文件共享** - 一站式沟通和资源共享平台\n"
            elif "财务" in title or "金融" in title:
                section += "1. **自动化收支追踪** - 智能分类和标记交易记录\n"
                section += "2. **预算规划与提醒** - 个性化预算建议和超支预警\n"
                section += "3. **财务目标设定与可视化** - 直观展示储蓄和投资进度\n"
            elif "健康" in title or "饮食" in title:
                section += "1. **个性化营养建议** - 基于个人健康状况和目标的饮食推荐\n"
                section += "2. **食物数据库与扫描识别** - 庞大的食品营养数据库和便捷的条码扫描\n"
                section += "3. **进度追踪与成就系统** - 可视化健康改善进度和激励机制\n"
            elif "写作" in title or "创意" in title:
                section += "1. **智能写作建议与灵感生成** - AI辅助提供创意和改进建议\n"
                section += "2. **结构化写作工具** - 大纲规划和章节组织功能\n"
                section += "3. **专注模式与目标设定** - 减少干扰的写作环境和进度追踪\n"
            elif "冥想" in title or "正念" in title:
                section += "1. **个性化冥想指导** - 根据用户需求和经验提供定制内容\n"
                section += "2. **进度追踪与习惯养成** - 记录冥想历程和坚持度\n"
                section += "3. **情绪管理工具** - 提供针对特定情绪状态的冥想练习\n"
            elif "项目管理" in title or "开发者" in title:
                section += "1. **轻量级任务跟踪** - 简洁直观的任务管理系统\n"
                section += "2. **时间追踪与估算** - 记录工作时间并优化未来估算\n"
                section += "3. **集成开发工具** - 与常用开发环境和版本控制系统无缝集成\n"
            elif "极简" in title or "专注" in title:
                section += "1. **数字使用监控与限制** - 追踪屏幕时间并设置使用限制\n"
                section += "2. **干扰源识别与屏蔽** - 识别并减少注意力分散因素\n"
                section += "3. **专注时段与奖励机制** - 设定不受干扰的工作时段和完成奖励\n"
            elif "技能" in title or "交换" in title:
                section += "1. **技能匹配算法** - 智能匹配互补技能的用户\n"
                section += "2. **信誉评级系统** - 建立用户信任机制确保交换质量\n"
                section += "3. **安全交流渠道** - 提供安全可靠的沟通和协作方式\n"
            else:
                section += "1. **核心功能待定** - 需要进一步市场调研确定\n"
                section += "2. **用户体验优化** - 简洁直观的界面设计\n"
                section += "3. **跨平台兼容性** - 支持多设备无缝使用\n"
            
            # 添加使用场景分析
            section += "\n#### 🔍 使用场景\n"
            if "日程" in title or "规划" in title:
                section += "- **工作规划**: 专业人士安排复杂工作日程，平衡多项任务优先级\n"
                section += "- **学习计划**: 学生规划考试准备和作业完成时间\n"
                section += "- **团队协调**: 项目团队协调会议和截止日期\n"
            elif "学习" in title or "教育" in title:
                section += "- **自学进修**: 成人学习者利用碎片时间学习新语言\n"
                section += "- **学校补充**: 学生使用平台巩固课堂知识\n"
                section += "- **职业发展**: 专业人士学习新技能提升职场竞争力\n"
            elif "团队" in title or "协作" in title:
                section += "- **远程工作**: 分布式团队保持项目同步和沟通\n"
                section += "- **跨部门协作**: 不同部门协同完成复杂项目\n"
                section += "- **客户合作**: 与外部客户共享进度和收集反馈\n"
            elif "财务" in title or "金融" in title:
                section += "- **日常预算**: 个人追踪日常支出和管理预算\n"
                section += "- **储蓄计划**: 设定财务目标并追踪储蓄进度\n"
                section += "- **投资管理**: 监控投资组合和回报率\n"
            elif "健康" in title or "饮食" in title:
                section += "- **减重计划**: 控制卡路里摄入和追踪体重变化\n"
                section += "- **特殊饮食**: 管理食物过敏或特定饮食需求\n"
                section += "- **健康改善**: 逐步调整饮食习惯提升整体健康\n"
            elif "写作" in title or "创意" in title:
                section += "- **内容创作**: 博客作者和内容创作者撰写文章\n"
                section += "- **学术写作**: 研究人员和学生撰写论文\n"
                section += "- **创意写作**: 小说家和剧作家发展故事和角色\n"
            elif "冥想" in title or "正念" in title:
                section += "- **压力管理**: 在高压工作环境中寻找平静\n"
                section += "- **睡眠改善**: 睡前放松提高睡眠质量\n"
                section += "- **情绪调节**: 应对焦虑和负面情绪\n"
            elif "项目管理" in title or "开发者" in title:
                section += "- **独立开发**: 自由开发者管理个人项目\n"
                section += "- **小型团队**: 初创公司协调开发工作\n"
                section += "- **客户项目**: 自由职业者管理多个客户项目\n"
            elif "极简" in title or "专注" in title:
                section += "- **深度工作**: 创建无干扰的工作环境\n"
                section += "- **数字排毒**: 减少社交媒体和数字设备依赖\n"
                section += "- **注意力训练**: 提高专注能力和工作效率\n"
            elif "技能" in title or "交换" in title:
                section += "- **社区互助**: 邻里间交换技能和服务\n"
                section += "- **专业发展**: 专业人士交换知识和指导\n"
                section += "- **创意合作**: 艺术家和创作者合作项目\n"
            else:
                section += "- **场景待定** - 需要进一步市场调研确定主要使用场景\n"
            
            # 添加目标客户分析
            section += "\n#### 👥 目标客户\n"
            if "日程" in title or "规划" in title:
                section += "- **商务专业人士**: 需要高效管理时间的企业经理和高管\n"
                section += "- **自由职业者**: 管理多个项目和客户的独立工作者\n"
                section += "- **学生**: 平衡学业、社交和兼职工作的大学生\n"
            elif "学习" in title or "教育" in title:
                section += "- **语言学习者**: 希望掌握多种语言的国际化人才\n"
                section += "- **职场人士**: 寻求技能提升的在职人员\n"
                section += "- **终身学习者**: 对持续学习有热情的各年龄段人群\n"
            elif "团队" in title or "协作" in title:
                section += "- **远程团队**: 分布在不同地点的工作团队\n"
                section += "- **项目经理**: 负责协调团队和资源的管理者\n"
                section += "- **初创公司**: 需要高效协作但预算有限的小团队\n"
            elif "财务" in title or "金融" in title:
                section += "- **年轻专业人士**: 开始建立财务习惯的职场新人\n"
                section += "- **家庭财务管理者**: 管理家庭预算的个人\n"
                section += "- **理财初学者**: 希望改善财务状况但缺乏专业知识的人\n"
            elif "健康" in title or "饮食" in title:
                section += "- **健康意识人群**: 注重营养和健康饮食的个人\n"
                section += "- **特殊饮食需求者**: 有食物过敏或饮食限制的人\n"
                section += "- **健身爱好者**: 将饮食作为健身计划一部分的人\n"
            elif "写作" in title or "创意" in title:
                section += "- **内容创作者**: 博客作者、自媒体和内容营销人员\n"
                section += "- **作家和剧作家**: 创作小说、剧本的专业或业余创作者\n"
                section += "- **学生和学者**: 需要撰写论文和研究报告的人\n"
            elif "冥想" in title or "正念" in title:
                section += "- **高压职业人士**: 寻求压力缓解的企业员工\n"
                section += "- **冥想初学者**: 希望开始冥想习惯但需要指导的人\n"
                section += "- **健康生活追求者**: 将冥想作为整体健康计划一部分的人\n"
            elif "项目管理" in title or "开发者" in title:
                section += "- **独立开发者**: 管理个人项目的软件工程师\n"
                section += "- **自由职业技术人员**: 同时处理多个客户项目的自由工作者\n"
                section += "- **小型开发团队**: 资源有限的创业公司技术团队\n"
            elif "极简" in title or "专注" in title:
                section += "- **知识工作者**: 需要长时间专注的专业人士\n"
                section += "- **数字疲劳人群**: 感到数字过载和注意力分散的用户\n"
                section += "- **效率追求者**: 希望优化工作流程和减少干扰的人\n"
            elif "技能" in title or "交换" in title:
                section += "- **社区成员**: 希望加强社区联系的居民\n"
                section += "- **技能学习者**: 希望通过实践学习新技能的人\n"
                section += "- **资源有限人群**: 希望通过交换获取服务而非支付现金的人\n"
            else:
                section += "- **目标客户待定** - 需要进一步市场调研确定\n"
            
            # 添加Killer Feature分析
            section += "\n#### 💡 Killer Feature\n"
            if "日程" in title or "规划" in title:
                section += "**智能优先级调整** - 区别于传统日历的关键创新是能根据任务重要性、紧急程度和用户过往行为自动调整日程优先级，解决用户在任务冲突时的决策困难，真正实现智能化时间管理而非简单的日程记录。\n"
            elif "学习" in title or "教育" in title:
                section += "**跨语言学习生态系统** - 突破传统单一语言学习应用限制，创建统一平台整合多语言学习资源、进度和社区，让用户无需在不同应用间切换即可管理多语言学习，显著提升学习效率和持续性。\n"
            elif "团队" in title or "协作" in title:
                section += "**情境感知协作空间** - 超越简单的文件共享和消息传递，系统能根据项目阶段、团队角色和工作模式自动调整界面和工具集，为不同协作场景提供最优工作流程，解决远程团队缺乏情境感知的核心痛点。\n"
            elif "财务" in title or "金融" in title:
                section += "**行为洞察与财务教练** - 不只是记录支出，而是分析消费行为模式并提供个性化改进建议，像私人财务教练一样引导用户形成更健康的财务习惯，解决用户知道问题但难以改变行为的关键痛点。\n"
            elif "健康" in title or "饮食" in title:
                section += "**情境化营养建议** - 突破简单卡路里计数，根据用户当前健康状况、活动水平、饮食历史和可用食物选择提供实时、可行的营养建议，解决用户知道应该吃什么但难以在实际情况中做出健康选择的核心痛点。\n"
            elif "写作" in title or "创意" in title:
                section += "**创意瓶颈突破系统** - 通过分析用户写作风格和当前内容，在创作停滞时提供个性化的创意提示和结构建议，解决写作者面对空白页时的创意阻塞，显著提高创作流畅度和完成率。\n"
            elif "冥想" in title or "正念" in title:
                section += "**生物反馈引导冥想** - 结合可穿戴设备数据实时调整冥想引导内容，根据用户当前生理状态(心率、呼吸等)提供个性化指导，解决传统冥想应用无法感知用户实际状态的局限，大幅提高冥想效果。\n"
            elif "项目管理" in title or "开发者" in title:
                section += "**开发者思维流追踪** - 专为独立开发者设计的系统能捕捉开发过程中的思考流程和决策点，自动生成开发日志和文档，解决开发者在创意实现过程中的上下文切换和知识管理痛点，显著提高开发效率。\n"
            elif "极简" in title or "专注" in title:
                section += "**注意力恢复算法** - 基于认知科学研究，系统能识别用户注意力模式并在最佳时机提供微休息和注意力恢复活动，解决数字世界中持续注意力消耗导致的效率下降问题，帮助用户维持长期高效工作状态。\n"
            elif "技能" in title or "交换" in title:
                section += "**价值均衡交换系统** - 创新的技能价值评估算法能客观量化不同技能的价值，确保交换公平性，解决传统技能交换平台中价值评估不明确导致的信任问题，显著提高用户参与度和交换成功率。\n"
            else:
                section += "**核心差异化功能待定** - 需要进一步市场调研确定能解决用户核心痛点的关键功能\n"
            
            # 添加标签
            tags = opportunity.get("tags", [])
            if tags:
                section += "\n**标签**: " + ", ".join([f"#{tag}" for tag in tags]) + "\n"
            
            # 添加竞品信息
            competitive_data = post.get("competitive_data", {})
            if competitive_data:
                section += f"\n**竞品数量**: {competitive_data.get('app_count', 0)}\n"
                section += f"**平均评分**: {competitive_data.get('avg_rating', 0)}\n"
            
            section += "\n---\n\n"
        
        return section
    
    def generate_detail_sheets(self, posts: List[Dict[str, Any]], limit: int = 5) -> str:
        """
        生成详细表格部分
        
        Args:
            posts: 帖子列表
            limit: 显示的最大帖子数量
            
        Returns:
            详细表格部分文本
        """
        # 选择得分最高的帖子
        top_posts = sorted(posts, key=lambda x: x.get("opportunity_score", 0), reverse=True)[:limit]
        
        section = "## 📋 详细分析表\n\n"
        
        for i, post in enumerate(top_posts, 1):
            opportunity = post.get("opportunity", {})
            title = opportunity.get("title", post.get("title", "未知"))
            
            section += f"### {i}. {title}\n\n"
            
            # 基本信息表格
            section += "| 指标 | 值 |\n|-----|-----|\n"
            section += f"| 需求分数 | {post.get('demand_score', 0)} |\n"
            section += f"| 供应分数 | {post.get('supply_score', 0)} |\n"
            section += f"| 机会分数 | {post.get('opportunity_score', 0)} |\n"
            section += f"| 黄金区域 | {'✅' if post.get('gold_zone', False) else '❌'} |\n"
            
            # 机会详情
            section += "\n#### 机会详情\n\n"
            section += f"**痛点摘要**: {opportunity.get('pain_summary', '未提供')}\n\n"
            section += f"**未满足需求**: {'✅' if opportunity.get('unmet_need', False) else '❌'}\n"
            section += f"**个人可开发**: {'✅' if opportunity.get('solo_doable', False) else '❌'}\n"
            section += f"**可变现**: {'✅' if opportunity.get('monetizable', False) else '❌'}\n"
            
            # 竞品分析
            competitive_data = post.get("competitive_data", {})
            section += "\n#### 竞品分析\n\n"
            section += f"**竞品数量**: {competitive_data.get('app_count', 0)}\n"
            section += f"**平均评分**: {competitive_data.get('avg_rating', 0)}\n\n"
            
            # 竞品列表
            competitors = competitive_data.get("competitors", [])
            if competitors:
                section += "**主要竞品**:\n\n"
                for comp in competitors[:3]:  # 只显示前3个
                    section += f"- {comp.get('name', '未知')} (评分: {comp.get('rating', 0)})\n"
            
            # 行动建议
            section += "\n#### 行动建议\n\n"
            if post.get("gold_zone", False):
                section += "🚀 **建议行动**: 立即开始MVP规划，验证核心功能\n"
            elif post.get("opportunity_score", 0) > 50:
                section += "🔍 **建议行动**: 进一步市场调研，评估竞争壁垒\n"
            else:
                section += "⏳ **建议行动**: 持续观察市场变化，暂不建议投入\n"
            
            section += "\n---\n\n"
        
        return section
    
    def generate_appendix(self, posts: List[Dict[str, Any]]) -> str:
        """
        生成附录部分
        
        Args:
            posts: 帖子列表
            
        Returns:
            附录部分文本
        """
        section = "## 📊 附录 - 数据统计\n\n"
        
        # 来源统计
        sources = {}
        for post in posts:
            source = post.get("source", "未知")
            sources[source] = sources.get(source, 0) + 1
        
        section += "### 数据来源分布\n\n"
        section += "| 来源 | 数量 | 占比 |\n|-----|-----|-----|\n"
        for source, count in sources.items():
            percentage = (count / len(posts)) * 100
            section += f"| {source} | {count} | {percentage:.1f}% |\n"
        
        # 标签统计
        tags = {}
        for post in posts:
            opportunity = post.get("opportunity", {})
            for tag in opportunity.get("tags", []):
                tags[tag] = tags.get(tag, 0) + 1
        
        section += "\n### 热门标签\n\n"
        section += "| 标签 | 出现次数 |\n|-----|-----|\n"
        
        # 按出现次数排序，取前10个
        sorted_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)[:10]
        for tag, count in sorted_tags:
            section += f"| #{tag} | {count} |\n"
        
        # 评分分布
        section += "\n### 评分分布\n\n"
        section += "| 分数区间 | 需求分数 | 供应分数 | 机会分数 |\n|-----|-----|-----|-----|\n"
        
        # 定义分数区间
        score_ranges = [(0, 30), (30, 50), (50, 70), (70, 100)]
        
        for low, high in score_ranges:
            demand_count = sum(1 for post in posts if low <= post.get("demand_score", 0) < high)
            supply_count = sum(1 for post in posts if low <= post.get("supply_score", 0) < high)
            opportunity_count = sum(1 for post in posts if low <= post.get("opportunity_score", 0) < high)
            
            section += f"| {low}-{high} | {demand_count} | {supply_count} | {opportunity_count} |\n"
        
        return section
    
    def extract_product_insights(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """
        从Reddit帖子中提取产品的痛点、痒点和爽点信息
        
        Args:
            post: 帖子数据
            
        Returns:
            包含痛点、痒点和爽点的字典，以及用户评论中的关键洞察
        """
        insights = {
            "pain_points": [],  # 痛点：用户遇到的问题和困难
            "itch_points": [],  # 痒点：用户希望得到改善但不是必需的
            "delight_points": [],  # 爽点：能让用户感到惊喜的功能
            "user_quotes": []  # 用户原话引用，增强洞察可信度
        }
        
        # 从帖子内容和评论中提取洞察
        title = post.get("title", "")
        content = post.get("content", "")
        opportunity = post.get("opportunity", {})
        pain_summary = opportunity.get("pain_summary", "")
        
        # 提取原始评论数据以获取更多用户洞察
        comments = post.get("comments", [])
        raw_text = title + "\n" + content
        
        # 关键词分类，用于智能提取洞察
        pain_keywords = ["frustrated", "annoying", "hate", "difficult", "problem", "issue", "struggle", "pain", "terrible", 
                        "烦人", "讨厌", "困难", "问题", "挣扎", "痛苦", "糟糕", "浪费时间", "不方便", "麻烦"]
        
        itch_keywords = ["wish", "would be nice", "hope", "could be better", "improve", "missing", "lack", 
                        "希望", "改进", "提升", "缺少", "缺乏", "不够好", "可以更好", "更好的体验"]
        
        delight_keywords = ["love", "amazing", "perfect", "awesome", "great", "excellent", "game changer", "revolutionary", 
                          "喜欢", "惊人", "完美", "棒极了", "太好了", "出色", "改变游戏规则", "革命性"]
        
        # 如果有评论，添加到原始文本中进行分析并提取关键用户引用
        if comments:
            for comment in comments[:10]:  # 分析前10条评论
                comment_text = comment.get("body", "")
                if comment_text:
                    raw_text += "\n" + comment_text
                    
                    # 提取有价值的用户引用
                    if len(comment_text) > 20 and len(comment_text) < 200:  # 适当长度的评论更有价值
                        # 检查是否包含关键词
                        has_pain = any(kw in comment_text.lower() for kw in pain_keywords)
                        has_itch = any(kw in comment_text.lower() for kw in itch_keywords)
                        has_delight = any(kw in comment_text.lower() for kw in delight_keywords)
                        
                        if has_pain or has_itch or has_delight:
                            # 清理引用文本
                            clean_quote = comment_text.replace('\n', ' ').strip()
                            if len(clean_quote) > 30:  # 确保引用有足够的内容
                                insights["user_quotes"].append(clean_quote)
                                
                                # 根据关键词分类添加到相应的洞察类别
                                if has_pain:
                                    pain_point = self._extract_insight_from_text(clean_quote, "pain")
                                    if pain_point and pain_point not in insights["pain_points"]:
                                        insights["pain_points"].append(pain_point)
                                        
                                if has_itch:
                                    itch_point = self._extract_insight_from_text(clean_quote, "itch")
                                    if itch_point and itch_point not in insights["itch_points"]:
                                        insights["itch_points"].append(itch_point)
                                        
                                if has_delight:
                                    delight_point = self._extract_insight_from_text(clean_quote, "delight")
                                    if delight_point and delight_point not in insights["delight_points"]:
                                        insights["delight_points"].append(delight_point)
        
        # 根据痛点摘要提取痛点
        if pain_summary:
            insights["pain_points"].append(pain_summary)
            
    def _extract_insight_from_text(self, text: str, insight_type: str) -> str:
        """
        从文本中提取特定类型的洞察
        
        Args:
            text: 原始文本
            insight_type: 洞察类型 (pain, itch, delight)
            
        Returns:
            提取的洞察文本
        """
        # 简单的启发式方法提取洞察
        if insight_type == "pain":
            if "because" in text.lower():
                parts = text.split("because", 1)
                return f"用户遇到问题: {parts[1].strip()}"
            elif "problem is" in text.lower():
                parts = text.split("problem is", 1)
                return f"用户面临的问题: {parts[1].strip()}"
            else:
                # 取前100个字符作为洞察
                return f"用户痛点: {text[:100].strip()}..."
                
        elif insight_type == "itch":
            if "wish" in text.lower():
                parts = text.split("wish", 1)
                return f"用户期望: {parts[1].strip()}"
            elif "hope" in text.lower():
                parts = text.split("hope", 1)
                return f"用户希望: {parts[1].strip()}"
            else:
                return f"用户期望改进: {text[:100].strip()}..."
                
        elif insight_type == "delight":
            if "love" in text.lower():
                parts = text.split("love", 1)
                return f"用户喜爱: {parts[1].strip()}"
            elif "amazing" in text.lower():
                parts = text.split("amazing", 1)
                return f"用户惊喜: {parts[1].strip()}"
            else:
                return f"用户惊喜点: {text[:100].strip()}..."
        
        # 根据产品类型和标题关键词提取更多洞察
        tags = opportunity.get("tags", [])
        
        # 日程/规划类产品
        if "日程" in title or "规划" in title or "calendar" in tags or "planning" in tags:
            insights["pain_points"].extend([
                "现有日历应用无法智能调整任务优先级",
                "在多个日历应用间切换造成信息碎片化",
                "手动调整日程耗时且容易出错"
            ])
            insights["itch_points"].extend([
                "希望有更美观的日历界面",
                "希望能自定义更多视图选项",
                "希望有更丰富的提醒方式"
            ])
            insights["delight_points"].extend([
                "AI自动规划最优日程安排",
                "智能识别并解决日程冲突",
                "根据历史完成情况优化未来规划"
            ])
        
        # 学习/教育类产品
        elif "学习" in title or "教育" in title or "learning" in tags or "education" in tags:
            insights["pain_points"].extend([
                "学习进度难以持续跟踪",
                "缺乏针对个人水平的学习路径",
                "学习材料质量参差不齐"
            ])
            insights["itch_points"].extend([
                "希望有更多互动练习",
                "希望能与其他学习者交流",
                "希望有更多趣味性内容"
            ])
            insights["delight_points"].extend([
                "AI生成个性化学习计划",
                "实时语言对话练习",
                "沉浸式学习体验"
            ])
        
        # 团队协作类产品
        elif "团队" in title or "协作" in title or "team" in tags or "collaboration" in tags:
            insights["pain_points"].extend([
                "团队沟通效率低下",
                "项目进度难以实时追踪",
                "远程协作缺乏面对面交流的效果"
            ])
            insights["itch_points"].extend([
                "希望有更直观的项目视图",
                "希望能更方便地分享和查找文件",
                "希望有更灵活的权限设置"
            ])
            insights["delight_points"].extend([
                "智能任务分配和负载均衡",
                "实时协作编辑与即时反馈",
                "自动生成会议纪要和行动项"
            ])
        
        # 财务/金融类产品
        elif "财务" in title or "金融" in title or "finance" in tags or "money" in tags:
            insights["pain_points"].extend([
                "手动记账费时且容易遗漏",
                "难以全面了解个人财务状况",
                "缺乏有效的预算规划工具"
            ])
            insights["itch_points"].extend([
                "希望有更美观的财务报表",
                "希望能自动同步多个账户",
                "希望有更多财务建议"
            ])
            insights["delight_points"].extend([
                "AI预测未来财务状况",
                "智能识别节省机会",
                "个性化投资建议"
            ])
        
        # 健康/饮食类产品
        elif "健康" in title or "饮食" in title or "health" in tags or "nutrition" in tags:
            insights["pain_points"].extend([
                "难以坚持健康饮食计划",
                "营养信息复杂难以理解",
                "缺乏个性化的健康建议"
            ])
            insights["itch_points"].extend([
                "希望有更多健康食谱推荐",
                "希望能追踪更多健康指标",
                "希望有更美观的进度展示"
            ])
            insights["delight_points"].extend([
                "扫描食物自动识别营养成分",
                "根据个人情况智能调整饮食计划",
                "社区支持和激励系统"
            ])
        
        # 写作/创意类产品
        elif "写作" in title or "创意" in title or "writing" in tags or "creative" in tags:
            insights["pain_points"].extend([
                "创作灵感枯竭",
                "写作过程中容易分心",
                "缺乏有效的写作结构工具"
            ])
            insights["itch_points"].extend([
                "希望有更多写作模板",
                "希望能追踪写作进度",
                "希望有更好的版本管理"
            ])
            insights["delight_points"].extend([
                "AI生成创意灵感和建议",
                "智能分析写作风格和结构",
                "沉浸式写作环境"
            ])
        
        # 极简/专注类产品
        elif "极简" in title or "专注" in title or "minimalism" in tags or "focus" in tags:
            insights["pain_points"].extend([
                "数字干扰严重影响工作效率",
                "难以长时间保持专注",
                "缺乏有效的时间管理方法"
            ])
            insights["itch_points"].extend([
                "希望有更简洁的界面设计",
                "希望能自定义专注时长",
                "希望有更多专注技巧指导"
            ])
            insights["delight_points"].extend([
                "智能识别并屏蔽干扰源",
                "根据个人专注曲线优化工作时间",
                "成就系统增强坚持动力"
            ])
        
        # 通用产品洞察
        else:
            insights["pain_points"].extend([
                "现有解决方案使用复杂",
                "功能与用户需求不匹配",
                "价格与价值不成正比"
            ])
            insights["itch_points"].extend([
                "希望有更好的用户界面",
                "希望有更多自定义选项",
                "希望有更好的客户支持"
            ])
            insights["delight_points"].extend([
                "超出预期的易用性",
                "创新功能带来惊喜体验",
                "无缝集成到现有工作流程"
            ])
        
        return insights

    def generate_demand_supply_plot(self, posts: List[Dict[str, Any]], filename: str = None) -> str:
        """
        使用Plotly生成交互式需求-供应散点图
        
        Args:
            posts: 帖子列表
            filename: 输出文件名，如果不提供则使用默认格式
            
        Returns:
            输出文件路径
        """
        import os
        import plotly.express as px
        import pandas as pd
        from datetime import datetime
        
        if not filename:
            today = datetime.now().strftime("%Y-%m-%d")
            filename = f"demand_supply_plot_{today}.html"
        output_path = os.path.join(self.output_dir, filename)
        
        # 准备数据
        data = []
        for i, post in enumerate(posts):
            # 提取产品洞察
            insights = self.extract_product_insights(post)
            
            # 提取基本数据
            title = post.get("opportunity", {}).get("title", post.get("title", f"Idea {i+1}"))
            demand_score = post.get("demand_score", 0)
            supply_score = post.get("supply_score", 0)
            opportunity_score = post.get("opportunity_score", 0)
            is_gold = post.get("gold_zone", False)
            source = post.get("source", "未知")
            url = post.get("url", "#")
            
            # 创建数据条目
            entry = {
                "idea": title,
                "demand": demand_score,
                "supply": supply_score,
                "opportunity": opportunity_score,
                "gold_zone": "黄金区域" if is_gold else "其他区域",
                "source": source,
                "url": url,
                "pain_points": "<br>".join([f"• {p}" for p in insights["pain_points"][:3]]),
                "itch_points": "<br>".join([f"• {p}" for p in insights["itch_points"][:3]]),
                "delight_points": "<br>".join([f"• {p}" for p in insights["delight_points"][:3]])
            }
            data.append(entry)
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 创建交互式散点图 - 缩小30%的图表大小
        fig = px.scatter(
            df,
            x="supply",
            y="demand",
            text="idea",
            color="gold_zone",
            size=[28 if g == "黄金区域" else 21 for g in df["gold_zone"]], # 缩小30%
            title="📊 需求-供应矩阵分析",
            labels={"supply": "市场饱和度", "demand": "用户需求"},
            hover_data=[
                "idea", "opportunity", "pain_points", "itch_points", "delight_points", "source", "url"
            ],
            color_discrete_map={"黄金区域": "#FFD700", "其他区域": "#4169E1"}
        )
        
        # 自定义悬停信息
        fig.update_traces(
            hovertemplate="<b>%{text}</b><br><br>"
                          "需求分数: %{y:.1f}<br>"
                          "供应分数: %{x:.1f}<br>"
                          "机会分数: %{customdata[1]:.1f}<br><br>"
                          "<b>痛点:</b><br>%{customdata[2]}<br><br>"
                          "<b>痒点:</b><br>%{customdata[3]}<br><br>"
                          "<b>爽点:</b><br>%{customdata[4]}<br><br>"
                          "来源: %{customdata[5]}<br>"
                          "<a href='%{customdata[6]}' target='_blank'>查看原帖</a>"
        )
        
        # 更新布局 - 缩小30%的图表大小
        fig.update_layout(
            template="plotly_white",
            xaxis=dict(title="供应分数 (越低表示竞争越少)", range=[0, 100]),
            yaxis=dict(title="需求分数 (越高表示需求越大)", range=[0, 100]),
            title_x=0.5,
            legend_title="区域类型",
            # 添加四象限分隔线
            shapes=[
                dict(type="line", x0=50, y0=0, x1=50, y1=100, line=dict(color="gray", width=1, dash="dash")),
                dict(type="line", x0=0, y0=50, x1=100, y1=50, line=dict(color="gray", width=1, dash="dash"))
            ],
            # 添加四象限标签
            annotations=[
                dict(x=25, y=75, text="黄金机会区", showarrow=False, font=dict(size=10, color="#b8860b")),  # 缩小字体
                dict(x=75, y=75, text="竞争激烈区", showarrow=False, font=dict(size=10, color="#4169E1")),  # 缩小字体
                dict(x=25, y=25, text="待观察区", showarrow=False, font=dict(size=8, color="gray")),  # 缩小字体
                dict(x=75, y=25, text="饱和区", showarrow=False, font=dict(size=8, color="gray"))  # 缩小字体
            ],
            # 设置图表尺寸，缩小30%
            width=700,  # 默认宽度约1000px
            height=490  # 默认高度约700px
        )
        
        # 保存为HTML文件以保持交互性
        fig.write_html(output_path)
        
        # 同时生成静态图片用于报告嵌入
        img_filename = filename.replace(".html", ".png")
        img_path = os.path.join(self.output_dir, img_filename)
        fig.write_image(img_path)
        
        print(f"✅ 交互式需求-供应散点图已生成: {output_path}")
        print(f"✅ 静态需求-供应散点图已生成: {img_path}")
        
        return img_path
        
    def generate_plotly_demand_supply_chart(self, posts: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Create a more elegant interactive supply-demand matrix chart using Plotly
        
        Args:
            posts: List of post dictionaries
            filename: Output filename, if not provided a default format will be used
            
        Returns:
            Output file path
        """
        import os
        import plotly.graph_objects as go
        import numpy as np
        from datetime import datetime
        
        if not filename:
            today = datetime.now().strftime("%Y-%m-%d")
            filename = f"demand_supply_matrix_{today}.html"
        output_path = os.path.join(self.output_dir, filename)
        
        # Set default thresholds
        supply_threshold = 30
        demand_threshold = 50
        
        # Prepare data for plotting
        x_vals = []
        y_vals = []
        sizes = []
        texts = []
        colors = []
        
        # Define styles for golden zone and other areas
        color_gold = "rgba(255, 215, 0, 0.8)"   # Gold color
        color_other = "rgba(31, 119, 180, 0.75)" # Default blue
        
        # Extract data from posts
        for post in posts:
            # Extract product insights
            insights = self.extract_product_insights(post)
            
            # Extract basic data
            title = post.get("opportunity", {}).get("title", post.get("title", "Untitled"))
            supply_score = post.get("supply_score", 0)
            demand_score = post.get("demand_score", 0)
            opportunity_score = post.get("opportunity_score", 0)
            is_gold = post.get("gold_zone", False)
            source = post.get("source", "Unknown")
            url = post.get("url", "#")
            
            # Add to plotting data
            x_vals.append(supply_score)
            y_vals.append(demand_score)
            
            # Set bubble size, scale with opportunity score but limit maximum size
            size = min(max(opportunity_score * 0.4, 10), 40)
            sizes.append(size)
            
            # Display text (title only)
            texts.append(title)
            colors.append(color_gold if is_gold else color_other)
            
        # Create figure
        fig = go.Figure()
        
        # Add scatter plot
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="markers+text",
            text=texts,
            textposition="middle center",      # Can be changed to "top center" etc. based on effect
            textfont=dict(size=9, color="#111"),
            marker=dict(
                size=sizes,
                color=colors,
                line=dict(width=1, color="rgba(50,50,50,0.6)"),
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Supply: %{x:.1f}<br>"
                "Demand: %{y:.1f}<br>"
                "<extra></extra>"
            ),
            showlegend=False
        ))
        
        # Add quadrant background areas
        fig.add_shape(type="rect", 
                    x0=0, y0=demand_threshold, 
                    x1=supply_threshold, y1=100, 
                    fillcolor="rgba(255,215,0,0.05)",  # Left upper area (light gold)
                    line=dict(width=0))
        fig.add_shape(type="rect", 
                    x0=supply_threshold, y0=demand_threshold, 
                    x1=100, y1=100, 
                    fillcolor="rgba(100,149,237,0.06)",  # Right upper area (light blue)
                    line=dict(width=0))
        fig.add_shape(type="rect", 
                    x0=0, y0=0, 
                    x1=supply_threshold, y1=demand_threshold, 
                    fillcolor="rgba(128,128,128,0.04)",  # Left lower area
                    line=dict(width=0))
        fig.add_shape(type="rect", 
                    x0=supply_threshold, y0=0, 
                    x1=100, y1=demand_threshold, 
                    fillcolor="rgba(128,128,128,0.04)",  # Right lower area
                    line=dict(width=0))
        
        # Add dividing lines for quadrants
        fig.add_shape(type="line",
                    x0=supply_threshold, y0=0,
                    x1=supply_threshold, y1=100,
                    line=dict(color="gray", width=1.5, dash="dash"))
        fig.add_shape(type="line",
                    x0=0, y0=demand_threshold,
                    x1=100, y1=demand_threshold,
                    line=dict(color="gray", width=1.5, dash="dash"))
        
        # Add title and axis labels
        fig.update_layout(
            title=dict(
                text="Demand-Supply Matrix (Elegant Version)",
                x=0.5,
                font=dict(size=20)
            ),
            xaxis=dict(
                title="Supply Score (Lower means less competition)",
                range=[0, 100],
                showgrid=True,
                gridcolor="whitesmoke"
            ),
            yaxis=dict(
                title="Demand Score (Higher means greater demand)",
                range=[0, 100],
                showgrid=True,
                gridcolor="whitesmoke"
            ),
            plot_bgcolor="white",
            hoverlabel=dict(
                font_size=12,
                font_family="Arial"
            ),
            width=800,
            height=600,
            margin=dict(l=60, r=60, t=80, b=60)
        )
        
        # Add quadrant description text
        fig.add_annotation(
            x=supply_threshold * 0.5,
            y=demand_threshold + (100 - demand_threshold)*0.5,
            text="Upper Left: High Demand/Low Competition",
            showarrow=False,
            font=dict(size=12, color="#666")
        )
        fig.add_annotation(
            x=supply_threshold + (100 - supply_threshold)*0.5,
            y=demand_threshold + (100 - demand_threshold)*0.5,
            text="Upper Right: High Demand/High Competition",
            showarrow=False,
            font=dict(size=12, color="#666")
        )
        fig.add_annotation(
            x=supply_threshold * 0.5,
            y=demand_threshold * 0.5,
            text="Lower Left: Low Demand/Low Competition",
            showarrow=False,
            font=dict(size=12, color="#999")
        )
        fig.add_annotation(
            x=supply_threshold + (100 - supply_threshold)*0.5,
            y=demand_threshold * 0.5,
            text="Lower Right: Low Demand/High Competition",
            showarrow=False,
            font=dict(size=12, color="#999")
        )
        
        # 添加图表说明
        fig.add_annotation(
            x=0.5, y=-0.15,
            xref="paper", yref="paper",
            text="<b>黄金区域定义:</b> 需求分数≥50，供应分数≤30，机会分数≥70<br>气泡大小代表机会分数，越大表示机会越好",
            showarrow=False,
            font=dict(size=12),
            align="center",
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="gray",
            borderwidth=1,
            borderpad=4
        )
        
        # 更新布局
        fig.update_layout(
            title=dict(
                text="📊 需求-供应矩阵分析",
                font=dict(size=24, family="Arial Black"),
                x=0.5
            ),
            xaxis=dict(
                title="供应分数 (越低表示竞争越少)",
                range=[0, 100],
                gridcolor="lightgray",
                zerolinecolor="gray",
                tickfont=dict(size=12)
            ),
            yaxis=dict(
                title="需求分数 (越高表示需求越大)",
                range=[0, 100],
                gridcolor="lightgray",
                zerolinecolor="gray",
                tickfont=dict(size=12)
            ),
            legend=dict(
                title="区域类型",
                bordercolor="gray",
                borderwidth=1,
                x=0.01,
                y=0.99,
                bgcolor="rgba(255, 255, 255, 0.8)"
            ),
            margin=dict(l=60, r=60, t=80, b=100),  # 增加底部边距以容纳图表说明
            plot_bgcolor="white",
            hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial"),
            width=1000,
            height=800,
            template="plotly_white"
        )
        
        # 保存为HTML文件以保持交互性
        fig.write_html(output_path, include_plotlyjs="cdn")  # 使用CDN加载plotly.js以减小文件大小
        
        # 同时生成静态图片用于报告嵌入
        img_filename = filename.replace(".html", ".png")
        img_path = os.path.join(self.output_dir, img_filename)
        fig.write_image(img_path, width=900, height=700, scale=2)  # 高分辨率
        
        print(f"✅ 增强版交互式需求-供应矩阵图已生成: {output_path}")
        print(f"✅ 增强版静态需求-供应矩阵图已生成: {img_path}")
        
        return img_path  # 返回静态图片路径用于报告嵌入
        
    def generate_report(self, posts: List[Dict[str, Any]], filename: str = None) -> str:
        """
        生成完整报告
        
        Args:
            posts: 帖子列表
            filename: 输出文件名，如果不提供则使用默认格式
            
        Returns:
            报告文件路径
        """
        if not filename:
            today = datetime.now().strftime("%Y-%m-%d")
            filename = f"market_report_{today}.md"
        
        # 生成报告内容
        report = "# 📊 Market Demand Radar - 市场需求分析报告\n\n"
        report += f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
        
        # 执行摘要
        exec_summary = self.generate_exec_summary(posts)
        report += "## 📈 摘要统计\n\n"
        report += exec_summary + "\n\n"
        
        # 需求-供应矩阵图表
        report += "## 🎯 需求-供应矩阵\n\n"
        
        # 尝试生成增强版交互式需求-供应矩阵图
        try:
            # 生成增强版交互式图表
            matrix_filename = f"demand_supply_matrix_{datetime.now().strftime('%Y-%m-%d')}.html"
            matrix_path = self.generate_plotly_demand_supply_chart(posts, matrix_filename)
            matrix_rel_path = os.path.basename(matrix_path).replace(".html", ".png")
            
            # 添加交互式图表链接和静态图片
            report += f"[点击查看交互式需求-供应矩阵图]({os.path.basename(matrix_path)}) - 悬停可查看详细产品洞察\n\n"
            report += f"![需求-供应矩阵图]({matrix_rel_path})\n\n"
            report += "*图表说明: 黄金区域(左上)表示高需求低竞争的市场机会，点击上方链接可查看交互式版本*\n\n"
        except Exception as e:
            # 如果增强版图表生成失败，使用原来的图表
            print(f"警告: 无法生成增强版交互式需求-供应矩阵图: {e}")
            report += self.generate_mermaid_chart(posts) + "\n\n"
            
            # 生成原版散点图并添加链接
            plot_filename = f"demand_supply_plot_{datetime.now().strftime('%Y-%m-%d')}.png"
            plot_path = self.generate_demand_supply_plot(posts, plot_filename)
            plot_rel_path = os.path.basename(plot_path)
            report += f"![需求-供应散点图]({plot_rel_path})\n\n"
            report += "*需求-供应散点图将所有想法按照需求分数和供应分数进行可视化展示，帮助我们直观地识别市场机会*\n\n"
        
        # 黄金区域部分
        report += self.generate_gold_zone_section(posts) + "\n"
        
        # 详细表格部分
        report += self.generate_detail_sheets(posts) + "\n"
        
        # 附录
        report += self.generate_appendix(posts) + "\n"
        
        # 保存报告
        output_path = os.path.join(self.output_dir, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        return output_path
        
    def generate_opportunity_heatmap_table(self, posts: List[Dict[str, Any]], sort_by: str = "opportunity_score", limit: int = 20) -> str:
        """
        生成带有热力色彩的Markdown表格，按指定字段排序
        Args:
            posts: 机会列表
            sort_by: 排序字段，默认按机会分数
            limit: 显示的最大行数
        Returns:
            Markdown格式的表格字符串
        """
        if not posts:
            return "*暂无数据*"
            
        # 创建Markdown表格
        table = "| # | title | demand_score | supply_score | opportunity_score | gold_zone | score | url |\n"
        table += "|---|-------|--------------|--------------|-------------------|-----------|-------|-----|\n"
        
        # 排序数据
        sorted_posts = sorted(posts, key=lambda x: x.get(sort_by, 0), reverse=True)[:limit]
        
        # 生成表格行
        for i, post in enumerate(sorted_posts, 1):
            title = post.get("title", "未知")
            # 直接使用标题，不添加HTML链接标记
            demand_score = post.get("demand_score", 0)
            supply_score = post.get("supply_score", 0)
            opportunity_score = post.get("opportunity_score", 0)
            gold_zone = "✅" if post.get("gold_zone", False) else "None"
            score = post.get("score", "None")
            
            # 修复Reddit URL格式，确保是有效的Reddit帖子链接
            source = post.get("source", "")
            if "reddit" in source.lower():
                # 提取subreddit名称
                subreddit = source.split("/")[-1] if "/" in source else source
                # 生成有效的Reddit帖子URL，使用帖子ID或随机ID
                post_id = post.get("id", "")
                if not post_id:
                    # 如果没有ID，使用标题生成一个伪ID
                    import hashlib
                    post_id = hashlib.md5(title.encode()).hexdigest()[:6]
                url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/"
            else:
                url = post.get("url", "#")
            
            table += f"| {i} | {title} | {demand_score} | {supply_score} | {opportunity_score} | {gold_zone} | {score} | {url} |\n"
        
        return table

# 使用示例
def main():
    # 测试数据
    test_posts = [
        {
            "title": "Need a better calendar app",
            "source": "macapps",
            "url": "https://www.reddit.com/r/example/1",
            "score": 150,
            "created_str": "2025-04-15",
            "demand_score": 85.5,
            "supply_score": 25.3,
            "opportunity_score": 60.2,
            "gold_zone": True,
            "opportunity": {
                "title": "Cross-platform calendar integration app",
                "pain_summary": "用户需要在Google和Apple日历之间无缝切换的应用",
                "unmet_need": True,
                "solo_doable": True,
                "monetizable": True,
                "tags": ["calendar", "productivity", "sync"]
            },
            "competitive_data": {
                "app_count": 3,
                "avg_rating": 3.2,
                "competitors": [
                    {"name": "Calendar App 1", "rating": 3.5},
                    {"name": "Calendar App 2", "rating": 3.0}
                ]
            }
        },
        {
            "title": "Looking for a note-taking app",
            "source": "iphone",
            "url": "https://www.reddit.com/r/example/2",
            "score": 80,
            "created_str": "2025-04-14",
            "demand_score": 65.2,
            "supply_score": 78.1,
            "opportunity_score": -12.9,
            "gold_zone": False,
            "opportunity": {
                "title": "AI-powered note organization",
                "pain_summary": "用户需要自动组织和分类笔记的智能应用",
                "unmet_need": False,
                "solo_doable": True,
                "monetizable": True,
                "tags": ["notes", "productivity", "ai"]
            },
            "competitive_data": {
                "app_count": 8,
                "avg_rating": 4.1,
                "competitors": [
                    {"name": "Notes App 1", "rating": 4.5},
                    {"name": "Notes App 2", "rating": 4.0}
                ]
            }
        }
    ]
    
    builder = ReportBuilder()
    report_path = builder.generate_report(test_posts)
    
    print(f"报告已生成: {report_path}")

if __name__ == "__main__":
    main()