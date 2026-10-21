# -*- coding: utf-8 -*-
"""Celery 应用实例（本地 eager / 生产 redis 双模式）。

- 本地无 Redis（Windows 调试）：CELERY_MODE=eager，任务同步执行；
- 生产 / Docker Compose：CELERY_MODE=redis，经 Redis 队列异步执行。
"""
from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "data_analysis_agent",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["tasks.analysis_tasks", "tasks.report_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# 本地无 Redis 时降级为同步执行（同一套代码路径可跑通）
if settings.celery_mode == "eager":
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
