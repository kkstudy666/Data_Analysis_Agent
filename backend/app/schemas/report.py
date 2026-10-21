# -*- coding: utf-8 -*-
"""报告相关请求模型。"""
from pydantic import BaseModel


class ReportGenerateIn(BaseModel):
    dataset_id: int
    title: str = "数据分析报告"
    # 对话消息列表：[{"role": "user"|"assistant", "content": "..."}]
    messages: list[dict] = []
