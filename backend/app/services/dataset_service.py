# -*- coding: utf-8 -*-
"""数据集管理服务：上传、解析、清洗预检、列表、重命名、删除。"""
import uuid
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.file_validate import (
    validate_extension,
    validate_magic_bytes,
    validate_mime,
    validate_size,
)
from app.core.logger import get_logger
from app.models.dataset import Dataset

settings = get_settings()
logger = get_logger("dataset_service")


def _read_dataframe(file_path: str, file_type: str) -> pd.DataFrame:
    """按类型读取数据为 DataFrame。"""
    if file_type in ("xlsx", "xls"):
        return pd.read_excel(file_path)
    if file_type == "json":
        return pd.read_json(file_path)
    return pd.read_csv(file_path, encoding="utf-8-sig")  # 兼容 BOM 与中文


def _build_meta(df: pd.DataFrame) -> dict:
    """构建元数据 + 清洗预检信息（字段/类型/缺失值/重复值/异常值）。"""
    total = len(df)
    columns = []
    for col in df.columns:
        s = df[col]
        missing = int(s.isna().sum())
        columns.append({
            "name": str(col),
            "dtype": str(s.dtype),
            "missing": missing,
            "missing_ratio": round(missing / total, 4) if total else 0,
            "unique": int(s.nunique()),
        })

    duplicate = int(df.duplicated().sum())

    # 数值列异常值检测（IQR 法）
    outliers = {}
    for col in df.select_dtypes(include="number").columns:
        s = df[col].dropna()
        if len(s) < 4:
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        cnt = int(((s < lo) | (s > hi)).sum())
        if cnt > 0:
            outliers[str(col)] = cnt

    # 预处理建议
    suggestions = []
    if any(c["missing"] > 0 for c in columns):
        suggestions.append("存在缺失值，建议进行缺失值填充或删除缺失行。")
    if duplicate > 0:
        suggestions.append(f"存在 {duplicate} 行重复数据，建议去重。")
    if outliers:
        suggestions.append(f"检测到异常值（列：{', '.join(outliers.keys())}），建议核查或剔除。")

    return {
        "row_count": total,
        "column_count": len(df.columns),
        "columns": columns,
        "duplicate_count": duplicate,
        "outliers": outliers,
        "suggestions": suggestions,
        "sample": df.head(5).to_dict(orient="records"),
    }


def upload_dataset(db: Session, user_id: int, filename: str, content: bytes) -> Dataset:
    """上传并登记数据集（三层校验 → 落盘 → 解析预检 → 入库）。"""
    file_type = validate_extension(filename)
    validate_size(len(content), settings.max_upload_mb)
    validate_mime(None, file_type)  # 上传接口未显式携带 MIME，靠 magic bytes 兜底
    validate_magic_bytes(content, file_type)

    # UUID 重命名 + 用户目录隔离
    user_dir = Path(settings.upload_dir) / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}.{file_type}"
    file_path = user_dir / stored_name
    file_path.write_bytes(content)

    try:
        df = _read_dataframe(str(file_path), file_type)
    except Exception as e:
        file_path.unlink(missing_ok=True)
        logger.error("数据集解析失败: %s", e)
        raise ValidationError(f"文件解析失败：{e}")

    meta = _build_meta(df)
    ds = Dataset(
        user_id=user_id,
        name=Path(filename).stem or "未命名数据集",
        stored_name=stored_name,
        file_path=str(file_path),
        file_type=file_type,
        row_count=meta["row_count"],
        column_count=meta["column_count"],
        meta_info=meta,
    )
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return ds


def list_datasets(db: Session, user_id: int) -> list[Dataset]:
    """按用户过滤数据集列表（数据权限隔离）。"""
    return (
        db.query(Dataset)
        .filter(Dataset.user_id == user_id)
        .order_by(Dataset.created_at.desc())
        .all()
    )


def get_dataset(db: Session, user_id: int, dataset_id: int) -> Dataset:
    """获取属于当前用户的数据集，否则 404（防止越权）。"""
    ds = db.query(Dataset).filter(
        Dataset.id == dataset_id, Dataset.user_id == user_id
    ).first()
    if not ds:
        raise NotFoundError("数据集不存在")
    return ds


def rename_dataset(db: Session, user_id: int, dataset_id: int, name: str) -> Dataset:
    ds = get_dataset(db, user_id, dataset_id)
    ds.name = name.strip() or ds.name
    db.commit()
    db.refresh(ds)
    return ds


def delete_dataset(db: Session, user_id: int, dataset_id: int) -> None:
    ds = get_dataset(db, user_id, dataset_id)
    try:
        Path(ds.file_path).unlink(missing_ok=True)
    except Exception:
        pass
    db.delete(ds)
    db.commit()
