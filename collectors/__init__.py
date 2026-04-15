"""数据采集器模块 - AI 趋势监控精简版"""

from .github_trending import fetch_trending_repos
from .product_hunt import fetch_product_hunt_posts
from .hackernews import fetch_hackernews_posts
from .theresanaiforthat import fetch_ai_tools
from .ai_news import fetch_ai_news

__all__ = [
    "fetch_trending_repos",
    "fetch_product_hunt_posts",
    "fetch_hackernews_posts",
    "fetch_ai_tools",
    "fetch_ai_news",
]
