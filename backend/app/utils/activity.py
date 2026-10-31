from typing import Optional, Any
import math
import numpy as np
from sqlalchemy.orm import Session
from app.models.user import ActivityLog


def log_activity(
    db: Session,
    user_id: Optional[int],
    activity_type: str,
    description: str,
) -> None:
    """Record an user/system activity log entry."""
    try:
        entry = ActivityLog(
            user_id=user_id,
            activity_type=activity_type,
            description=description,
        )
        db.add(entry)
        db.commit()
    except Exception:
        db.rollback()


def sanitize_json(obj: Any) -> Any:
    """Recursively convert NaN, Inf, numpy scalars, and timestamps into JSON-safe Python primitives."""
    if obj is None:
        return None
    if isinstance(obj, (bool, str)):
        return obj
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        val = float(obj)
        if math.isnan(val) or math.isinf(val):
            return None
        return round(val, 6)
    if isinstance(obj, np.ndarray):
        return sanitize_json(obj.tolist())
    if isinstance(obj, dict):
        return {str(k): sanitize_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [sanitize_json(item) for item in obj]
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return str(obj)

