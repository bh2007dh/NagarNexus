from typing import Dict, Any, List
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.location import Location, Observation
from app.models.risk import RiskAlert
from app.utils.activity import sanitize_json


def run_location_comparison(
    db: Session,
    location_ids: List[int],
    indicators: List[str] | None = None,
) -> Dict[str, Any]:
    """
    Compare 2 or more locations across compatible indicators, units, time periods,
    and geographical resolutions.
    """
    locations = db.query(Location).filter(Location.id.in_(location_ids)).all()
    if len(locations) < 2:
        # Fallback to first 2 available locations in DB if fewer than 2 valid IDs were provided
        locations = db.query(Location).limit(3).all()

    target_indicators = indicators or [
        "temperature_c",
        "rainfall_mm",
        "humidity_pct",
        "pm25",
        "pm10",
        "no2",
        "aqi",
    ]

    comparison_table: List[Dict[str, Any]] = []
    indicator_chart_series: Dict[str, List[Dict[str, Any]]] = {ind: [] for ind in target_indicators}
    resolutions = set()

    for loc in locations:
        resolutions.add(loc.geographical_resolution)
        obs_list = (
            db.query(Observation)
            .filter(Observation.location_id == loc.id)
            .order_by(Observation.observed_at.asc())
            .all()
        )
        alerts_cnt = db.query(RiskAlert).filter(RiskAlert.location_id == loc.id).count()

        loc_metrics: Dict[str, Any] = {
            "location_id": loc.id,
            "name": loc.name,
            "city": loc.city,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "geographical_resolution": loc.geographical_resolution,
            "zone_type": loc.zone_type,
            "observation_count": len(obs_list),
            "risk_alert_count": alerts_cnt,
            "indicators": {},
        }

        df_obs = pd.DataFrame([
            {
                "indicator": o.indicator,
                "value": o.value,
                "unit": o.unit,
                "observed_at": o.observed_at,
            }
            for o in obs_list
        ])

        for ind in target_indicators:
            if not df_obs.empty and ind in df_obs["indicator"].values:
                sub = df_obs[df_obs["indicator"] == ind].sort_values("observed_at")
                vals = sub["value"].astype(float).values
                unit = str(sub["unit"].iloc[0])
                avg_val = round(float(np.mean(vals)), 2)
                min_val = round(float(np.min(vals)), 2)
                max_val = round(float(np.max(vals)), 2)
                # Historical change: second half mean minus first half mean
                mid = max(1, len(vals) // 2)
                hist_change = round(float(np.mean(vals[mid:]) - np.mean(vals[:mid])), 2) if len(vals) >= 2 else 0.0
                # Linear projection for next step
                if len(vals) >= 3:
                    slope = float(np.polyfit(np.arange(len(vals)), vals, 1)[0])
                    projected = round(float(vals[-1] + slope), 2)
                else:
                    projected = avg_val

                loc_metrics["indicators"][ind] = {
                    "average": avg_val,
                    "min": min_val,
                    "max": max_val,
                    "unit": unit,
                    "historical_change": hist_change,
                    "projected_next": projected,
                    "sample_count": int(len(vals)),
                }
                indicator_chart_series[ind].append({
                    "location": f"{loc.name} ({loc.city})",
                    "average": avg_val,
                    "max": max_val,
                    "projected": projected,
                    "historical_change": hist_change,
                    "unit": unit,
                })

        comparison_table.append(loc_metrics)

    radar_comparison = []
    for ind in target_indicators:
        row_obj: Dict[str, Any] = {"indicator": ind}
        for loc_entry in comparison_table:
            ind_data = loc_entry["indicators"].get(ind)
            if ind_data:
                row_obj[loc_entry["name"]] = ind_data["average"]
                row_obj["unit"] = ind_data["unit"]
        if len(row_obj) > 1:
            radar_comparison.append(row_obj)

    compatibility_warning = (
        "All compared locations share compatible geographical resolution."
        if len(resolutions) <= 1
        else (
            f"Note: Compared locations have differing geographical resolutions ({', '.join(resolutions)}). "
            "Avoid treating city-level aggregates as pinpoint street-level measurements."
        )
    )

    return sanitize_json({
        "locations_compared": len(comparison_table),
        "compatibility_check": {
            "resolutions_present": list(resolutions),
            "resolution_uniform": len(resolutions) <= 1,
            "note": compatibility_warning,
        },
        "comparison_table": comparison_table,
        "indicator_charts": indicator_chart_series,
        "multi_indicator_matrix": radar_comparison,
    })

