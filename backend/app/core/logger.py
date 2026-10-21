# -*- coding: utf-8 -*-
"""分级日志 + 敏感信息脱敏。

分级约定：
- info：正常业务流程；
- error：异常与堆栈；
- debug：Agent 调用细节（仅 debug 模式开启）。
"""
import logging
import re
import sys

# 需脱敏的敏感字段（出现于日志内容时替换值）
_SENSITIVE_RE = re.compile(
    r'("?(?:password|token|api_key|apikey|authorization|secret|jwt)"?\s*[:=]\s*)"?[^",\s]+"?',
    re.IGNORECASE,
)


class SensitiveFilter(logging.Filter):
    """将日志记录中的敏感字段值替换为 ***。"""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.msg = _SENSITIVE_RE.sub(r"\1***", str(record.msg))
            record.args = ()
        except Exception:
            pass
        return True


def setup_logging(debug: bool = False) -> None:
    """初始化全局日志配置（幂等，避免重复添加 handler）。"""
    level = logging.DEBUG if debug else logging.INFO
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        ))
        handler.addFilter(SensitiveFilter())
        root.addHandler(handler)
    # 降低第三方库日志噪音
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的 logger。"""
    return logging.getLogger(name)
