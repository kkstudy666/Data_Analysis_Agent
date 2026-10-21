# -*- coding: utf-8 -*-
"""Celery 任务：代码执行（通过沙箱）。"""
from celery_app import celery_app
from app.sandbox.executor import execute_code


@celery_app.task(bind=True, time_limit=60, soft_time_limit=45)
def execute_code_task(self, data_file_path: str, file_type: str, code: str) -> dict:
    """在沙箱中执行代码，返回标准化结果。"""
    return execute_code(data_file_path, file_type, code)
