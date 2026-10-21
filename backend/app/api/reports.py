# -*- coding: utf-8 -*-
"""报告接口（异步生成、查询、下载）。"""
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.api.deps import get_current_user
from app.schemas.report import ReportGenerateIn
from app.services import report_service

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/generate")
def generate(data: ReportGenerateIn, user: dict = Depends(get_current_user)):
    """提交异步报告生成，返回 task_id（毫秒级返回）。"""
    return report_service.submit_report(data.model_dump())


@router.get("/{task_id}")
def status(task_id: str, user: dict = Depends(get_current_user)):
    """查询报告生成状态。"""
    return report_service.get_report_status(task_id)


@router.get("/{task_id}/download")
def download(task_id: str, user: dict = Depends(get_current_user)):
    """下载 Markdown 报告。"""
    path = report_service.get_report_path(task_id)
    return FileResponse(
        path,
        filename=f"analysis_report_{task_id[:8]}.md",
        media_type="text/markdown",
    )
