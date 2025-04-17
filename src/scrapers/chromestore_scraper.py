#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Chrome Web Store Scraper Module

根据PRD v2要求实现的Chrome Web Store异步数据抓取模块
支持从Chrome Web Store获取扩展数据，并返回标准化的RawPost格式
"""

import asyncio
import httpx
import time
import random
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re

# Chrome Web Store配置
CHROME_STORE_BASE = "https://chromewebstore.google.com"
CHROME_STORE_TOP_EXTENSIONS = "https://chromewebstore.google.com/category/extensions"

# 重试配置
MAX_RETRIES = 3
BASE_DELAY = 2  # 基础延迟秒数

class ChromeStoreScraper:
    """
    Chrome Web Store异步抓取器
    使用httpx和asyncio实现异步抓取，支持指数回退重试
    """
    
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        """
        初始化Chrome Web Store抓取器
        
        Args:
            client: 可选的httpx异步客户端，如果不提供则创建新的
        """
        self.client = client
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    async def __aenter__(self):
        if self.client is None:
            # 创建客户端时设置follow_redirects为True
            self.client = httpx.AsyncClient(headers=self.headers, follow_redirects=True)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client is not None:
            await self.client.aclose()
    
    async def fetch_with_retry(self, url: str, method: str = "GET", data: Dict = None) -> str:
        """
        带有指数回退重试的异步请求
        
        Args:
            url: 请求的URL
            method: HTTP方法 (GET, POST)
            data: POST请求的数据
            
        Returns:
            响应文本
            
        Raises:
            httpx.HTTPError: 如果所有重试都失败
        """
        for attempt in range(MAX_RETRIES):
            try:
                # 添加随机延迟以避免限流
                jitter = random.uniform(0.1, 0.5)
                delay = (BASE_DELAY ** attempt) + jitter
                
                if attempt > 0:
                    await asyncio.sleep(delay)
                
                if method.upper() == "GET":
                    # 设置follow_redirects为True以自动处理重定向
                    response = await self.client.get(url, follow_redirects=True)
                else:  # POST
                    response = await self.client.post(url, data=data, follow_redirects=True)
                
                response.raise_for_status()
                return response.text
                
            except httpx.HTTPError as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                
                # 如果是429 Too Many Requests，增加延迟
                if getattr(e, "response", None) and e.response.status_code == 429:
                    await asyncio.sleep(delay * 2)
    
    async def fetch_top_extensions(self, limit: int = 250) -> List[Dict[str, Any]]:
        """
        获取Chrome Web Store热门扩展列表
        
        Args:
            limit: 返回的扩展数量上限
            
        Returns:
            扩展列表，每个扩展包含id、名称、评分等信息
        """
        results = []
        
        try:
            # 构建URL，添加语言和区域参数
            page_url = f"{CHROME_STORE_TOP_EXTENSIONS}?hl=en&gl=US"
            html = await self.fetch_with_retry(page_url)
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html, "html.parser")
            
            # 新的Chrome Web Store使用div[role='listitem']作为卡片容器
            extension_cards = soup.select("div[role='listitem']")
            
            for card in extension_cards:
                try:
                    # 提取扩展链接和ID
                    link_elem = card.select_one("a")
                    if not link_elem or not link_elem.get("href"):
                        continue
                        
                    extension_url = link_elem["href"]
                    if not extension_url.startswith('http'):
                        if extension_url.startswith('/'):
                            extension_url = f"{CHROME_STORE_BASE}{extension_url}"
                        else:
                            extension_url = f"{CHROME_STORE_BASE}/{extension_url}"
                    
                    # 从URL中提取扩展ID
                    parts = extension_url.split('/')
                    extension_id = parts[-1]
                    
                    # 提取扩展名称
                    name_elem = card.select_one("h2")
                    name = name_elem.text.strip() if name_elem else "Unknown"
                    
                    # 提取评分 - 寻找包含rating的aria-label属性
                    rating_elem = card.select_one("[aria-label*='rating']")
                    rating = 0
                    if rating_elem:
                        rating_text = rating_elem.get_text(strip=True)
                        try:
                            # 尝试从文本中提取数字
                            rating = float(rating_text.split()[0])
                        except (ValueError, IndexError):
                            rating = 0
                    
                    # 提取用户数量 - 寻找包含users的文本
                    users_elem = card.select_one("div:-soup-contains('users')")
                    users_text = users_elem.text.strip() if users_elem else "0"
                    users = self._parse_users_count(users_text)
                    
                    extension_data = {
                        "id": extension_id,
                        "name": name,
                        "url": extension_url,
                        "rating": rating,
                        "users": users,
                        "source": "chrome_web_store"
                    }
                    
                    results.append(extension_data)
                    
                    # 达到限制时停止
                    if len(results) >= limit:
                        break
                        
                except Exception as e:
                    print(f"解析扩展卡片时出错: {str(e)}")
                    continue
            
        except Exception as e:
            print(f"获取扩展列表时出错: {str(e)}")
        
        return results[:limit]  # 确保不超过限制
    
    async def fetch_extension_details(self, extension_id: str) -> Dict[str, Any]:
        """
        获取Chrome扩展的详细信息
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            扩展详细信息
        """
        # 更新URL格式，添加语言参数
        url = f"{CHROME_STORE_BASE}/detail/{extension_id}?hl=en"
        html = await self.fetch_with_retry(url)
        
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html, "html.parser")
        
        # 提取扩展名称
        name_elem = soup.select_one("h1")
        name = name_elem.text.strip() if name_elem else "Unknown"
        
        # 提取描述 - 先尝试具有itemprop属性的元素，再尝试role=region的元素
        desc_elem = soup.select_one("[itemprop='description']")
        if not desc_elem:
            desc_elem = soup.select_one("div[role='region'], .C-b-p-j-Pb, .e-f-o")
        description = desc_elem.text.strip() if desc_elem else ""
        
        # 提取评分 - 从aria-label属性中提取
        rating_elem = soup.select_one("[aria-label*='rating'], [aria-label*='stars'], [aria-label*='out of 5']")
        rating = 0
        if rating_elem:
            aria_label = rating_elem.get('aria-label', '')
            if aria_label:
                # 尝试从"4.7 out of 5 stars"格式中提取数字
                try:
                    rating = float(aria_label.split()[0])
                except (ValueError, IndexError):
                    try:
                        # 另一种可能的格式
                        rating_match = re.search(r'(\d+(\.\d+)?)', aria_label)
                        if rating_match:
                            rating = float(rating_match.group(1))
                    except Exception:
                        rating = 0
        
        # 提取用户数量 - 在页面文本中查找包含"users"的内容
        users_text = ""
        page_text = soup.get_text()
        users_pattern = re.compile(r'([\d,]+(?:\.\d+)?[KMB]?) users', re.IGNORECASE)
        users_match = users_pattern.search(page_text)
        if users_match:
            users_text = users_match.group(0)
        
        users = self._parse_users_count(users_text)
        
        # 提取最后更新日期
        updated_text = ""
        # 查找包含Updated的文本
        updated_pattern = re.compile(r'Updated\s*[\w\s,]+\d{4}', re.IGNORECASE)
        updated_match = updated_pattern.search(page_text)
        if updated_match:
            updated_text = updated_match.group(0).replace("Updated", "").strip()
        
        updated_date = self._parse_update_date(updated_text)
        
        # 提取开发者
        developer = ""
        # 查找"Offered by:"后面的文本
        dev_pattern = re.compile(r'Offered by[:\s]+([\w\s()-]+)', re.IGNORECASE)
        dev_match = dev_pattern.search(page_text)
        if dev_match:
            developer = dev_match.group(1).strip()
        
        # 评论部分可能很难通过固定选择器获取，这里使用简单的方法
        reviews = []
        
        return {
            "id": extension_id,
            "name": name,
            "description": description,
            "url": url,
            "rating": rating,
            "users": users,
            "updated_date": updated_date,
            "developer": developer,
            "reviews": reviews,
            "source": "chrome_web_store"
        }
    
    def _parse_users_count(self, users_text: str) -> int:
        """
        解析用户数量文本
        
        Args:
            users_text: 用户数量文本 (例如: "10,000+ users")
            
        Returns:
            用户数量的整数表示
        """
        try:
            # 提取数字部分和可能的单位(K, M, B)
            match = re.search(r'([\d,]+(?:\.\d+)?)([KMB]?)', users_text, re.IGNORECASE)
            if not match:
                return 0
            
            num_str = match.group(1).replace(',', '')
            unit = match.group(2).upper() if len(match.groups()) > 1 else ''
            
            # 转换基础数字
            base_num = float(num_str)
            
            # 根据单位应用乘数
            if unit == 'K':
                return int(base_num * 1000)
            elif unit == 'M':
                return int(base_num * 1000000)
            elif unit == 'B':
                return int(base_num * 1000000000)
            else:
                return int(base_num)
                
        except Exception as e:
            print(f"解析用户数量时出错: {str(e)}")
            return 0
    
    def _parse_update_date(self, date_text: str) -> str:
        """
        解析更新日期文本
        
        Args:
            date_text: 日期文本
            
        Returns:
            标准化的日期字符串 (YYYY-MM-DD)
        """
        try:
            # 常见日期格式尝试解析
            date_formats = [
                "%B %d, %Y",   # January 1, 2023
                "%b %d, %Y",   # Jan 1, 2023
                "%Y-%m-%d",    # 2023-01-01
                "%d %B %Y",    # 1 January 2023
                "%d %b %Y",    # 1 Jan 2023
            ]
            
            for fmt in date_formats:
                try:
                    dt = datetime.strptime(date_text, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
                    
            return date_text  # 如果无法解析，返回原始文本
        except Exception:
            return ""
    
    async def fetch_and_convert_to_raw_post(self, extension_id: str) -> Dict[str, Any]:
        """
        获取扩展详情并转换为RawPost格式
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            RawPost格式的数据
        """
        details = await self.fetch_extension_details(extension_id)
        
        # 构建元数据
        metadata = {
            "rating": details.get("rating", 0),
            "users": details.get("users", 0),
            "updated_date": details.get("updated_date", ""),
            "developer": details.get("developer", "")
        }
        
        # 构建内容
        content = details.get("description", "")
        
        # 添加评论
        reviews = details.get("reviews", [])
        if reviews:
            content += "\n\n用户评论:\n"
            for i, review in enumerate(reviews[:5]):  # 最多包含5条评论
                rating_str = "★" * int(review.get("rating", 0))
                content += f"\n{i+1}. {rating_str} {review.get('comment', '')}"
        
        # 转换为RawPost格式
        raw_post = {
            "title": details.get("name", ""),
            "content": content,
            "url": details.get("url", ""),
            "score": details.get("rating", 0),
            "source": "chrome_web_store",
            "metadata": metadata,
            "id": extension_id
        }
        
        return raw_post

async def main():
    """测试函数"""
    async with ChromeStoreScraper() as scraper:
        extensions = await scraper.fetch_top_extensions(limit=5)
        print(f"获取到 {len(extensions)} 个热门扩展")
        
        for ext in extensions:
            print(f"\n扩展: {ext['name']} (ID: {ext['id']})")
            details = await scraper.fetch_extension_details(ext['id'])
            print(f"详情: {details['name']}, 用户数: {details['users']}, 评分: {details['rating']}")
            
if __name__ == "__main__":
    asyncio.run(main())