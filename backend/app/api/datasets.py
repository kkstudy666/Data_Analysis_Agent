# -*- coding: utf-8 -*-
"""数据集管理接口。"""
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.schemas.dataset import DatasetMetaOut, DatasetOut, DatasetRenameIn
from app.services import dataset_service

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.get("", response_model=list[DatasetOut])
def list_datasets(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return dataset_service.list_datasets(db, user["id"])


@router.post("/upload", response_model=DatasetOut)
async def upload(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = await file.read()
    return dataset_service.upload_dataset(db, user["id"], file.filename or "data.csv", content)


@router.patch("/{dataset_id}", response_model=DatasetOut)
def rename(
    dataset_id: int,
    data: DatasetRenameIn,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return dataset_service.rename_dataset(db, user["id"], dataset_id, data.name)


@router.delete("/{dataset_id}")
def delete(
    dataset_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dataset_service.delete_dataset(db, user["id"], dataset_id)
    return {"message": "删除成功"}


@router.get("/{dataset_id}/meta", response_model=DatasetMetaOut)
def get_meta(
    dataset_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return dataset_service.get_dataset(db, user["id"], dataset_id)
