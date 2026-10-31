from pathlib import Path
from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.analytics.comparison_engine import run_location_comparison
from app.analytics.insights_engine import generate_intelligent_insights
from app.api.routes.datasets import get_authorized_dataset
from app.core.database import get_db
from app.core.security import get_current_user
from app.data_processing.profiler import load_dataframe
from app.models.dataset import Dataset
from app.models.prediction import MLModel
from app.models.user import User
from app.schemas.risk_report import InsightGenerateRequest
from app.utils.activity import log_activity

router = APIRouter(prefix="/api/insights", tags=["AI Insights"])


@router.post("/generate")
def generate_insights_endpoint(
    payload: InsightGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    df = None
    ds_name = "Urban Environmental Telemetry"

    if payload.dataset_id:
        ds = get_authorized_dataset(db, payload.dataset_id, current_user)
    else:
        ds = (
            db.query(Dataset)
            .filter(or_(Dataset.user_id == current_user.id, Dataset.is_public.is_(True)))
            .order_by(Dataset.upload_timestamp.desc())
            .first()
        )

    if ds:
        ds_name = ds.name
        target_path = (
            ds.processed_file_path
            if ds.processed_file_path and Path(ds.processed_file_path).exists()
            else ds.file_path
        )
        if Path(target_path).exists():
            df = load_dataframe(target_path)

    model_metrics = None
    if payload.model_id:
        m = db.query(MLModel).filter(MLModel.id == payload.model_id).first()
    else:
        m = (
            db.query(MLModel)
            .filter(or_(MLModel.user_id == current_user.id, MLModel.is_public == 1))
            .order_by(MLModel.created_at.desc())
            .first()
        )
    if m:
        model_metrics = m.metrics_json

    comp_data = None
    if payload.comparison_location_ids and len(payload.comparison_location_ids) >= 2:
        comp_data = run_location_comparison(db, payload.comparison_location_ids)

    result = generate_intelligent_insights(
        df=df,
        dataset_name=ds_name,
        model_metrics=model_metrics,
        comparison_data=comp_data,
    )

    log_activity(
        db,
        current_user.id,
        "INSIGHTS_GENERATE",
        f"Generated {result['total_insights']} evidence-backed urban intelligence insights",
    )
    return result

