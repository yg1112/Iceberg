#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 Chrome Web Store 页面抓取
"""

import asyncio
import httpx
from bs4 import BeautifulSoup

async def main():
    # 设置请求头，模拟浏览器
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    # 获取热门扩展页面
    url = "https://chromewebstore.google.com/category/extensions?hl=en&gl=US"
    
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        # 获取页面内容
        print(f"正在获取页面: {url}")
        response = await client.get(url)
        response.raise_for_status()
        
        # 保存HTML
        with open("chrome_store_page.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"已保存页面到 chrome_store_page.html")
        
        # 分析页面结构
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 尝试多种可能的选择器查找扩展卡片元素
        print("\n尝试查找扩展卡片元素...")
        selectors = [
            "div[role='listitem']",
            "article",
            "div.webstore-test-wall-tile",
            "div.e-f-b",
            "div.a-d-na",
            "div.a-Tc",
            "div[data-test='app-card']",
            "div.webstore-test-item-card"
        ]
        
        for selector in selectors:
            card_elements = soup.select(selector)
            print(f"选择器 '{selector}': 找到 {len(card_elements)} 个元素")
            
            if card_elements:
                print(f"\n使用选择器 '{selector}' 找到了扩展卡片！")
                break
        
        # 如果找到了扩展卡片
        if card_elements:
            # 输出第一个卡片的HTML结构
            print("\n第一个卡片的HTML结构:")
            first_card = card_elements[0]
            print(str(first_card)[:500] + "..." if len(str(first_card)) > 500 else str(first_card))
            
            # 尝试找到不同的元素
            print("\n尝试在第一个卡片中找到不同的元素:")
            elements_to_find = [
                "a",  # 链接
                "h2", # 标题
                "h3",
                "div",
                "span",
                "img",
                "div:-soup-contains('users')",
                "[aria-label*='rating']"
            ]
            
            for element in elements_to_find:
                found = first_card.select(element)
                print(f"选择器 '{element}': 找到 {len(found)} 个元素")
                if found and element in ["a", "h2", "h3", "div:-soup-contains('users')", "[aria-label*='rating']"]:
                    print(f"  示例: {str(found[0])[:200]}")
            
            # 尝试提取扩展信息
            print("\n尝试提取扩展信息:")
            for i, card in enumerate(card_elements[:3]):  # 只分析前3个卡片
                try:
                    print(f"\n卡片 #{i+1}:")
                    
                    # 寻找标题元素
                    for title_selector in ["h2", "h3", "div.a-na-d-w", ".a-na-d-w", "[class*='title']"]:
                        title = card.select_one(title_selector)
                        if title:
                            print(f"  标题元素 (选择器: {title_selector}): {title.text.strip()}")
                            break
                    
                    # 寻找链接元素
                    link = card.select_one("a")
                    if link and 'href' in link.attrs:
                        href = link['href']
                        print(f"  链接: {href}")
                        extension_id = href.split('/')[-1] if '/' in href else href
                        print(f"  扩展ID: {extension_id}")
                    
                    # 尝试多种选择器查找评分元素
                    for rating_selector in ["[aria-label*='rating']", "[aria-label*='stars']", ".rsw-stars", ".Na-ja-W"]:
                        rating_element = card.select_one(rating_selector)
                        if rating_element:
                            print(f"  评分元素 (选择器: {rating_selector}): {rating_element}")
                            rating_text = rating_element.get_text(strip=True)
                            aria_label = rating_element.get('aria-label', '')
                            print(f"  评分文本: {rating_text}")
                            print(f"  评分aria-label: {aria_label}")
                            break
                        
                    # 尝试多种选择器查找安装量元素
                    for users_selector in ["div:-soup-contains('users')", "div:-soup-contains('人安装')", ".e-f-ih", ".a-P", "div[class*='user']"]:
                        users_element = card.select_one(users_selector)
                        if users_element:
                            print(f"  用户数量元素 (选择器: {users_selector}): {users_element}")
                            users_text = users_element.get_text(strip=True)
                            print(f"  用户数量文本: {users_text}")
                            break
                except Exception as e:
                    print(f"  处理卡片时出错: {str(e)}")
        
        # 尝试获取一个特定扩展的详情页作为示例
        test_extension_id = "cjpalhdlnbpafiamejdnhcphjbkeiagm"  # uBlock Origin
        detail_url = f"https://chromewebstore.google.com/detail/{test_extension_id}?hl=en"
        
        print(f"\n正在获取特定扩展详情页: {detail_url}")
        detail_response = await client.get(detail_url)
        detail_response.raise_for_status()
        
        # 保存详情页HTML
        with open("chrome_store_detail.html", "w", encoding="utf-8") as f:
            f.write(detail_response.text)
        print(f"已保存详情页到 chrome_store_detail.html")
        
        # 分析详情页
        detail_soup = BeautifulSoup(detail_response.text, "html.parser")
        
        # 查找关键元素
        print("\n尝试从详情页提取信息:")
        
        # 标题
        for title_selector in ["h1", "h1.e-f-w", "h1[itemprop='name']"]:
            title = detail_soup.select_one(title_selector)
            if title:
                print(f"  标题元素 (选择器: {title_selector}): {title.get_text(strip=True)}")
                break
        
        # 描述
        for desc_selector in ["[itemprop='description']", ".C-b-p-j-Pb", ".e-f-o", "div[role='region']"]:
            description = detail_soup.select_one(desc_selector)
            if description:
                desc_text = description.get_text(strip=True)
                print(f"  描述元素 (选择器: {desc_selector}): 找到")
                print(f"  描述前50个字符: {desc_text[:50]}...")
                break
        
        # 评分
        for rating_selector in ["[aria-label*='rating']", "[aria-label*='stars']", ".rsw-stars"]:
            rating = detail_soup.select_one(rating_selector)
            if rating:
                rating_text = rating.get_text(strip=True)
                aria_label = rating.get('aria-label', '')
                print(f"  评分元素 (选择器: {rating_selector}): {rating_text}")
                print(f"  评分aria-label: {aria_label}")
                break
        
        # 用户数量
        for users_selector in ["div:-soup-contains('users')", "div:-soup-contains('人安装')", ".e-f-ih"]:
            users = detail_soup.select_one(users_selector)
            if users:
                print(f"  用户数量元素 (选择器: {users_selector}): {users.get_text(strip=True)}")
                break
        
        # 开发者
        for dev_selector in ["div:-soup-contains('Offered by:')", ".e-f-Me", "a[href*='detail/collection']"]:
            dev = detail_soup.select_one(dev_selector)
            if dev:
                print(f"  开发者元素 (选择器: {dev_selector}): {dev.get_text(strip=True)}")
                break
        
        # 更新日期
        for date_selector in ["div:-soup-contains('Updated:')", ".h-C-b-p-D-xh-hh"]:
            date = detail_soup.select_one(date_selector)
            if date:
                print(f"  更新日期元素 (选择器: {date_selector}): {date.get_text(strip=True)}")
                break
        
        # 评论
        for review_selector in [".Ka-Ia-bc", "div[role='comment']", ".W-Xb-J-S"]:
            reviews = detail_soup.select(review_selector)
            if reviews:
                print(f"  评论元素 (选择器: {review_selector}): 找到 {len(reviews)} 条评论")
                if reviews:
                    review_text = reviews[0].get_text(strip=True)
                    print(f"  第一条评论前50个字符: {review_text[:50]}...")
                break

if __name__ == "__main__":
    asyncio.run(main()) 