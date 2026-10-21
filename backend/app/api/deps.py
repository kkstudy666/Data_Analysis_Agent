# -*- coding: utf-8 -*-
"""API 依赖：JWT 鉴权。"""
from fastapi import Request

from app.core.exceptions import AuthError
from app.core.security import decode_access_token


def get_current_user(request: Request) -> dict:
    """从 Authorization 头解析当前用户，失败抛 401。"""
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise AuthError()
    try:
        payload = decode_access_token(auth[7:])
    except Exception:
        raise AuthError()
    return {"id": int(payload["sub"]), "username": payload["username"]}
