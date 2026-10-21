# -*- coding: utf-8 -*-
"""应用配置：通过 pydantic-settings 读取环境变量 / .env 文件。

所有密钥与可变参数均经环境变量注入，禁止硬编码（配合日志脱敏）。
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ---- 应用基础 ----
    app_name: str = "Data Analysis Agent"
    debug: bool = False
    secret_key: str = "dev-secret"
    jwt_secret: str = "dev-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # ---- 数据库 ----
    database_url: str = "sqlite:///./data/app.db"

    # ---- 上传 ----
    upload_dir: str = "./data/uploads"
    max_upload_mb: int = 50

    # ---- Celery / Redis ----
    celery_mode: str = "eager"  # eager=本地无 Redis 同步执行；redis=生产异步队列
    redis_url: str = "redis://localhost:6379/0"

    # ---- LLM（OpenAI 兼容 API，可切换 Ollama / DeepSeek）----
    # 本地 Ollama
    openai_api_base: str = "http://localhost:11434/v1"
    openai_api_key: str = "ollama"
    model_name: str = "qwen2.5:7b"
    # DeepSeek API（填写 DEEPSEEK_API_KEY 后即可在前端切换使用）
    deepseek_api_base: str = "https://api.deepseek.com/v1"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    llm_temperature: float = 0.0

    # ---- CORS ----
    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    # ---- 限流 ----
    rate_limit_per_minute: int = 60

    # ---- 沙箱 ----
    sandbox_timeout: int = 30
    sandbox_max_memory_mb: int = 512

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """单例配置对象。"""
    return Settings()
