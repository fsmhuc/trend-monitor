"""AI 行业新闻采集器 - 用于股票/基金参考"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def fetch_ai_news(limit=5):
    """从多个 RSS 源抓取 AI 行业新闻"""
    all_news = []

    # 1. TechCrunch AI 板块
    try:
        r = requests.get("https://techcrunch.com/category/artificial-intelligence/feed/", headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "xml")
        for item in soup.select("item")[:limit]:
            title = item.select_one("title")
            link = item.select_one("link")
            pub = item.select_one("pubDate")
            desc = item.select_one("description")
            if title and link:
                all_news.append({
                    "source": "TechCrunch AI",
                    "title": title.get_text(strip=True),
                    "link": link.get_text(strip=True),
                    "date": pub.get_text(strip=True) if pub else "",
                    "desc": _clean_desc(desc.get_text(strip=True) if desc else ""),
                })
    except Exception as e:
        print(f"  TechCrunch 采集失败: {e}")

    # 2. The Verge AI 板块
    try:
        r = requests.get("https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "xml")
        for item in soup.select("entry")[:limit]:
            title = item.select_one("title")
            link = item.select_one("link")
            if title and link:
                href = link.get("href", "") if isinstance(link, object) else link.get_text(strip=True)
                all_news.append({
                    "source": "The Verge AI",
                    "title": title.get_text(strip=True),
                    "link": href,
                    "date": "",
                    "desc": "",
                })
    except Exception as e:
        print(f"  The Verge 采集失败: {e}")

    # 3. 36Kr AI 板块（中文）
    try:
        r = requests.get("https://36kr.com/feed", headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "xml")
        ai_items = []
        for item in soup.select("item"):
            title = item.select_one("title")
            cats = [c.get_text() for c in item.select("category")] if item.select("category") else []
            if title and any("AI" in c or "人工智能" in c or "智能" in c for c in cats):
                link = item.select_one("link")
                ai_items.append({
                    "source": "36Kr AI",
                    "title": title.get_text(strip=True),
                    "link": link.get_text(strip=True) if link else "",
                    "date": item.select_one("pubDate").get_text(strip=True) if item.select_one("pubDate") else "",
                    "desc": "",
                })
        all_news.extend(ai_items[:limit])
    except Exception as e:
        print(f"  36Kr 采集失败: {e}")

    # 去重（按标题）
    seen = set()
    unique = []
    for item in all_news:
        if item["title"] not in seen:
            seen.add(item["title"])
            unique.append(item)

    return unique[:limit * 2]


def _clean_desc(text):
    """清理描述中的 HTML 标签"""
    if not text:
        return ""
    text = text[:200]
    # 简单清理
    import re
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()[:150]
