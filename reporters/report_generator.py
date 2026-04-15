"""Markdown 报告生成器 - AI 趋势监控精简版"""

from datetime import datetime
from zoneinfo import ZoneInfo


def generate_markdown_report(repos, products, hackernews_posts, ai_tools=None, ai_news=None):
    """生成 Markdown 格式的报告"""
    cst = ZoneInfo("Asia/Shanghai")
    now = datetime.now(cst)
    timestamp = now.strftime("%Y-%m-%d %H:%M (北京时间)")

    lines = [
        "# 🤖 AI 趋势日报",
        "",
        f"**生成时间**: {timestamp}",
        "",
        "---",
        "",
    ]

    # GitHub Trending
    lines.append("## 🐙 GitHub Trending")
    lines.append("")
    if repos:
        for i, repo in enumerate(repos, 1):
            name = repo.get("name", "未知")
            desc = repo.get("description", "无描述")
            stars = repo.get("stars", "N/A")
            link = f"https://github.com/{name}"
            lines.append(f"### {i}. [{name}]({link}) ⭐ {stars}")
            lines.append(f"- {desc}")
            lines.append("")
    else:
        lines.append("*暂无数据*")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Product Hunt
    lines.append("## 🚀 Product Hunt 今日热门")
    lines.append("")
    if products:
        for i, product in enumerate(products, 1):
            name = product.get("name", "未知")
            tagline = product.get("tagline", "无简介")
            link = product.get("link", "")
            lines.append(f"### {i}. [{name}]({link})")
            lines.append(f"- {tagline}")
            lines.append("")
    else:
        lines.append("*暂无数据*")
        lines.append("")

    lines.append("---")
    lines.append("")

    # There's An AI For That
    lines.append("## 🧰 AI 工具推荐")
    lines.append("")
    if ai_tools:
        for i, tool in enumerate(ai_tools, 1):
            name = tool.get("name", "未知")
            desc = tool.get("description", "无描述")
            link = tool.get("link", "")
            category = tool.get("category", "")
            lines.append(f"### {i}. [{name}]({link})")
            if desc:
                lines.append(f"- {desc}")
            if category:
                lines.append(f"- 分类: {category}")
            lines.append("")
    else:
        lines.append("*暂无数据*")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Hacker News
    lines.append("## 💬 Hacker News 热议")
    lines.append("")
    if hackernews_posts:
        for i, post in enumerate(hackernews_posts, 1):
            title = post.get("title", "未知")
            link = post.get("link", "")
            points = post.get("points", "N/A")
            comments_count = post.get("comments", "N/A")
            lines.append(f"### {i}. [{title}]({link})")
            lines.append(f"- 得分: {points} | 评论: {comments_count}")
            lines.append("")
    else:
        lines.append("*暂无数据*")
        lines.append("")

    lines.append("---")
    lines.append("")

    # AI 行业新闻（投资参考）
    lines.append("## 📈 AI 行业新闻（投资参考）")
    lines.append("")
    if ai_news:
        for i, news in enumerate(ai_news, 1):
            title = news.get("title", "未知")
            link = news.get("link", "")
            source = news.get("source", "")
            desc = news.get("desc", "")
            lines.append(f"### {i}. [{title}]({link})")
            lines.append(f"- **来源:** {source}")
            if desc:
                lines.append(f"- {desc}")
            lines.append("")
    else:
        lines.append("*暂无数据*")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("_报告由 trend-monitor 自动生成_")
    lines.append("")

    return "\n".join(lines)
