"""创业机会 + 工作提效分析器"""

import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo


# 关键词分类：判断产品适合哪个方向
WORK_EFFICIENCY_KEYWORDS = [
    "productivity", "efficiency", "automation", "workflow", "assistant",
    "summarize", "translate", "schedule", "calendar", "email", "writing",
    "code", "developer", "programming", "debug", "test", "generate",
    "agent", "copilot", "tool", "extension", "plugin", "integrat",
    "AI", "智能", "效率", "办公", "自动", "生成", "助手",
]

STARTUP_KEYWORDS = [
    "startup", "business", "saas", "platform", "service", "monetiz",
    "revenue", "subscription", "market", "ecommerce", "shop", "sell",
    "customer", "crm", "marketing", "social", "content", "creator",
    "创业", "商业", "变现", "订阅", "平台", "服务", "营销", "内容",
]

INVEST_KEYWORDS = [
    "funding", "investment", "valuation", "acquisition", "ipo", "market",
    "stock", "earnings", "financial", "bank", "trading", "quant",
    "data center", "gpu", "chip", "cloud", "infrastruct",
    "投资", "融资", "上市", "估值", "金融", "芯片", "数据中",
]


def _classify(item_text):
    """判断产品属于哪个方向"""
    text = (item_text or "").lower()
    categories = []
    for kw in WORK_EFFICIENCY_KEYWORDS:
        if kw.lower() in text:
            categories.append("工作提效")
            break
    for kw in STARTUP_KEYWORDS:
        if kw.lower() in text:
            categories.append("创业方向")
            break
    for kw in INVEST_KEYWORDS:
        if kw.lower() in text:
            categories.append("投资参考")
            break
    if not categories:
        categories = ["其他"]
    return categories


def _score_product(product):
    """给产品打分（创业可行性）"""
    text = json.dumps(product).lower()
    score = 0
    # 技术门槛低（纯软件、无硬件）
    if any(kw in text for kw in ["app", "web", "extension", "plugin", "tool", "api"]):
        score += 1
    # 有明确用户场景
    if any(kw in text for kw in ["for", "help", "your", "manage", "create", "build"]):
        score += 1
    # 有商业模式暗示
    if any(kw in text for kw in ["pro", "premium", "subscription", "plan", "pricing"]):
        score += 1
    # AI 相关（当前风口）
    if any(kw in text for kw in ["ai", "llm", "gpt", "claude", "model", "generative"]):
        score += 1
    return min(score, 5)


def _find_duplicates(all_items, window=3):
    """找出近 N 天重复出现的产品"""
    name_count = {}
    for item in all_items:
        name = item.get("name", item.get("title", ""))
        if name:
            name_count[name] = name_count.get(name, 0) + 1
    return {k: v for k, v in name_count.items() if v >= 2}


def generate_opportunity_report(product_hunt, ai_tools, github, hackernews):
    """生成创业机会 + 工作提效分析报告"""
    cst = ZoneInfo("Asia/Shanghai")
    today = datetime.now(cst).strftime("%Y-%m-%d %H:%M")

    # 合并所有数据
    all_items = []
    for p in product_hunt:
        all_items.append({"type": "Product Hunt", **p})
    for t in ai_tools:
        all_items.append({"type": "AI Tool", **t})
    for g in github:
        all_items.append({"type": "GitHub", **g})
    for h in hackernews:
        all_items.append({"type": "Hacker News", **h})

    # 分类
    work_tools = [i for i in all_items if "工作提效" in _classify(i.get("desc", i.get("description", "")))]
    startup_tools = [i for i in all_items if "创业方向" in _classify(i.get("desc", i.get("description", "")))]
    invest_tools = [i for i in all_items if "投资参考" in _classify(i.get("desc", i.get("description", "")))]

    # 打分排序
    for item in startup_tools:
        item["score"] = _score_product(item)
    startup_tools.sort(key=lambda x: x.get("score", 0), reverse=True)

    # 重复出现（持续热度）
    duplicates = _find_duplicates(all_items)

    lines = [
        "# 🚀 创业机会 & 工作提效分析报告",
        f"**生成时间:** {today} (北京时间)",
        "",
        "## 📊 今日概览",
        f"- 共发现 {len(all_items)} 个项目",
        f"- 工作提效: {len(work_tools)} 个",
        f"- 创业方向: {len(startup_tools)} 个",
        f"- 投资参考: {len(invest_tools)} 个",
        "",
        "---",
        "",
    ]

    # 工作提效推荐
    lines.append("## 💼 工作提效推荐")
    lines.append("")
    if work_tools:
        for i, item in enumerate(work_tools[:5], 1):
            name = item.get("name", item.get("title", "未知"))
            desc = item.get("desc", item.get("description", "无描述"))[:150]
            link = item.get("link", "")
            source = item.get("type", "")
            lines.append(f"### {i}. [{name}]({link})")
            lines.append(f"**来源:** {source}")
            if desc:
                lines.append(f"**简介:** {desc}")
            lines.append("")
    else:
        lines.append("今日无相关项目")
        lines.append("")

    lines.append("---")
    lines.append("")

    # 创业机会分析
    lines.append("## 💡 创业机会（Top 5）")
    lines.append("")
    if startup_tools:
        for i, item in enumerate(startup_tools[:5], 1):
            name = item.get("name", item.get("title", "未知"))
            desc = item.get("desc", item.get("description", "无描述"))[:150]
            link = item.get("link", "")
            score = item.get("score", 0)
            lines.append(f"### {i}. [{name}]({link}) ⭐{'★' * score}{'☆' * (5 - score)}")
            if desc:
                lines.append(f"**简介:** {desc}")
            lines.append(f"**创业可行性:** {'高' if score >= 3 else '中' if score >= 2 else '低'}")
            lines.append("")
    else:
        lines.append("今日无相关项目")
        lines.append("")

    lines.append("---")
    lines.append("")

    # 投资参考
    lines.append("## 📈 投资参考")
    lines.append("")
    if invest_tools:
        for i, item in enumerate(invest_tools[:5], 1):
            name = item.get("name", item.get("title", "未知"))
            desc = item.get("desc", item.get("description", "无描述"))[:150]
            link = item.get("link", "")
            lines.append(f"### {i}. [{name}]({link})")
            if desc:
                lines.append(f"**摘要:** {desc}")
            lines.append("")
    else:
        lines.append("今日无相关项目")
        lines.append("")

    lines.append("---")
    lines.append("")

    # 持续热度（重复出现）
    if duplicates:
        lines.append("## 🔥 持续热度（重复出现）")
        lines.append("")
        for name, count in list(duplicates.items())[:10]:
            lines.append(f"- **{name}** — 出现 {count} 次")
        lines.append("")

    lines.append("---")
    lines.append("_报告由 trend-monitor 自动生成_")
    lines.append("")

    return "\n".join(lines)
