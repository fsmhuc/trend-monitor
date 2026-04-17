"""数据分析模块"""

# weekly_analyzer 依赖已删除的 storage 模块，改为按需导入
# from .weekly_analyzer import ...

from .opportunity_analyzer import generate_opportunity_report
from .opportunity_html_generator import generate_opportunity_html

__all__ = [
    "generate_opportunity_report",
    "generate_opportunity_html",
]
