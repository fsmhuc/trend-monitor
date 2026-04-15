"""LLM 智能简评生成器 - 使用 DashScope (通义千问)"""

import os
import json
import requests


DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
DASHSCOPE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
MODEL = "qwen-turbo"  # 便宜快速


def generate_comment(section_name, items):
    """
    为某个板块生成 1-2 句简评

    Args:
        section_name: 板块名称
        items: 该板块的数据列表

    Returns:
        str: 简评文本
    """
    if not items:
        return "今日暂无数据"

    if not DASHSCOPE_API_KEY:
        return _rule_based_comment(section_name, items)

    # 提取关键信息用于提示词
    item_summaries = []
    for item in items[:6]:  # 最多取 6 条
        if "name" in item:
            item_summaries.append(f"- {item['name']}: {item.get('description', item.get('tagline', ''))[:80]}")
        elif "title" in item:
            item_summaries.append(f"- {item['title'][:80]}")

    prompt = f"""你是 AI 趋势日报的智能编辑。请根据以下数据，用中文写 1-2 句简评，要求：
1. 点出今天最值得关注的趋势或亮点
2. 指出与"工作提效/创业/投资"的关联
3. 简洁，不要废话，不要"综上所述"
4. 不要编造数据中没有的信息

板块：{section_name}
数据：
{chr(10).join(item_summaries)}

请写简评："""

    try:
        resp = requests.post(
            DASHSCOPE_URL,
            headers={
                "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 150,
                "temperature": 0.3,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        comment = data["choices"][0]["message"]["content"].strip()
        return comment
    except Exception as e:
        print(f"  LLM 简评失败，使用规则生成: {e}")
        return _rule_based_comment(section_name, items)


def _rule_based_comment(section_name, items):
    """规则生成简评（备用方案）"""
    count = len(items)

    if "GitHub" in section_name:
        # 统计 AI 相关项目
        ai_count = sum(1 for i in items if any(kw in (i.get("name", "") + " " + i.get("description", "")).lower()
                          for kw in ["ai", "llm", "agent", "gpt", "model", "claude"]))
        names = [i.get("name", "?") for i in items[:3]]
        if ai_count > count // 2:
            return f"今日 {count} 个 Trending 项目中 {ai_count} 个与 AI 相关，AI 热度持续。值得关注：{', '.join(names)}"
        else:
            return f"今日 {count} 个项目上榜。热门：{', '.join(names)}"

    elif "Product Hunt" in section_name:
        names = [i.get("name", "?") for i in items[:3]]
        return f"今日 {count} 个新产品上线。值得关注：{', '.join(names)}"

    elif "Hacker News" in section_name:
        titles = [i.get("title", "?")[:40] for i in items[:3]]
        return f"今日技术社区热议：{'；'.join(titles)}"

    elif "AI 工具" in section_name:
        names = [i.get("name", "?") for i in items[:3]]
        return f"今日发现 {count} 个新 AI 工具。推荐关注：{', '.join(names)}"

    elif "新闻" in section_name:
        sources = set(i.get("source", "") for i in items)
        return f"今日从 {', '.join(sources)} 等来源采集 {count} 条 AI 行业新闻"

    return f"今日 {count} 条内容"
