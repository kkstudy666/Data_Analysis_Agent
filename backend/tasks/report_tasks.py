# -*- coding: utf-8 -*-
"""Celery 任务：报告生成。"""
from celery_app import celery_app
from app.services.report_service import generate_report_file


@celery_app.task(bind=True, time_limit=120)
def generate_report_task(self, task_id: str, title: str, messages: list) -> str:
    """异步生成 Markdown 分析报告，返回文件路径。"""
    return generate_report_file(task_id, title, messages)
