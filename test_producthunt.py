#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Product Hunt页面抓取
"""

import asyncio
import httpx

async def main():
    url = "https://www.producthunt.com/p/general"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    }
    
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        response = await client.get(url)
        print(f"Status: {response.status_code}")
        
        # 打印前1000个字符
        print(response.text[:1000])
        
        # 保存完整页面到文件
        with open("product_hunt_page.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"完整页面已保存到 product_hunt_page.html")
        
        # 查找__NEXT_DATA__脚本
        if "__NEXT_DATA__" in response.text:
            print("找到Next.js数据...")
            start_idx = response.text.find('<script id="__NEXT_DATA__"')
            if start_idx > 0:
                end_idx = response.text.find('</script>', start_idx)
                if end_idx > 0:
                    next_data = response.text[start_idx:end_idx+9]
                    with open("next_data.html", "w", encoding="utf-8") as f:
                        f.write(next_data)
                    print(f"Next.js数据已保存到 next_data.html")

if __name__ == "__main__":
    asyncio.run(main()) 