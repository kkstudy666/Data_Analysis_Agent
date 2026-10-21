# -*- coding: utf-8 -*-
"""用户认证服务。"""
from sqlalchemy.orm import Session

from app.core.exceptions import AuthError, ValidationError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User


def register(db: Session, username: str, password: str) -> User:
    """注册新用户（PBKDF2 加盐哈希存储）。"""
    username = username.strip()
    if not username or not password:
        raise ValidationError("用户名和密码不能为空")
    if len(password) < 6:
        raise ValidationError("密码长度至少 6 位")
    if db.query(User).filter(User.username == username).first():
        raise ValidationError("用户名已存在")

    hashed, salt = hash_password(password)
    user = User(username=username, password_hash=hashed, salt=salt)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(db: Session, username: str, password: str) -> dict:
    """登录校验并签发 JWT。"""
    user = db.query(User).filter(User.username == username.strip()).first()
    if not user or not verify_password(password, user.salt, user.password_hash):
        raise AuthError("用户名或密码错误")
    token = create_access_token(user.id, user.username)
    return {"token": token, "user": {"id": user.id, "username": user.username}}
