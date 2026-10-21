# -*- coding: utf-8 -*-
"""统一业务异常与响应结构。

API 层抛出这些异常，由 main.py 的全局异常处理器转换为统一 JSON 响应：
{code: 业务错误码, message: 人类可读信息}
"""


class AppError(Exception):
    """业务异常基类。"""

    def __init__(self, message: str, status_code: int = 400, code: str = "BAD_REQUEST"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class AuthError(AppError):
    """未登录 / 凭证失效（401）。"""

    def __init__(self, message: str = "未登录或凭证已失效"):
        super().__init__(message, 401, "UNAUTHORIZED")


class ForbiddenError(AppError):
    """无权访问（403）。"""

    def __init__(self, message: str = "无权访问该资源"):
        super().__init__(message, 403, "FORBIDDEN")


class NotFoundError(AppError):
    """资源不存在（404）。"""

    def __init__(self, message: str = "资源不存在"):
        super().__init__(message, 404, "NOT_FOUND")


class ValidationError(AppError):
    """参数 / 数据校验失败（422）。"""

    def __init__(self, message: str = "参数校验失败"):
        super().__init__(message, 422, "VALIDATION_ERROR")
