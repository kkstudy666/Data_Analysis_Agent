# -*- coding: utf-8 -*-
"""上传文件校验：扩展名白名单 + MIME 类型 + 文件头 magic bytes。"""
from pathlib import Path

from app.core.exceptions import ValidationError

ALLOWED_EXTS = {".csv", ".xlsx", ".xls", ".json"}

# 各扩展名（不带点）对应的 magic bytes 前缀（用于识别真实文件类型，防止伪造扩展名）
_MAGIC = {
    "xlsx": b"PK\x03\x04",       # xlsx 本质是 zip 压缩包
    "xls": b"\xd0\xcf\x11\xe0",  # 老式 OLE2 复合文档
}


def validate_extension(filename: str) -> str:
    """校验扩展名白名单，返回不带点的小写扩展名（如 'csv'）。"""
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTS:
        raise ValidationError(f"不支持的文件类型 {suffix or '(无扩展名)'}，仅支持 CSV / Excel / JSON")
    return suffix.lstrip(".")


def validate_mime(mime: str | None, ext: str) -> None:
    """MIME 类型粗校验。

    CSV/JSON 常被浏览器上报为 text/plain 或 application/octet-stream，
    此处仅对 Excel 做严格校验（其 MIME 相对稳定），其余放宽以避免误伤。
    """
    if ext in ("xlsx", "xls"):
        valid = {"application/zip", "application/vnd.ms-excel",
                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                 "application/octet-stream"}
        if mime and mime not in valid:
            raise ValidationError(f"MIME 类型 {mime} 与 Excel 扩展名不符")


def validate_magic_bytes(content: bytes, ext: str) -> None:
    """校验文件头 magic bytes。"""
    head = content[:16]
    if ext in _MAGIC:
        if not head.startswith(_MAGIC[ext]):
            raise ValidationError(f"文件内容与 .{ext} 扩展名不符，疑似伪造文件")
    elif ext == "json":
        if head.lstrip()[:1] not in (b"{", b"["):
            raise ValidationError("文件内容不是有效的 JSON")
    elif ext == "csv":
        if b"\x00" in head:
            raise ValidationError("文件内容不是有效的 CSV 文本")


def validate_size(size: int, max_mb: int) -> None:
    """校验文件大小上限。"""
    if size > max_mb * 1024 * 1024:
        raise ValidationError(f"文件大小超过 {max_mb}MB 上限")
