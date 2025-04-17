# idea_radar.py (Fixed for openai>=1.0.0 API)

import praw
from datetime import datetime
import os
import openai

# === Reddit Credentials ===
REDDIT_CLIENT_ID = "VUQT-RvwOD3W-6s0R3qxGw"
REDDIT_CLIENT_SECRET = "5TW22rlhHzR9VUl7jBnKcoXoIYPhlg"
REDDIT_USER_AGENT = "ideaRadar/0.1 by Repeat_Admirable"
REDDIT_USERNAME = "Repeat_Admirable"
REDDIT_PASSWORD = "RedditPass@01"

# === OpenAI Key ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY is not set. Please export it in your shell or hardcode for local test.")

openai.api_key = OPENAI_API_KEY

# === Search Scope ===
KEYWORDS = [
    "i wish",
    "is there an app",
    "looking for an app",
    "need a chrome extension",
    "frustrating",
    "missing feature",
    "why isn't there"
]
SUBREDDITS = ["macapps", "iphone", "chrome_extensions"]

print("🔐 Authenticating Reddit account...")
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
    username=REDDIT_USERNAME,
    password=REDDIT_PASSWORD
)

try:
    me = reddit.user.me()
    print(f"✅ Authenticated as: u/{me}")
except Exception as e:
    print("❌ Reddit authentication failed:", e)
    exit(1)

def analyze_post_with_gpt(title, subreddit, url):
    prompt = f"""
Reddit Post Title:
"{title}"
Subreddit: {subreddit}
URL: {url}

Please analyze the post. Return JSON with the following fields:
- unmet_need: true/false
- pain_summary: short summary of the pain point
- alternatives: are there known tools solving this?
- solo_doable: true/false — can a solo dev build this?
- monetizable: true/false — would users likely pay?
- tags: a few keywords like 'macOS', 'productivity', 'calendar', etc.
"""
    try:
        # 使用新版OpenAI API格式
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ GPT分析失败: {str(e)}")
        return None

def save_to_markdown(ideas, filename=None, competitor_data=None):
    # 新增价值评估维度说明
    VALUE_MATRIX_DESC = """
## 商业价值评估矩阵
- 🛠 技术可行性：综合开发技能匹配度、API依赖复杂度
- 🌐 市场饱和度：考量竞品数量、市场增长率
- 💰 变现潜力：LTV与获客成本差值"""
    if not filename:
        today = datetime.today().strftime("%Y-%m-%d")
        filename = f"top_ideas_{today}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write("# 📌 Top Reddit App/Extension Ideas for Solo Dev\n\n")
        for idx, idea in enumerate(ideas, 1):
            f.write(f"{idx}. [{idea['title']}]({idea['url']})  👍 {idea['score']} points\n")
            f.write(f"    Subreddit: r/{idea['subreddit']} | Posted on: {idea['created_str']}\n\n")
            if idea.get("gpt_analysis"):
                f.write("**GPT Analysis**\n")
                f.write(f"```json\n{idea['gpt_analysis']}\n```\n")
                f.write(f"**商业评估**: {idea.get('value_insight', '待分析')}\n\n")
            else:
                f.write("_❌ GPT analysis failed_\n\n")

    print(f"✅ Results saved to: {filename}")
    
    # 添加竞品对比附录
    if competitor_data:
        with open(filename, "a", encoding="utf-8") as f:
            f.write("\n## 🔍 竞品流量对比\n")
            for domain, stats in competitor_data.items():
                f.write(f"### {domain}\n")
                if stats is not None:
                    f.write(f"- 全球排名: {stats.get('global_rank', 'N/A')}\n")
                    f.write(f"- 平均访问时长: {stats.get('avg_visit_duration', 0):.1f}分钟\n")
                    f.write(f"- 页面/访问: {stats.get('pages_per_visit', 0):.1f}\n\n")
                else:
                    f.write("- 数据获取失败，请检查API密钥或网络连接\n\n")

def search_ideas():
    # 导入依赖模块
    import numpy as np
    from competitive_analysis import CompetitorAnalyzer
    from business_value import ValueAssessor
    
    results = []

    for sub in SUBREDDITS:
        subreddit = reddit.subreddit(sub)
        for keyword in KEYWORDS:
            print(f"🔍 Searching '{keyword}' in r/{sub}...")
            for post in subreddit.search(keyword, sort="top", time_filter="month", limit=20):
                if not post.stickied and len(post.title) < 200:
                    result = {
                        "subreddit": sub,
                        "title": post.title,
                        "score": post.score,
                        "url": post.url,
                        "created": datetime.fromtimestamp(post.created_utc),
                        "created_str": datetime.fromtimestamp(post.created_utc).strftime("%Y-%m-%d")
                    }
                    results.append(result)

    # Deduplicate
    seen = set()
    deduped = []
    for r in results:
        if r["title"] not in seen:
            seen.add(r["title"])
            deduped.append(r)

    # Sort with freshness weight
    def weighted_score(r):
        age_days = (datetime.utcnow() - r["created"]).days
        # 增强版算法：指数衰减+对数转换
        time_decay = np.exp(-age_days/45)  # 45天衰减周期
        engagement_weight = np.log1p(r["score"]) * 0.8  # 对数转换防刷赞
        return engagement_weight * time_decay * \
               (1 + 0.3*(r["subreddit"] in {"macapps", "chrome_extensions"}))

    # 新增数据清洗
    filtered = [r for r in deduped 
               if r["score"] >= 15  # 最低点赞阈值
               and (datetime.utcnow() - r["created"]).days <= 90  # 三个月内
               and len(r["title"].split()) >= 5]  # 排除简单提问

    top = sorted(filtered, key=weighted_score, reverse=True)[:10]

    for r in top:
        print(f"\n🧠 GPT analyzing: {r['title']}")
        analysis = analyze_post_with_gpt(r['title'], r['subreddit'], r['url'])
        r['gpt_analysis'] = analysis

    # 新增商业价值评估
    assessor = ValueAssessor()
    top = assessor.enrich_with_value_analysis(top)

    # 生成竞品对比报告
    competitor_report = {
        'similarweb': CompetitorAnalyzer('similarweb.com').get_traffic_stats(),
        'explodingtopics': CompetitorAnalyzer('explodingtopics.com').get_traffic_stats()
    }

    save_to_markdown(top, competitor_data=competitor_report)

if __name__ == "__main__":
    search_ideas()
