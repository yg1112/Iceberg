#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM Extractor Module

根据PRD v2要求实现的LLM提取器模块
使用OpenAI GPT-3.5-turbo模型分析帖子并提取结构化的产品机会信息
"""

import json
import os
import asyncio
from typing import Dict, Any, List, Optional
import openai
from datetime import datetime

# 加载OpenAI API密钥
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY is not set. Please export it in your shell.")

# 设置OpenAI客户端
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# 备用模型，当主模型失败时使用
PRIMARY_MODEL = "gpt-3.5-turbo"
FALLBACK_MODEL = "gpt-3.5-turbo-instruct"

# 批处理大小
BATCH_SIZE = 10

class LLMExtractor:
    """
    LLM提取器
    使用OpenAI GPT模型分析帖子并提取结构化的产品机会信息
    """
    
    def __init__(self, model: str = PRIMARY_MODEL, prompt_path: str = None):
        """
        初始化LLM提取器
        
        Args:
            model: 使用的OpenAI模型名称
            prompt_path: 提示词文件路径，如果不提供则使用默认路径
        """
        self.model = model
        self.client = openai_client
        
        # 加载提示词模板
        if prompt_path is None:
            prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                      "prompts", "opportunity_v2.txt")
        
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()
    
    async def extract_opportunity(self, post_text: str, source: str, url: str) -> Dict[str, Any]:
        """
        从帖子中提取产品机会信息
        
        Args:
            post_text: 帖子文本内容
            source: 来源平台（如Reddit, Product Hunt等）
            url: 帖子URL
            
        Returns:
            结构化的产品机会信息，包含更丰富的用户需求洞察
        """
        # 填充提示词模板
        prompt = self.prompt_template.replace("{{post_text}}", post_text)
        prompt = prompt.replace("{{source}}", source)
        prompt = prompt.replace("{{url}}", url)
        
        try:
            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )
            
            result = response.choices[0].message.content.strip()
            
            # 解析JSON结果
            try:
                opportunity = json.loads(result)
                return opportunity
            except json.JSONDecodeError:
                # 如果返回的不是有效JSON，尝试提取JSON部分
                json_start = result.find("{")
                json_end = result.rfind("}")
                if json_start != -1 and json_end != -1:
                    json_str = result[json_start:json_end+1]
                    return json.loads(json_str)
                else:
                    raise ValueError("无法从LLM响应中提取有效JSON")
                
        except Exception as e:
            print(f"⚠️ 使用{self.model}提取机会时出错: {str(e)}")
            
            # 如果使用主模型失败，尝试使用备用模型
            if self.model == PRIMARY_MODEL:
                print(f"尝试使用备用模型{FALLBACK_MODEL}...")
                backup_extractor = LLMExtractor(model=FALLBACK_MODEL)
                return await backup_extractor.extract_opportunity(post_text, source, url)
            else:
                # 返回空结果
                return {
                    "title": "提取失败",
                    "pain_summary": "无法从帖子中提取产品机会信息",
                    "unmet_need": False,
                    "solo_doable": False,
                    "monetizable": False,
                    "tags": ["extraction_failed"]
                }
    
    async def batch_extract(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量处理帖子并提取产品机会信息
        
        Args:
            posts: 帖子列表，每个帖子应包含title, content, source, url字段
            
        Returns:
            带有提取结果的帖子列表
        """
        results = []
        
        # 分批处理以避免API限制
        for i in range(0, len(posts), BATCH_SIZE):
            batch = posts[i:i+BATCH_SIZE]
            tasks = []
            
            for post in batch:
                # 组合标题和内容作为分析文本
                post_text = post.get("title", "")
                if post.get("content"):
                    post_text += "\n" + post["content"]
                
                source = post.get("source", "unknown")
                url = post.get("url", "")
                
                # 创建异步任务
                task = asyncio.create_task(
                    self.extract_opportunity(post_text, source, url)
                )
                tasks.append((post, task))
            
            # 等待所有任务完成
            for post, task in tasks:
                try:
                    opportunity = await task
                    post["opportunity"] = opportunity
                    results.append(post)
                except Exception as e:
                    print(f"处理帖子时出错: {str(e)}")
                    post["opportunity"] = {
                        "title": "处理错误",
                        "pain_summary": f"处理帖子时出错: {str(e)}",
                        "unmet_need": False,
                        "solo_doable": False,
                        "monetizable": False,
                        "tags": ["processing_error"]
                    }
                    results.append(post)
        
        return results

# 使用示例
async def main():
    # 测试数据
    test_post = {
        "title": "I wish there was a better calendar app that integrates with both Google and Apple calendars",
        "content": "I'm constantly switching between my work Google calendar and personal Apple calendar. It's frustrating that there's no good app that shows both seamlessly and allows easy event creation in either system.",
        "source": "reddit",
        "url": "https://www.reddit.com/r/macapps/comments/example"
    }
    
    extractor = LLMExtractor()
    opportunity = await extractor.extract_opportunity(
        test_post["title"] + "\n" + test_post["content"],
        test_post["source"],
        test_post["url"]
    )
    
    print(json.dumps(opportunity, indent=2))

if __name__ == "__main__":
    asyncio.run(main())