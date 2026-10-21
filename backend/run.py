# -*- coding: utf-8 -*-
"""本地无 Docker 启动入口：python run.py

启动前请先：pip install -r requirements.txt
并复制 .env.example 为 .env（本地默认 CELERY_MODE=eager，无需 Redis）。
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
