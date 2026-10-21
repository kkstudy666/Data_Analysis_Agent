# -*- coding: utf-8 -*-
"""LLM 工厂：OpenAI 兼容 API，支持本地 Ollama / DeepSeek 云端切换。

通过环境变量配置两种提供商：
- 本地 Ollama：OPENAI_API_BASE / OPENAI_API_KEY / MODEL_NAME
- DeepSeek API：DEEPSEEK_API_BASE / DEEPSEEK_API_KEY / DEEPSEEK_MODEL
"""
from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.core.exceptions import ValidationError

settings = get_settings()


def get_llm(provider: str = "ollama", streaming: bool = True) -> ChatOpenAI:
    """创建 LLM 实例。

    Args:
        provider: "ollama"（本地）或 "deepseek"（云端 API）。
        streaming: 是否流式（SSE 思考过程可视化需 True；工具内纠错用 False）。
    """
    if provider == "deepseek":
        if not settings.deepseek_api_key:
            raise ValidationError("请先在 .env 配置 DEEPSEEK_API_KEY 后再使用 DeepSeek API")
        base_url = settings.deepseek_api_base
        api_key = settings.deepseek_api_key
        model = settings.deepseek_model
    else:
        base_url = settings.openai_api_base
        api_key = settings.openai_api_key
        model = settings.model_name

    return ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model,
        temperature=settings.llm_temperature,
        streaming=streaming,
        timeout=120,
        max_retries=2,
    )
