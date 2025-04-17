#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
全局配置文件 

市场需求雷达的全局配置项，用于集中管理所有模块的关键配置。
"""

import os
from typing import Dict, List, Any, Optional

# 基础配置
PROJECT_NAME = "Market Demand Radar"
VERSION = "2.0.0"
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")

# 确保必要的目录存在
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# API密钥（优先从环境变量获取）
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.environ.get("REDDIT_USER_AGENT", f"{PROJECT_NAME}/{VERSION}")
PRODUCTHUNT_API_KEY = os.environ.get("PRODUCTHUNT_API_KEY")

# Reddit配置
DEFAULT_SUBREDDITS = ["macapps", "iphone", "chrome_extensions"]
DEFAULT_POST_LIMIT = 25

# LLM配置
LLM_MODEL = "gpt-3.5-turbo"
LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS = 500
LLM_PROMPT_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts/opportunity_v2.txt")

# 评分引擎配置
SCORING_CONFIG = {
    "demand_score_formula": {
        "post_score_weight": 10,  # log10(post_score+1) * weight
        "sentiment_weight": 10,   # sentiment * weight
        "velocity_weight": 20     # velocity * weight
    },
    "supply_score_formula": {
        "app_count_weight": 5,    # app_count * weight
        "avg_rating_weight": 2    # avg_rating * weight
    },
    "gold_zone_criteria": {
        "min_opportunity_score": 70,
        "min_demand_score": 50,
        "max_supply_score": 30
    }
}

# 应用商店配置
APPSTORE_APP_IDS = {
    "productivity": [
        {"id": "1232780281", "name": "Notion"},
        {"id": "310633997", "name": "Evernote"},
        {"id": "1274495053", "name": "Things 3"}
    ],
    "calendar": [
        {"id": "1160481993", "name": "Fantastical"},
        {"id": "975937182", "name": "Calendars 5"}
    ],
    "browser": [
        {"id": "1077036385", "name": "Brave Browser"}
    ]
}

# 抓取器通用配置
SCRAPER_CONFIG = {
    "retry_attempts": 3,
    "retry_delay_base": 2,  # 指数退避的基础延迟（秒）
    "timeout": 30,          # 请求超时时间（秒）
    "rate_limit": {
        "requests_per_minute": 20
    },
    "user_agent_list": [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0"
    ]
}

# 报告配置
REPORT_CONFIG = {
    "max_exec_summary_chars": 120,
    "max_top_opportunities": 10,
    "report_name_template": "market_report_{date}.md",
    "include_mermaid_charts": True
}

# 仪表板配置
DASHBOARD_CONFIG = {
    "default_filters": {
        "date_range": "Last 30 days",
        "min_demand": 50,
        "show_gold_only": True
    },
    "performance": {
        "max_records_without_warning": 1000,
        "query_timeout_ms": 300
    }
}

# 电子邮件摘要配置
EMAIL_CONFIG = {
    "send_day": "Monday",
    "send_hour": 8,
    "send_timezone": "UTC",
    "sender_email": os.environ.get("EMAIL_SENDER"),
    "smtp_server": os.environ.get("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.environ.get("SMTP_PORT", "587")),
    "smtp_username": os.environ.get("SMTP_USERNAME"),
    "smtp_password": os.environ.get("SMTP_PASSWORD"),
    "subject_template": "Market Demand Radar - Weekly Digest {date}",
    "recipient_list": []  # 在生产环境中填充
}

def get_config() -> Dict[str, Any]:
    """
    获取完整的配置字典
    
    Returns:
        包含所有配置项的字典
    """
    return {
        "project_name": PROJECT_NAME,
        "version": VERSION,
        "cache_dir": CACHE_DIR,
        "reports_dir": REPORTS_DIR,
        "api_keys": {
            "openai": OPENAI_API_KEY,
            "reddit_client_id": REDDIT_CLIENT_ID,
            "reddit_client_secret": REDDIT_CLIENT_SECRET,
            "producthunt": PRODUCTHUNT_API_KEY
        },
        "reddit": {
            "default_subreddits": DEFAULT_SUBREDDITS,
            "default_post_limit": DEFAULT_POST_LIMIT,
            "user_agent": REDDIT_USER_AGENT
        },
        "llm": {
            "model": LLM_MODEL,
            "temperature": LLM_TEMPERATURE,
            "max_tokens": LLM_MAX_TOKENS,
            "prompt_template_path": LLM_PROMPT_TEMPLATE_PATH
        },
        "scoring": SCORING_CONFIG,
        "appstore": {
            "app_ids": APPSTORE_APP_IDS
        },
        "scraper": SCRAPER_CONFIG,
        "report": REPORT_CONFIG,
        "dashboard": DASHBOARD_CONFIG,
        "email": EMAIL_CONFIG
    }

def validate_config() -> List[str]:
    """
    验证配置是否完整和有效
    
    Returns:
        问题列表，如果没有问题则为空列表
    """
    issues = []
    
    # 检查必需的API密钥
    if not OPENAI_API_KEY:
        issues.append("Missing OPENAI_API_KEY environment variable")
    
    # 检查必需的目录
    if not os.path.exists(CACHE_DIR):
        issues.append(f"Cache directory does not exist: {CACHE_DIR}")
    if not os.path.exists(REPORTS_DIR):
        issues.append(f"Reports directory does not exist: {REPORTS_DIR}")
    
    # 检查LLM提示词模板
    if not os.path.exists(LLM_PROMPT_TEMPLATE_PATH):
        issues.append(f"LLM prompt template file not found: {LLM_PROMPT_TEMPLATE_PATH}")
    
    return issues

def get_api_status() -> Dict[str, bool]:
    """
    获取各API的可用状态
    
    Returns:
        包含各API可用状态的字典
    """
    return {
        "openai": bool(OPENAI_API_KEY),
        "reddit": bool(REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET),
        "producthunt": bool(PRODUCTHUNT_API_KEY)
    }

if __name__ == "__main__":
    # 如果直接运行此文件，则执行配置验证并打印结果
    issues = validate_config()
    if issues:
        print("Configuration issues found:")
        for issue in issues:
            print(f"- {issue}")
    else:
        print("Configuration is valid.")
    
    print("\nAPI status:")
    for api, available in get_api_status().items():
        status = "Available" if available else "Not configured"
        print(f"- {api}: {status}")
    
    # 打印配置概要
    config = get_config()
    print("\nConfiguration summary:")
    print(f"- Project: {config['project_name']} v{config['version']}")
    print(f"- Default subreddits: {', '.join(config['reddit']['default_subreddits'])}")
    print(f"- LLM model: {config['llm']['model']}")
    print(f"- Gold zone criteria: Opportunity ≥ {config['scoring']['gold_zone_criteria']['min_opportunity_score']}, " +
          f"Demand ≥ {config['scoring']['gold_zone_criteria']['min_demand_score']}, " +
          f"Supply ≤ {config['scoring']['gold_zone_criteria']['max_supply_score']}") 