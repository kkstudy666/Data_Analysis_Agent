# -*- coding: utf-8 -*-
"""模型提供商列表接口（供前端选择本地 Ollama / DeepSeek API）。"""
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.config import get_settings

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
def list_models(user: dict = Depends(get_current_user)):
    """返回可用模型提供商列表，DeepSeek 未配置 key 时标记 unavailable。"""
    settings = get_settings()
    return {
        "models": [
            {
                "provider": "ollama",
                "label": "本地模型 (Ollama)",
                "model": settings.model_name,
                "available": True,
            },
            {
                "provider": "deepseek",
                "label": "DeepSeek API",
                "model": settings.deepseek_model,
                "available": bool(settings.deepseek_api_key),
            },
        ]
    }
