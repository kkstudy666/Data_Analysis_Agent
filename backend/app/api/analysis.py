# -*- coding: utf-8 -*-
"""数据分析接口（SSE 流式）。"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.schemas.analysis import ChatIn
from app.services import analysis_service, dataset_service

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/chat")
async def chat(
    data: ChatIn,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """对话分析：SSE 流式返回 Agent 执行全过程。"""
    ds = dataset_service.get_dataset(db, user["id"], data.dataset_id)
    return StreamingResponse(
        analysis_service.stream_analysis(ds, data.question, data.history, data.provider),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 关闭 nginx 缓冲，保证流式推送
        },
    )
