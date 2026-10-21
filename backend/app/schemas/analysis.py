# -*- coding: utf-8 -*-
"""数据分析相关请求模型。"""
from pydantic import BaseModel, Field


class ChatIn(BaseModel):
    """对话分析请求：携带数据集 ID、问题、模型提供商与多轮历史。"""

    dataset_id: int
    question: str = Field(min_length=1)
    # 历史消息：[{"role": "user"|"assistant", "content": "..."}]
    history: list[dict] = []
    # 模型提供商：ollama（本地）/ deepseek（云端 API）
    provider: str = "ollama"
