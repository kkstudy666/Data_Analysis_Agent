# -*- coding: utf-8 -*-
"""FastAPI 应用入口：中间件、异常处理、路由挂载、建表。"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import analysis, auth, datasets, reports
from app.api import models as api_models  # 别名避免与 app.models 数据库模型包冲突
from app.config import get_settings
from app.core.exceptions import AppError
from app.core.logger import get_logger, setup_logging
from app.core.rate_limit import RateLimitMiddleware
from app.database import Base, engine

settings = get_settings()
setup_logging(settings.debug)
logger = get_logger("main")

# 建表（导入 models 以注册所有表到 Base.metadata）
from app import models  # noqa: E402,F401

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IP + 用户双维度限流
app.add_middleware(RateLimitMiddleware)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """业务异常 → 统一 JSON 响应。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    """未捕获异常 → 记录错误日志并返回 500。"""
    logger.error("未捕获异常: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"code": "INTERNAL_ERROR", "message": "服务器内部错误"},
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}


app.include_router(auth.router)
app.include_router(datasets.router)
app.include_router(api_models.router)
app.include_router(analysis.router)
app.include_router(reports.router)
