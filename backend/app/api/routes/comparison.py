from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analytics.comparison_engine import run_location_comparison
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.location import ComparisonRunRequest
from app.utils.activity import log_activity

router = APIRouter(prefix="/api/comparison", tags=["Location Comparison"])


@router.post("/run")
def run_comparison_endpoint(
    payload: ComparisonRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = run_location_comparison(
        db=db,
        location_ids=payload.location_ids,
        indicators=payload.indicators,
    )
    log_activity(
        db,
        current_user.id,
        "LOCATION_COMPARISON",
        f"Compared {result['locations_compared']} urban localities across environmental indicators",
    )
    return result

