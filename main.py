#!/usr/bin/env python3
"""AI 趋势监控工具 - 工作提效 | 创业方向 | 行业动态 | 投资参考"""

import argparse
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from collectors import fetch_trending_repos, fetch_product_hunt_posts, fetch_hackernews_posts, fetch_ai_tools, fetch_ai_news
from reporters import generate_markdown_report
from reporters.html_generator import generate_html_report
from analyzers.opportunity_analyzer import generate_opportunity_report
from analyzers.opportunity_html_generator import generate_opportunity_html
from senders import send_email_report
from storage import save_daily_data
from llm_comment import generate_comment


def main():
    parser = argparse.ArgumentParser(description="AI 趋势监控工具")
    parser.add_argument("--no-email", action="store_true", help="跳过发送邮件")
    args = parser.parse_args()

    print("正在采集数据...")

    # 采集 GitHub Trending（发现新工具）
    print("  - 抓取 GitHub Trending...")
    github_trending_data = fetch_trending_repos(limit=8)
    print(f"    获取到 {len(github_trending_data)} 个项目")

    # 采集 Product Hunt（新产品发布）
    print("  - 抓取 Product Hunt...")
    product_hunt_data = fetch_product_hunt_posts(limit=8)
    print(f"    获取到 {len(product_hunt_data)} 个产品")

    # 采集 Hacker News（技术社区热议）
    print("  - 抓取 Hacker News...")
    hackernews_data = fetch_hackernews_posts(limit=8)
    print(f"    获取到 {len(hackernews_data)} 个热门")

    # 采集 There's An AI For That（AI 工具库）
    print("  - 抓取 There's An AI For That...")
    ai_tools_data = fetch_ai_tools(limit=8)
    print(f"    获取到 {len(ai_tools_data)} 个工具")

    # 采集 AI 行业新闻（投资参考）
    print("  - 抓取 AI 行业新闻...")
    ai_news_data = fetch_ai_news(limit=5)
    print(f"    获取到 {len(ai_news_data)} 条新闻")

    # 生成各板块简评
    print("正在生成智能简评...")
    comments = {
        "github": generate_comment("GitHub Trending", github_trending_data),
        "product_hunt": generate_comment("Product Hunt", product_hunt_data),
        "hacker_news": generate_comment("Hacker News", hackernews_data),
        "ai_tools": generate_comment("AI 工具推荐", ai_tools_data),
        "ai_news": generate_comment("AI 行业新闻", ai_news_data),
    }
    for k, v in comments.items():
        print(f"  [{k}] {v}")

    # 生成 Markdown 报告
    print("正在生成报告...")
    report = generate_markdown_report(
        github_trending_data,
        product_hunt_data,
        hackernews_data,
        ai_tools_data,
        ai_news_data,
        comments,
    )
    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("✅ 报告已生成：report.md")

    # 生成 HTML 报告
    html_report = generate_html_report(
        product_hunt_data,
        ai_tools_data,
        github_trending_data,
        hackernews_data,
        ai_news_data,
        comments,
    )
    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html_report)
    print("✅ HTML report saved to docs/index.html")

    # 存储每日数据
    print("正在存储数据...")
    cst = ZoneInfo("Asia/Shanghai")
    today = datetime.now(cst).strftime("%Y-%m-%d")
    daily_data = {
        "github_trending": github_trending_data,
        "product_hunt": product_hunt_data,
        "hacker_news": hackernews_data,
        "ai_tools": ai_tools_data,
        "ai_news": ai_news_data,
        "comments": comments,
    }
    if save_daily_data(today, daily_data):
        print(f"✅ 数据已存储：data/daily/{today}.json")
    else:
        print("⚠️  数据存储失败，继续执行...")

    # 生成创业机会+工作提效分析报告
    print("正在生成机会分析报告...")
    opp_report = generate_opportunity_report(
        product_hunt_data,
        ai_tools_data,
        github_trending_data,
        hackernews_data,
    )
    os.makedirs("analysis/daily", exist_ok=True)
    opp_path = f"analysis/daily/{today}-opportunity.md"
    with open(opp_path, "w", encoding="utf-8") as f:
        f.write(opp_report)
    print(f"✅ Opportunity analysis saved to {opp_path}")

    # 生成机会分析 HTML
    opp_html = generate_opportunity_html(opp_report)
    with open("docs/opportunity.html", "w", encoding="utf-8") as f:
        f.write(opp_html)
    print("✅ Opportunity HTML saved to docs/opportunity.html")

    # 发送邮件
    if not args.no_email:
        print("正在发送邮件...")
        if send_email_report(report):
            print("✅ 邮件发送成功")
    else:
        print("⏭️  跳过邮件发送")


if __name__ == "__main__":
    main()
