from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.analytics.eda_engine import run_automated_eda, generate_eda_visualization
from app.analytics.statistics_engine import perform_statistical_analysis
from app.api.routes.datasets import get_authorized_dataset
from app.core.database import get_db
from app.core.security import get_current_user
from app.data_processing.cleaner import execute_data_cleaning
from app.data_processing.profiler import load_dataframe, profile_dataframe
from app.models.analysis import Analysis
from app.models.dataset import Dataset
from app.models.user import User
from app.schemas.analysis import (
    CleaningOperationRequest,
    EDAVisualizationRequest,
    StatisticalCalculationRequest,
)
from app.utils.activity import log_activity

router = APIRouter(tags=["Data Cleaning, EDA & Statistics"])


def _get_active_dataframe(ds: Dataset):
    """Load the processed file if available, otherwise load the original uploaded file."""
    if ds.processed_file_path and Path(ds.processed_file_path).exists():
        return load_dataframe(ds.processed_file_path)
    return load_dataframe(ds.file_path)


# --- DATA CLEANING ROUTES ---

@router.get("/api/analysis/{dataset_id}/quality")
def get_dataset_quality(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ds = get_authorized_dataset(db, dataset_id, current_user)
    df = _get_active_dataframe(ds)
    profile = profile_dataframe(df)
    return {
        "dataset_id": ds.id,
        "dataset_name": ds.name,
        "has_processed_version": bool(ds.processed_file_path and Path(ds.processed_file_path).exists()),
        "profile": profile,
    }


@router.post("/api/analysis/{dataset_id}/clean")
def clean_dataset(
    dataset_id: int,
    payload: CleaningOperationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ds = get_authorized_dataset(db, dataset_id, current_user)
    # Always start from original file or current active file without altering original file on disk
    df = load_dataframe(ds.file_path)
    cleaning_result = execute_data_cleaning(df, ds.name, payload)

    ds.processed_file_path = cleaning_result["processed_file_path"]
    ds.quality_score = cleaning_result["after_profile"]["data_quality"]["overall_score"]
    ds.processing_status = "cleaned"

    analysis_rec = Analysis(
        user_id=current_user.id,
        dataset_id=ds.id,
        analysis_type="cleaning",
        result_json=cleaning_result,
    )
    db.add(analysis_rec)
    db.commit()

    log_activity(
        db,
        current_user.id,
        "DATA_CLEANING",
        f"Cleaned dataset '{ds.name}' (Quality: {cleaning_result['comparison']['quality_score_before']} -> {cleaning_result['comparison']['quality_score_after']})",
    )
    return cleaning_result


# --- EXPLORATORY DATA ANALYSIS (EDA) ROUTES ---

@router.post("/api/eda/{dataset_id}/run")
def run_eda_endpoint(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ds = get_authorized_dataset(db, dataset_id, current_user)
    df = _get_active_dataframe(ds)
    eda_results = run_automated_eda(df)

    analysis_rec = Analysis(
        user_id=current_user.id,
        dataset_id=ds.id,
        analysis_type="eda",
        result_json=eda_results,
    )
    db.add(analysis_rec)
    db.commit()

    log_activity(db, current_user.id, "EDA_RUN", f"Executed Automated EDA on dataset '{ds.name}'")
    return {
        "dataset_id": ds.id,
        "dataset_name": ds.name,
        "eda": eda_results,
    }


@router.get("/api/eda/{dataset_id}/results")
def get_eda_results_endpoint(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ds = get_authorized_dataset(db, dataset_id, current_user)
    latest = (
        db.query(Analysis)
        .filter(Analysis.dataset_id == ds.id, Analysis.analysis_type == "eda")
        .order_by(Analysis.created_at.desc())
        .first()
    )
    if latest:
        return {
            "dataset_id": ds.id,
            "dataset_name": ds.name,
            "eda": latest.result_json,
            "cached": True,
        }
    df = _get_active_dataframe(ds)
    eda_results = run_automated_eda(df)
    return {
        "dataset_id": ds.id,
        "dataset_name": ds.name,
        "eda": eda_results,
        "cached": False,
    }


@router.post("/api/eda/{dataset_id}/visualization")
def generate_eda_chart_endpoint(
    dataset_id: int,
    payload: EDAVisualizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ds = get_authorized_dataset(db, dataset_id, current_user)
    df = _get_active_dataframe(ds)
    chart_result = generate_eda_visualization(df, payload)
    return chart_result


# --- STATISTICAL ANALYSIS ROUTES ---

@router.post("/api/statistics/{dataset_id}/calculate")
def calculate_statistics_endpoint(
    dataset_id: int,
    payload: StatisticalCalculationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ds = get_authorized_dataset(db, dataset_id, current_user)
    df = _get_active_dataframe(ds)
    try:
        stats_res = perform_statistical_analysis(df, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    analysis_rec = Analysis(
        user_id=current_user.id,
        dataset_id=ds.id,
        analysis_type="statistics",
        result_json=stats_res,
    )
    db.add(analysis_rec)
    db.commit()

    log_activity(
        db,
        current_user.id,
        "STATISTICS_CALC",
        f"Ran statistical analysis on '{payload.target_column}' in dataset '{ds.name}'",
    )
    return {
        "dataset_id": ds.id,
        "dataset_name": ds.name,
        "results": stats_res,
    }

