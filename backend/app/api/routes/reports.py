from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.analytics.eda_engine import run_automated_eda
from app.analytics.insights_engine import generate_intelligent_insights
from app.analytics.risk_engine import analyze_urban_risks
from app.api.routes.datasets import get_authorized_dataset, serialize_dataset
from app.api.routes.predictions import serialize_ml_model
from app.core.database import get_db
from app.core.security import get_current_user
from app.data_processing.profiler import load_dataframe
from app.models.dataset import Dataset
from app.models.prediction import MLModel, Prediction
from app.models.report import Report
from app.models.user import User
from app.schemas.risk_report import ReportGenerateRequest
from app.services.report_generator import generate_analytical_report
from app.utils.activity import log_activity, sanitize_json

router = APIRouter(prefix="/api/reports", tags=["Report Center"])


def serialize_report(r: Report) -> dict:
    return sanitize_json({
        "id": r.id,
        "user_id": r.user_id,
        "dataset_id": r.dataset_id,
        "title": r.title,
        "report_type": r.report_type,
        "has_csv": bool(r.csv_file_path and Path(r.csv_file_path).exists()),
        "summary_json": r.summary_json,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    })


@router.post("/generate", status_code=status.HTTP_201_CREATED)
def generate_report_endpoint(
    payload: ReportGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ds = None
    df = None
    ds_meta = None
    eda_summary = None
    risk_summary = None
    insights_summary = None

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
        ds_meta = serialize_dataset(ds)
        target_path = (
            ds.processed_file_path
            if ds.processed_file_path and Path(ds.processed_file_path).exists()
            else ds.file_path
        )
        if Path(target_path).exists():
            df = load_dataframe(target_path)
            eda_summary = run_automated_eda(df)
            risk_summary = analyze_urban_risks(df, source_label=ds.name)
            insights_summary = generate_intelligent_insights(df=df, dataset_name=ds.name)

    ml_meta = None
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
        ml_meta = serialize_ml_model(m)

    preds = (
        db.query(Prediction)
        .filter(or_(Prediction.user_id == current_user.id, Prediction.user_id.is_(None)))
        .order_by(Prediction.created_at.desc())
        .limit(5)
        .all()
    )
    preds_list = [
        {
            "category": p.category,
            "predicted_value": p.predicted_value,
            "created_at": p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "",
        }
        for p in preds
    ]

    generated = generate_analytical_report(
        title=payload.title,
        report_type=payload.report_type,
        dataset_meta=ds_meta,
        df=df,
        eda_summary=eda_summary,
        ml_model_meta=ml_meta,
        predictions_list=preds_list,
        risk_summary=risk_summary,
        insights_summary=insights_summary,
        notes=payload.notes,
    )

    rep_rec = Report(
        user_id=current_user.id,
        dataset_id=ds.id if ds else None,
        title=payload.title,
        report_type=payload.report_type,
        file_path=generated["pdf_path"],
        csv_file_path=generated["csv_path"],
        summary_json={
            "report_uid": generated["report_uid"],
            "generated_at": generated["generated_at"],
            "dataset_name": ds.name if ds else "System Aggregate",
            "model_name": ml_meta["model_name"] if ml_meta else "N/A",
            "total_alerts": risk_summary["total_alerts"] if risk_summary else 0,
        },
    )
    db.add(rep_rec)
    db.commit()
    db.refresh(rep_rec)

    log_activity(
        db,
        current_user.id,
        "REPORT_GENERATE",
        f"Generated {payload.report_type.upper()} report '{payload.title}' ({generated['report_uid']})",
    )
    return serialize_report(rep_rec)


@router.get("")
def list_reports_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reports = (
        db.query(Report)
        .filter(Report.user_id == current_user.id)
        .order_by(Report.created_at.desc())
        .all()
    )
    return {"reports": [serialize_report(r) for r in reports]}


@router.get("/{report_id}/download")
def download_report_endpoint(
    report_id: int,
    format: str = Query("pdf", description="pdf | csv"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rep = db.query(Report).filter(Report.id == report_id).first()
    if not rep:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    if rep.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only download your own private reports.",
        )

    if format.lower() == "csv":
        if not rep.csv_file_path or not Path(rep.csv_file_path).exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CSV export not found.")
        return FileResponse(
            path=rep.csv_file_path,
            filename=Path(rep.csv_file_path).name,
            media_type="text/csv",
        )

    if not Path(rep.file_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF file not found on disk.")
    return FileResponse(
        path=rep.file_path,
        filename=Path(rep.file_path).name,
        media_type="application/pdf",
    )

