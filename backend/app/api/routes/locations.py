from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.integrations.external_apis import (
    fetch_open_meteo_weather,
    fetch_openaq_air_quality,
    geocode_nominatim,
)
from app.models.location import Location, Observation, DataSource
from app.models.risk import RiskAlert
from app.models.user import User
from app.schemas.location import LocationCreateRequest
from app.utils.activity import log_activity, sanitize_json

router = APIRouter(prefix="/api/locations", tags=["Location Intelligence"])


def serialize_location(loc: Location) -> dict:
    return {
        "id": loc.id,
        "name": loc.name,
        "city": loc.city,
        "state": loc.state,
        "country": loc.country,
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "geographical_resolution": loc.geographical_resolution,
        "elevation_m": loc.elevation_m,
        "zone_type": loc.zone_type,
        "created_at": loc.created_at.isoformat() if loc.created_at else None,
    }


@router.get("/search")
def search_locations(
    q: Optional[str] = Query(None, description="Search city or locality name"),
    city: Optional[str] = Query(None),
    include_external_geocoding: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Location)
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(or_(Location.name.ilike(term), Location.city.ilike(term), Location.zone_type.ilike(term)))
    if city:
        query = query.filter(Location.city.ilike(f"%{city.strip()}%"))

    locations = query.order_by(Location.city.asc(), Location.name.asc()).all()
    external_matches = []
    if include_external_geocoding and q and len(q.strip()) >= 3:
        external_matches = geocode_nominatim(q.strip())

    return sanitize_json({
        "locations": [serialize_location(loc) for loc in locations],
        "external_geocoding_results": external_matches,
        "attribution": "Map data © OpenStreetMap contributors (ODbL)",
    })


@router.post("", status_code=status.HTTP_201_CREATED)
def create_custom_location(
    payload: LocationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_loc = Location(
        name=payload.name.strip(),
        city=payload.city.strip(),
        state=payload.state or "Tamil Nadu",
        country=payload.country or "India",
        latitude=payload.latitude,
        longitude=payload.longitude,
        geographical_resolution=payload.geographical_resolution or "coordinate_pin",
        zone_type=payload.zone_type or "Custom Monitored Coordinate",
    )
    db.add(new_loc)
    db.commit()
    db.refresh(new_loc)
    log_activity(db, current_user.id, "LOCATION_CREATE", f"Added monitored location '{new_loc.name}' ({new_loc.city})")
    return serialize_location(new_loc)


@router.get("/{location_id}")
def get_location_details(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found.")

    observations = (
        db.query(Observation)
        .filter(Observation.location_id == loc.id)
        .order_by(Observation.observed_at.desc())
        .all()
    )

    latest_by_indicator = {}
    trends_by_indicator = {}
    source_ids = set()

    for o in reversed(observations):
        if o.source_id:
            source_ids.add(o.source_id)
        trends_by_indicator.setdefault(o.indicator, []).append({
            "timestamp": o.observed_at.strftime("%Y-%m-%d") if hasattr(o.observed_at, "strftime") else str(o.observed_at)[:10],
            "value": round(float(o.value), 2),
            "unit": o.unit,
        })
        latest_by_indicator[o.indicator] = {
            "value": round(float(o.value), 2),
            "unit": o.unit,
            "observed_at": o.observed_at.isoformat() if hasattr(o.observed_at, "isoformat") else str(o.observed_at),
        }

    sources = db.query(DataSource).filter(DataSource.id.in_(list(source_ids))).all() if source_ids else []
    alerts = (
        db.query(RiskAlert)
        .filter(RiskAlert.location_id == loc.id)
        .order_by(RiskAlert.created_at.desc())
        .limit(10)
        .all()
    )

    return sanitize_json({
        "location": serialize_location(loc),
        "latest_measurements": latest_by_indicator,
        "historical_trends": trends_by_indicator,
        "risk_indicators": [
            {
                "id": a.id,
                "risk_category": a.risk_category,
                "indicator": a.indicator,
                "risk_level": a.risk_level,
                "measured_value": a.measured_value,
                "threshold": a.threshold,
                "unit": a.unit,
                "explanation": a.explanation,
                "suggested_action": a.suggested_action,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alerts
        ],
        "sources": [
            {
                "source_name": s.source_name,
                "source_url": s.source_url,
                "source_type": s.source_type,
                "retrieved_at": s.retrieved_at.isoformat() if s.retrieved_at else None,
                "attribution": s.attribution,
            }
            for s in sources
        ],
        "resolution_notice": (
            f"Geographical Resolution: {loc.geographical_resolution}. "
            "Measurements represent spatial resolution of the underlying station or reanalysis grid cell."
        ),
    })


@router.get("/{location_id}/observations")
def get_location_observations(
    location_id: int,
    indicator: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found.")

    q = db.query(Observation).filter(Observation.location_id == loc.id)
    if indicator:
        q = q.filter(Observation.indicator == indicator)

    items = q.order_by(Observation.observed_at.asc()).limit(limit).all()
    return sanitize_json({
        "location": serialize_location(loc),
        "count": len(items),
        "observations": [
            {
                "id": o.id,
                "indicator": o.indicator,
                "value": round(float(o.value), 3),
                "unit": o.unit,
                "observed_at": o.observed_at.isoformat() if hasattr(o.observed_at, "isoformat") else str(o.observed_at),
            }
            for o in items
        ],
    })


@router.post("/{location_id}/live-weather")
def fetch_live_location_telemetry(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found.")

    weather = fetch_open_meteo_weather(loc.latitude, loc.longitude)
    air_quality = fetch_openaq_air_quality(loc.latitude, loc.longitude)
    return sanitize_json({
        "location": serialize_location(loc),
        "open_meteo": weather,
        "openaq": air_quality,
    })

