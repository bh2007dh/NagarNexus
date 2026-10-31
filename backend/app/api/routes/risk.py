from pathlib import Path
from typing import Optional
import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.analytics.risk_engine import analyze_urban_risks
from app.api.routes.datasets import get_authorized_dataset
from app.core.database import get_db
from app.core.security import get_current_user
from app.data_processing.profiler import load_dataframe
from app.models.location import Location, Observation
from app.models.risk import RiskAlert
from app.models.user import User
from app.schemas.risk_report import RiskAnalyzeRequest
from app.utils.activity import log_activity, sanitize_json

router = APIRouter(prefix="/api/risk", tags=["Urban Risk Detection"])


@router.post("/analyze")
def run_risk_analysis_endpoint(
    payload: RiskAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    df = None
    source_label = "NagarNexus Stored Urban Observations"
    default_loc_name = "Monitored Urban Zone"

    if payload.dataset_id:
        ds = get_authorized_dataset(db, payload.dataset_id, current_user)
        target_path = (
            ds.processed_file_path
            if ds.processed_file_path and Path(ds.processed_file_path).exists()
            else ds.file_path
        )
        df = load_dataframe(target_path)
        source_label = f"Dataset: {ds.name} ({ds.source_type})"

    if df is None and payload.location_id:
        loc = db.query(Location).filter(Location.id == payload.location_id).first()
        if loc:
            default_loc_name = f"{loc.name} ({loc.city})"
            obs = db.query(Observation).filter(Observation.location_id == loc.id).all()
            if obs:
                pivoted = {}
                for o in obs:
                    ts = o.observed_at.strftime("%Y-%m-%d") if hasattr(o.observed_at, "strftime") else str(o.observed_at)[:10]
                    pivoted.setdefault(ts, {"observed_at": ts, "location": default_loc_name})[o.indicator] = o.value
                df = pd.DataFrame(list(pivoted.values()))
                source_label = f"Telemetry Station: {default_loc_name}"

    if df is None or df.empty:
        # Fallback: build DataFrame from all stored observations in DB
        obs = db.query(Observation).limit(500).all()
        rows = []
        for o in obs:
            rows.append({
                "observed_at": o.observed_at.isoformat() if hasattr(o.observed_at, "isoformat") else str(o.observed_at),
                "location_id": o.location_id,
                o.indicator: o.value,
            })
        df = pd.DataFrame(rows) if rows else pd.DataFrame({"temperature_c": [32.0, 34.5, 36.2], "pm25": [42.0, 58.0, 72.0]})

    result = analyze_urban_risks(
        df=df,
        source_label=source_label,
        default_location=default_loc_name,
        use_isolation_forest=payload.use_isolation_forest,
        contamination=payload.contamination,
    )

    # Persist top alerts to RISK_ALERTS table
    for alert in result.get("alerts", [])[:8]:
        rec = RiskAlert(
            location_id=payload.location_id,
            dataset_id=payload.dataset_id,
            risk_category=alert["risk_category"],
            indicator=alert["indicator"],
            risk_level=alert["risk_level"],
            measured_value=float(alert["measured_value"]),
            threshold=float(alert["threshold"]),
            unit=alert.get("unit", ""),
            explanation=alert["reason"],
            suggested_action=alert.get("suggested_action"),
            data_source=alert.get("data_source", source_label),
            threshold_type=alert.get("threshold_reference"),
        )
        db.add(rec)
    db.commit()

    log_activity(
        db,
        current_user.id,
        "RISK_ANALYZE",
        f"Executed Urban Risk Detection ({result['total_alerts']} alerts generated)",
    )
    return result


@router.get("/alerts")
def get_risk_alerts_endpoint(
    risk_level: Optional[str] = Query(None),
    location_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(RiskAlert)
    if risk_level and risk_level != "all":
        q = q.filter(RiskAlert.risk_level == risk_level)
    if location_id:
        q = q.filter(RiskAlert.location_id == location_id)

    alerts = q.order_by(RiskAlert.created_at.desc()).limit(limit).all()
    loc_map = {loc.id: f"{loc.name} ({loc.city})" for loc in db.query(Location).all()}

    level_counts = {"Low": 0, "Moderate": 0, "High": 0, "Critical": 0}
    serialized = []
    for a in alerts:
        level_counts[a.risk_level] = level_counts.get(a.risk_level, 0) + 1
        serialized.append({
            "id": a.id,
            "risk_category": a.risk_category,
            "location": loc_map.get(a.location_id, "Monitored Urban Zone"),
            "location_id": a.location_id,
            "indicator": a.indicator,
            "risk_level": a.risk_level,
            "measured_value": round(float(a.measured_value), 3),
            "threshold": round(float(a.threshold), 3),
            "unit": a.unit,
            "reason": a.explanation,
            "suggested_action": a.suggested_action,
            "data_source": a.data_source,
            "threshold_reference": a.threshold_type,
            "detection_timestamp": a.created_at.isoformat() if a.created_at else None,
        })

    return sanitize_json({
        "total": len(serialized),
        "level_counts": level_counts,
        "risk_distribution": [{"level": k, "count": v} for k, v in level_counts.items()],
        "alerts": serialized,
    })

