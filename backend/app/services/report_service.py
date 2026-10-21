# -*- coding: utf-8 -*-
"""报告服务：异步提交报告生成、查询状态、下载。"""
import json
import uuid
from datetime import datetime
from pathlib import Path

from app.config import get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logger import get_logger

settings = get_settings()
logger = get_logger("report_service")

_REPORT_DIR = Path("data/reports")


def _report_path(task_id: str) -> Path:
    return _REPORT_DIR / f"{task_id}.md"


def submit_report(data: dict) -> dict:
    """提交异步报告生成任务，返回 task_id。"""
    if not data.get("messages"):
        raise ValidationError("对话消息为空，无法生成报告")
    # 延迟导入避免与 tasks.report_tasks 形成循环依赖
    from tasks.report_tasks import generate_report_task

    task_id = uuid.uuid4().hex[:16]
    # 提交 Celery 异步任务
    generate_report_task.delay(task_id, data.get("title", "数据分析报告"), data["messages"])
    return {"task_id": task_id, "status": "processing"}


def generate_report_file(task_id: str, title: str, messages: list) -> str:
    """Celery 任务执行体：把对话消息整合为 Markdown 报告并落盘。"""
    _REPORT_DIR.mkdir(parents=True, exist_ok=True)

    md = f"# {title}\n\n"
    md += f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md += "## 分析对话记录\n\n"
    for m in messages:
        role = m.get("role")
        content = m.get("content", "")
        if role == "user":
            md += f"### 问题\n\n{content}\n\n"
        elif role == "assistant":
            md += f"### 分析结论\n\n{content}\n\n"

    path = _report_path(task_id)
    path.write_text(md, encoding="utf-8")
    logger.info("报告已生成：%s", path)
    return str(path)


def get_report_status(task_id: str) -> dict:
    """查询报告生成状态（落盘即完成）。"""
    if _report_path(task_id).exists():
        return {"task_id": task_id, "status": "completed"}
    # 任务可能仍在执行
    return {"task_id": task_id, "status": "processing"}


def get_report_path(task_id: str) -> str:
    """获取报告文件路径（不存在则 404）。"""
    path = _report_path(task_id)
    if not path.exists():
        raise NotFoundError("报告不存在或尚未生成完成")
    return str(path)
