from pathlib import Path
from typing import Optional
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.data_processing.profiler import load_dataframe, profile_dataframe
from app.models.dataset import Dataset, DatasetColumn
from app.models.user import User
from app.utils.activity import log_activity, sanitize_json
from app.utils.file_security import validate_and_save_upload

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])


def get_authorized_dataset(db: Session, dataset_id: int, current_user: User, require_owner: bool = False) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")

    if require_owner:
        if dataset.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only modify or delete your own private datasets.",
            )
    else:
        if not dataset.is_public and dataset.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: This dataset is private to another user.",
            )
    return dataset


def serialize_dataset(d: Dataset) -> dict:
    return sanitize_json({
        "id": d.id,
        "user_id": d.user_id,
        "name": d.name,
        "description": d.description,
        "file_type": d.file_type,
        "file_size": d.file_size,
        "row_count": d.row_count,
        "column_count": d.column_count,
        "source_type": d.source_type,
        "is_public": bool(d.is_public),
        "quality_score": round(float(d.quality_score or 100.0), 2),
        "profile_json": d.profile_json,
        "upload_timestamp": d.upload_timestamp.isoformat() if d.upload_timestamp else None,
        "processing_status": d.processing_status,
        "has_processed_version": bool(d.processed_file_path and Path(d.processed_file_path).exists()),
        "columns": [
            {
                "id": c.id,
                "column_name": c.column_name,
                "data_type": c.data_type,
                "raw_dtype": c.raw_dtype,
                "missing_count": c.missing_count,
                "unique_count": c.unique_count,
                "sample_values": c.sample_values,
            }
            for c in d.columns
        ],
    })


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_dataset(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    saved_path, file_ext, file_size = validate_and_save_upload(file, settings.UPLOAD_DIR)
    try:
        df = load_dataframe(saved_path)
        profile = profile_dataframe(df)
    except Exception as exc:
        Path(saved_path).unlink(missing_ok=True)
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid dataset structure: {str(exc)}",
        )

    dataset_name = (name or Path(file.filename or "Uploaded Dataset").stem).strip()
    new_ds = Dataset(
        user_id=current_user.id,
        name=dataset_name,
        description=description or f"User-uploaded {file_ext.upper()} dataset ({profile['row_count']} rows)",
        file_path=saved_path,
        file_type=file_ext,
        file_size=file_size,
        row_count=profile["row_count"],
        column_count=profile["column_count"],
        source_type="user_upload",
        is_public=False,
        quality_score=profile["data_quality"]["overall_score"],
        profile_json=profile,
        processing_status="ready",
    )
    db.add(new_ds)
    db.flush()

    for col_meta in profile["columns"]:
        col_record = DatasetColumn(
            dataset_id=new_ds.id,
            column_name=col_meta["column_name"],
            data_type=col_meta["data_type"],
            raw_dtype=col_meta.get("raw_dtype"),
            missing_count=col_meta["missing_count"],
            unique_count=col_meta["unique_count"],
            sample_values=col_meta.get("sample_values", []),
        )
        db.add(col_record)

    db.commit()
    db.refresh(new_ds)

    log_activity(
        db,
        current_user.id,
        "DATASET_UPLOAD",
        f"Uploaded dataset '{new_ds.name}' ({new_ds.row_count} rows, {new_ds.column_count} columns)",
    )
    return serialize_dataset(new_ds)


@router.get("")
def list_datasets(
    search: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    file_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Dataset).filter(
        or_(Dataset.user_id == current_user.id, Dataset.is_public.is_(True))
    )
    if search:
        query = query.filter(Dataset.name.ilike(f"%{search.strip()}%"))
    if source_type and source_type != "all":
        query = query.filter(Dataset.source_type == source_type)
    if file_type and file_type != "all":
        query = query.filter(Dataset.file_type == file_type.lower())

    total = query.count()
    items = (
        query.order_by(Dataset.upload_timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "datasets": [serialize_dataset(d) for d in items],
    }


@router.get("/{dataset_id}")
def get_dataset_details(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ds = get_authorized_dataset(db, dataset_id, current_user)
    return serialize_dataset(ds)


@router.get("/{dataset_id}/preview")
def preview_dataset(
    dataset_id: int,
    limit: int = Query(50, ge=1, le=500),
    version: str = Query("active", description="active | original | processed"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ds = get_authorized_dataset(db, dataset_id, current_user)
    target_path = ds.file_path
    if version in ("active", "processed") and ds.processed_file_path and Path(ds.processed_file_path).exists():
        target_path = ds.processed_file_path

    df = load_dataframe(target_path)
    preview_df = df.head(limit).replace({np.nan: None})
    return sanitize_json({
        "dataset_id": ds.id,
        "name": ds.name,
        "version_shown": "processed" if target_path == ds.processed_file_path else "original",
        "total_rows": int(len(df)),
        "total_columns": int(len(df.columns)),
        "columns": [str(c) for c in df.columns],
        "rows": preview_df.to_dict(orient="records"),
    })


@router.get("/{dataset_id}/download")
def download_dataset(
    dataset_id: int,
    version: str = Query("active", description="active | original | processed"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ds = get_authorized_dataset(db, dataset_id, current_user)
    target_path = ds.file_path
    suffix = "original"
    if version in ("active", "processed") and ds.processed_file_path and Path(ds.processed_file_path).exists():
        target_path = ds.processed_file_path
        suffix = "cleaned"

    path_obj = Path(target_path)
    if not path_obj.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset file not found on disk.")

    download_name = f"{ds.name.replace(' ', '_')}_{suffix}{path_obj.suffix}"
    return FileResponse(
        path=str(path_obj),
        filename=download_name,
        media_type="application/octet-stream",
    )


@router.delete("/{dataset_id}")
def delete_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ds = get_authorized_dataset(db, dataset_id, current_user, require_owner=True)
    name = ds.name
    # Remove uploaded private file (never delete shared sample files in datasets/sample)
    if ds.source_type == "user_upload":
        Path(ds.file_path).unlink(missing_ok=True)
    if ds.processed_file_path:
        Path(ds.processed_file_path).unlink(missing_ok=True)

    db.delete(ds)
    db.commit()
    log_activity(db, current_user.id, "DATASET_DELETE", f"Deleted dataset '{name}' (ID #{dataset_id})")
    return {"status": "deleted", "dataset_id": dataset_id, "name": name}

