# -*- coding: utf-8 -*-
"""数据集相关请求/响应模型。"""
from datetime import datetime

from pydantic import BaseModel, Field


class DatasetOut(BaseModel):
    id: int
    name: str
    file_type: str
    row_count: int
    column_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DatasetRenameIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class DatasetMetaOut(BaseModel):
    id: int
    name: str
    file_type: str
    row_count: int
    column_count: int
    meta_info: dict

    model_config = {"from_attributes": True}
