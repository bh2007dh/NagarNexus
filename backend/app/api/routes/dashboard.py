from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, ActivityLog
from app.models.dataset import Dataset
from app.models.location import Location, Observation
from app.models.prediction import MLModel, Prediction
from app.models.risk import RiskAlert
from app.utils.activity import sanitize_json

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary")
def get_dashboard_summary(
    location_id: Optional[int] = Query(None),
    dataset_id: Optional[int] = Query(None),
    indicator: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Datasets visible to current user (their own + public sample datasets)
    visible_datasets = (
        db.query(Dataset)
        .filter(or_(Dataset.user_id == current_user.id, Dataset.is_public.is_(True)))
        .all()
    )
    if dataset_id:
        filtered_datasets = [d for d in visible_datasets if d.id == dataset_id]
    else:
        filtered_datasets = visible_datasets

    total_datasets = len(filtered_datasets)
    total_records = sum(int(d.row_count or 0) for d in filtered_datasets)
    total_locations = db.query(Location).count()
    total_predictions = (
        db.query(Prediction)
        .filter(or_(Prediction.user_id == current_user.id, Prediction.user_id.is_(None)))
        .count()
    )

    alert_query = db.query(RiskAlert)
    if location_id:
        alert_query = alert_query.filter(RiskAlert.location_id == location_id)
    if dataset_id:
        alert_query = alert_query.filter(RiskAlert.dataset_id == dataset_id)
    alerts = alert_query.order_by(RiskAlert.created_at.desc()).all()

    total_anomalies = len(alerts)
    high_risk_count = sum(1 for a in alerts if a.risk_level in ("High", "Critical"))

    # Observations query for dashboard trend charts
    obs_query = db.query(Observation)
    if location_id:
        obs_query = obs_query.filter(Observation.location_id == location_id)
    if dataset_id:
        obs_query = obs_query.filter(Observation.dataset_id == dataset_id)
    if indicator:
        obs_query = obs_query.filter(Observation.indicator == indicator)
    if start_date:
        obs_query = obs_query.filter(Observation.observed_at >= start_date)
    if end_date:
        obs_query = obs_query.filter(Observation.observed_at <= end_date)

    observations = obs_query.order_by(Observation.observed_at.asc()).limit(500).all()

    def build_trend(ind_name: str):
        pts = [o for o in observations if o.indicator == ind_name]
        return [
            {
                "timestamp": o.observed_at.strftime("%Y-%m-%d") if hasattr(o.observed_at, "strftime") else str(o.observed_at)[:10],
                "value": round(float(o.value), 2),
                "unit": o.unit,
                "location_id": o.location_id,
            }
            for o in pts[-30:]
        ]

    temperature_trend = build_trend("temperature_c")
    rainfall_trend = build_trend("rainfall_mm")
    air_quality_trend = build_trend("pm25") or build_trend("aqi")

    # Environmental comparison across locations
    locations = db.query(Location).limit(8).all()
    env_comparison = []
    for loc in locations:
        loc_obs = db.query(Observation).filter(Observation.location_id == loc.id).all()
        if not loc_obs:
            continue
        by_ind = {}
        for o in loc_obs:
            by_ind.setdefault(o.indicator, []).append(float(o.value))
        env_comparison.append({
            "location": loc.name,
            "city": loc.city,
            "temperature_c": round(sum(by_ind.get("temperature_c", [0])) / max(len(by_ind.get("temperature_c", [1])), 1), 2),
            "rainfall_mm": round(sum(by_ind.get("rainfall_mm", [0])) / max(len(by_ind.get("rainfall_mm", [1])), 1), 2),
            "pm25": round(sum(by_ind.get("pm25", [0])) / max(len(by_ind.get("pm25", [1])), 1), 2),
            "aqi": round(sum(by_ind.get("aqi", [0])) / max(len(by_ind.get("aqi", [1])), 1), 2),
        })

    # Risk distribution
    risk_counts = {"Low": 0, "Moderate": 0, "High": 0, "Critical": 0}
    for a in alerts:
        risk_counts[a.risk_level] = risk_counts.get(a.risk_level, 0) + 1
    risk_distribution = [{"level": k, "count": v} for k, v in risk_counts.items()]

    # Dataset analysis statistics
    dataset_stats = [
        {
            "id": d.id,
            "name": d.name,
            "rows": d.row_count,
            "columns": d.column_count,
            "quality_score": round(float(d.quality_score or 100.0), 1),
            "source_type": d.source_type,
        }
        for d in filtered_datasets[:10]
    ]

    # Latest predictions
    recent_preds = (
        db.query(Prediction)
        .filter(or_(Prediction.user_id == current_user.id, Prediction.user_id.is_(None)))
        .order_by(Prediction.created_at.desc())
        .limit(6)
        .all()
    )
    latest_predictions = []
    for p in recent_preds:
        model_obj = db.query(MLModel).filter(MLModel.id == p.model_id).first()
        latest_predictions.append({
            "id": p.id,
            "model_name": model_obj.model_name if model_obj else f"Model #{p.model_id}",
            "category": p.category,
            "predicted_value": p.predicted_value,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })

    return sanitize_json({
        "kpis": {
            "total_uploaded_datasets": total_datasets,
            "total_records_analyzed": total_records,
            "total_locations_monitored": total_locations,
            "total_predictions_generated": total_predictions,
            "total_detected_anomalies": total_anomalies,
            "high_risk_observations": high_risk_count,
        },
        "charts": {
            "temperature_trend": temperature_trend,
            "rainfall_trend": rainfall_trend,
            "air_quality_trend": air_quality_trend,
            "environmental_comparison": env_comparison,
            "risk_distribution": risk_distribution,
            "dataset_statistics": dataset_stats,
        },
        "latest_predictions": latest_predictions,
        "available_filters": {
            "locations": [{"id": loc.id, "name": f"{loc.name} ({loc.city})"} for loc in locations],
            "datasets": [{"id": d.id, "name": d.name} for d in visible_datasets],
            "indicators": ["temperature_c", "rainfall_mm", "humidity_pct", "pm25", "pm10", "no2", "aqi"],
        },
    })


@router.get("/recent-activity")
def get_recent_activity(
    limit: int = Query(15, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logs = (
        db.query(ActivityLog)
        .filter(or_(ActivityLog.user_id == current_user.id, ActivityLog.user_id.is_(None)))
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "activities": [
            {
                "id": log.id,
                "activity_type": log.activity_type,
                "description": log.description,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
    }

