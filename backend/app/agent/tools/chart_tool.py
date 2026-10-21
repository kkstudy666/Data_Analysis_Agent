# -*- coding: utf-8 -*-
"""图表生成工具：根据分析结果生成 ECharts 配置（option）。"""
import json

from langchain_core.tools import tool


@tool
def chart_tool(chart_type: str, title: str, data: str) -> str:
    """根据分析结果生成 ECharts 图表配置（前端可交互渲染）。

    Args:
        chart_type: 图表类型，可选 line(折线)/bar(柱状)/pie(饼图)/scatter(散点)/heatmap(热力)。
        title: 图表标题。
        data: 图表数据（JSON 字符串），不同图表类型格式：
            - line/bar: {"categories": [...], "series": [{"name": "...", "data": [...]}]}
            - pie: {"data": [{"name": "...", "value": 123}, ...]}
            - scatter: {"data": [[x1,y1], [x2,y2], ...]}
            - heatmap: {"x": [...], "y": [...], "data": [[i,j,value], ...]}
    """
    try:
        payload = json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return json.dumps({"status": "error", "error": "图表数据不是有效 JSON"}, ensure_ascii=False)

    try:
        option = _build_option(chart_type, title, payload)
    except Exception as e:  # noqa: BLE001
        return json.dumps({"status": "error", "error": f"图表配置生成失败：{e}"}, ensure_ascii=False)

    return json.dumps({"status": "success", "option": option}, ensure_ascii=False, default=str)


def _build_option(chart_type: str, title: str, p: dict) -> dict:
    """构造标准 ECharts option（折线/柱状/饼/散点/热力）。"""
    base = {
        "title": {"text": title, "left": "center"},
        "tooltip": {"trigger": "item" if chart_type in ("pie", "scatter") else "axis"},
        "legend": {"bottom": 0},
        "grid": {"left": "3%", "right": "4%", "bottom": "12%", "containLabel": True},
    }

    if chart_type in ("line", "bar"):
        return {
            **base,
            "xAxis": {"type": "category", "data": p.get("categories", [])},
            "yAxis": {"type": "value"},
            "series": [
                {
                    "type": chart_type,
                    "name": s.get("name", ""),
                    "data": s.get("data", []),
                    "smooth": chart_type == "line",
                }
                for s in p.get("series", [])
            ],
        }

    if chart_type == "pie":
        return {
            **base,
            "series": [{
                "type": "pie",
                "radius": "60%",
                "data": p.get("data", []),
                "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowColor": "rgba(0,0,0,0.3)"}},
            }],
        }

    if chart_type == "scatter":
        return {
            **base,
            "xAxis": {"type": "value"},
            "yAxis": {"type": "value"},
            "series": [{"type": "scatter", "symbolSize": 10, "data": p.get("data", [])}],
        }

    if chart_type == "heatmap":
        return {
            **base,
            "xAxis": {"type": "category", "data": p.get("x", []), "splitArea": {"show": True}},
            "yAxis": {"type": "category", "data": p.get("y", []), "splitArea": {"show": True}},
            "visualMap": {"min": 0, "max": 10, "calculable": True, "orient": "horizontal", "left": "center", "bottom": "0%"},
            "series": [{"type": "heatmap", "data": p.get("data", []), "label": {"show": True}}],
        }

    raise ValueError(f"不支持的图表类型：{chart_type}")
