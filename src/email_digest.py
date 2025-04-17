#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Email Digest Module

根据PRD v2要求实现的邮件摘要模块
使用Buttondown API发送每周市场机会摘要邮件
"""

import os
import json
import httpx
from datetime import datetime
from typing import Dict, Any, List, Optional

# 导入项目模块
from src.scoring import ScoringEngine
from src.report import ReportBuilder

# Buttondown API配置
BUTTONDOWN_API_BASE = "https://api.buttondown.email/v1"
BUTTONDOWN_API_KEY = os.getenv("BUTTONDOWN_API_KEY")

class EmailDigest:
    """
    邮件摘要模块
    使用Buttondown API发送每周市场机会摘要邮件
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化邮件摘要模块
        
        Args:
            api_key: Buttondown API密钥，如果不提供则使用环境变量
        """
        self.api_key = api_key or BUTTONDOWN_API_KEY
        
        if not self.api_key:
            raise ValueError("❌ BUTTONDOWN_API_KEY is not set. Please export it in your shell.")
        
        self.headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def send_email(self, subject: str, body: str, email_type: str = "newsletter") -> Dict[str, Any]:
        """
        发送邮件
        
        Args:
            subject: 邮件主题
            body: 邮件正文（Markdown格式）
            email_type: 邮件类型 (newsletter, draft)
            
        Returns:
            API响应
        """
        url = f"{BUTTONDOWN_API_BASE}/emails"
        
        payload = {
            "subject": subject,
            "body": body,
            "type": email_type
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
    
    def generate_email_content(self, posts: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        生成邮件内容
        
        Args:
            posts: 帖子列表
            
        Returns:
            包含主题和正文的字典
        """
        # 使用ReportBuilder生成执行摘要
        report_builder = ReportBuilder()
        exec_summary = report_builder.generate_exec_summary(posts)
        
        # 获取黄金区域帖子
        scorer = ScoringEngine()
        gold_zone_posts = scorer.get_gold_zone_posts(posts, limit=5)
        
        # 生成邮件主题
        today = datetime.now().strftime("%Y-%m-%d")
        subject = f"Market Demand Radar - 每周机会摘要 ({today})"
        
        # 生成邮件正文
        body = f"# 📊 Market Demand Radar - 每周机会摘要\n\n"
        body += f"*生成时间: {today}*\n\n"
        
        # 添加执行摘要
        body += "## 📈 本周摘要\n\n"
        body += exec_summary + "\n\n"
        
        # 添加Top 5机会
        body += "## 🥇 本周Top 5机会\n\n"
        
        if gold_zone_posts:
            for i, post in enumerate(gold_zone_posts, 1):
                opportunity = post.get("opportunity", {})
                title = opportunity.get("title", post.get("title", "未知"))
                pain_summary = opportunity.get("pain_summary", "")
                
                body += f"### {i}. {title}\n\n"
                body += f"- **机会分数**: {post.get('opportunity_score', 0)}\n"
                
                if pain_summary:
                    body += f"- **痛点摘要**: {pain_summary}\n"
                
                # 添加标签
                tags = opportunity.get("tags", [])
                if tags:
                    body += "- **标签**: " + ", ".join([f"#{tag}" for tag in tags]) + "\n"
                
                body += "\n"
        else:
            body += "*本周未发现黄金区域机会*\n\n"
        
        # 添加CTA按钮
        body += "## 🚀 开始行动\n\n"
        body += "发现感兴趣的机会？点击下方按钮开始构建！\n\n"
        body += "[开始构建](https://example.com/start-building)\n\n"
        
        # 添加页脚
        body += "---\n\n"
        body += "*此邮件由Market Demand Radar自动生成。如需退订，请点击邮件底部的退订链接。*\n"
        
        return {
            "subject": subject,
            "body": body
        }
    
    async def send_weekly_digest(self, posts: List[Dict[str, Any]], send_as_draft: bool = False) -> Dict[str, Any]:
        """
        发送每周摘要邮件
        
        Args:
            posts: 帖子列表
            send_as_draft: 是否作为草稿发送
            
        Returns:
            API响应
        """
        # 生成邮件内容
        email_content = self.generate_email_content(posts)
        
        # 发送邮件
        email_type = "draft" if send_as_draft else "newsletter"
        response = await self.send_email(
            subject=email_content["subject"],
            body=email_content["body"],
            email_type=email_type
        )
        
        return response

# 使用示例
async def main():
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
            }
        }
    ]
    
    # 初始化EmailDigest
    # 注意：需要设置BUTTONDOWN_API_KEY环境变量
    try:
        digest = EmailDigest()
        
        # 生成邮件内容但不发送
        email_content = digest.generate_email_content(test_posts)
        print(f"邮件主题: {email_content['subject']}")
        print(f"邮件正文预览:\n{email_content['body'][:200]}...")
        
        # 如果设置了API密钥，可以尝试发送草稿
        if BUTTONDOWN_API_KEY:
            print("尝试发送草稿...")
            response = await digest.send_weekly_digest(test_posts, send_as_draft=True)
            print(f"API响应: {response}")
    except Exception as e:
        print(f"发送邮件摘要时出错: {str(e)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())