# -*- coding: utf-8 -*-
"""安全模块：PBKDF2 加盐哈希 + JWT 令牌。"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app.config import get_settings

settings = get_settings()
PBKDF2_ITERATIONS = 200_000  # PBKDF2-SHA256 迭代次数


def hash_password(password: str) -> tuple[str, str]:
    """对密码做 PBKDF2-SHA256 加盐哈希，返回 (哈希值, 盐)。"""
    salt = secrets.token_hex(32)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    )
    return digest.hex(), salt


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """校验密码是否匹配（常量时间比较防时序攻击）。"""
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    )
    return secrets.compare_digest(digest.hex(), expected_hash)


def create_access_token(user_id: int, username: str) -> str:
    """签发 JWT 访问令牌。"""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """解析并校验 JWT，失败抛出异常由调用方处理。"""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
