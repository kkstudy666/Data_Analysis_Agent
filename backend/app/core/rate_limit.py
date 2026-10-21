# -*- coding: utf-8 -*-
"""接口限流：Redis 固定窗口计数器，IP + 用户双维度。

生产环境使用 Redis；本地无 Redis 时自动降级为 fakeredis（进程内）。
"""
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import get_settings

settings = get_settings()


class FixedWindowRateLimiter:
    """固定窗口计数器：key 在 window 秒内的请求次数不超过 limit。"""

    def __init__(self):
        self._redis = None
        self._local: dict[tuple, int] = {}  # 极端情况下的进程内兜底

    def _client(self):
        if self._redis is None:
            try:
                if settings.celery_mode == "redis":
                    import redis as redis_lib

                    self._redis = redis_lib.from_url(settings.redis_url)
                else:
                    import fakeredis

                    self._redis = fakeredis.FakeRedis()
            except Exception:
                import fakeredis

                self._redis = fakeredis.FakeRedis()
        return self._redis

    def is_allowed(self, key: str, limit: int, window: int = 60) -> bool:
        try:
            r = self._client()
            now = int(time.time())
            bucket = f"rl:{key}:{now // window}"
            count = r.incr(bucket)
            if count == 1:
                r.expire(bucket, window + 1)
            return count <= limit
        except Exception:
            # 进程内兜底
            now = int(time.time())
            bucket = (key, now // window)
            self._local[bucket] = self._local.get(bucket, 0) + 1
            return self._local[bucket] <= limit


_limiter = FixedWindowRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """IP + 用户双维度固定窗口限流中间件。"""

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api"):
            ip = request.client.host if request.client else "unknown"

            # 用户维度：尽力解析 JWT 中的 user_id，失败记为 anonymous
            user_key = "anonymous"
            try:
                from app.core.security import decode_access_token

                auth = request.headers.get("authorization", "")
                if auth.startswith("Bearer "):
                    user_key = decode_access_token(auth[7:]).get("sub", "anonymous")
            except Exception:
                user_key = "anonymous"

            limit = settings.rate_limit_per_minute
            for key in (f"ip:{ip}", f"user:{user_key}"):
                if not _limiter.is_allowed(key, limit):
                    return JSONResponse(
                        {"code": "RATE_LIMITED", "message": "请求过于频繁，请稍后再试"},
                        status_code=429,
                    )
        return await call_next(request)
