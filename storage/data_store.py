"""每日数据存储 - AI 趋势监控精简版"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


# 数据存储目录
DATA_DIR = Path(__file__).parent.parent / "data" / "daily"


def save_daily_data(date, data):
    """
    保存每日采集的数据为 JSON 文件

    Args:
        date: 日期字符串，格式 YYYY-MM-DD
        data: 包含所有数据源的字典

    Returns:
        bool: 保存成功返回 True，失败返回 False
    """
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        cst = ZoneInfo("Asia/Shanghai")
        timestamp = datetime.now(cst).strftime("%Y-%m-%d %H:%M")

        output = {
            "date": date,
            "timestamp": timestamp,
            "sources": {
                "github_trending": len(data.get("github_trending", [])),
                "product_hunt": len(data.get("product_hunt", [])),
                "hacker_news": len(data.get("hacker_news", [])),
                "ai_tools": len(data.get("ai_tools", [])),
                "ai_news": len(data.get("ai_news", [])),
            },
            **data,
        }

        filepath = DATA_DIR / f"{date}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"存储失败: {e}")
        return False


def cleanup_old_data(keep_days=30):
    """清理 N 天前的数据"""
    try:
        cutoff = datetime.now(ZoneInfo("Asia/Shanghai")) - timedelta(days=keep_days)
        for f in DATA_DIR.glob("*.json"):
            file_date = datetime.strptime(f.stem, "%Y-%m-%d").replace(tzinfo=ZoneInfo("Asia/Shanghai"))
            if file_date < cutoff:
                f.unlink()
                print(f"  删除过期数据: {f.name}")
        return True
    except Exception as e:
        print(f"清理失败: {e}")
        return False
