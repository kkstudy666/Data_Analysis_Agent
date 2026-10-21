# -*- coding: utf-8 -*-
"""报告生成工具：整合分析结论与图表，生成 Markdown 报告文本。"""
import json

from langchain_core.tools import tool


@tool
def report_tool(title: str, conclusions: str, charts: str = "[]") -> str:
    """整合分析结论与图表，生成 Markdown 格式的分析报告。

    Args:
        title: 报告标题。
        conclusions: 分析结论（Markdown 文本，可含多段、列表、表格）。
        charts: 报告中包含的图表清单（JSON 字符串数组），
            形如 [{"title": "各品类销售额分布", "chart_type": "pie"}]。
    """
    try:
        chart_list = json.loads(charts) if charts else []
    except (json.JSONDecodeError, TypeError):
        chart_list = []

    md = f"# {title}\n\n"
    md += conclusions.rstrip() + "\n\n"

    if chart_list:
        md += "## 图表清单\n\n"
        for c in chart_list:
            if isinstance(c, dict):
                md += f"- **{c.get('title', '图表')}**（{c.get('chart_type', '')}）\n"
    return md
