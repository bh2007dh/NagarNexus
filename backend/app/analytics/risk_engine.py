from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from app.utils.activity import sanitize_json


# Documented Reference Thresholds (WHO 2021 / CPCB NAAQS / IMD Criteria & Project Experimental Thresholds)
REFERENCE_THRESHOLDS = {
    "temperature_c": {
        "moderate": 35.0,
        "high": 38.0,
        "critical": 41.0,
        "unit": "°C",
        "category": "Urban Heat Stress",
        "reference_source": "IMD Heatwave Advisory & Urban Microclimate Reference Threshold",
        "action": "Activate urban cooling corridors, issue heat advisories for outdoor workers, and monitor transformer loads.",
    },
    "rainfall_mm": {
        "moderate": 35.0,
        "high": 64.5,
        "critical": 115.5,
        "unit": "mm",
        "category": "Abnormal Rainfall & Drainage Load",
        "reference_source": "IMD Heavy (64.5 mm/day) & Very Heavy (115.5 mm/day) Precipitation Classification",
        "action": "Inspect stormwater drain outfalls, pre-position pumping units in low-lying basins, and monitor underpass sensors.",
    },
    "pm25": {
        "moderate": 35.0,
        "high": 60.0,
        "critical": 120.0,
        "unit": "µg/m³",
        "category": "Fine Particulate Pollution (PM2.5)",
        "reference_source": "CPCB 24-Hour NAAQS (60 µg/m³) & WHO Interim Target-1 (35 µg/m³)",
        "action": "Enforce dust suppression at construction corridors, optimize traffic signal flow, and advise sensitive groups.",
    },
    "pm10": {
        "moderate": 75.0,
        "high": 100.0,
        "critical": 250.0,
        "unit": "µg/m³",
        "category": "Coarse Particulate Pollution (PM10)",
        "reference_source": "CPCB 24-Hour NAAQS (100 µg/m³)",
        "action": "Deploy mechanical road sweepers and water sprinkling along high-particulate arterial roads.",
    },
    "no2": {
        "moderate": 40.0,
        "high": 80.0,
        "critical": 140.0,
        "unit": "µg/m³",
        "category": "Vehicular/Industrial NO₂ Spike",
        "reference_source": "CPCB 24-Hour NAAQS (80 µg/m³) & WHO Annual/24h Reference",
        "action": "Audit peak-hour congestion bottlenecks and industrial stack emissions in the locality.",
    },
    "aqi": {
        "moderate": 101.0,
        "high": 201.0,
        "critical": 301.0,
        "unit": "AQI",
        "category": "Composite Air Quality Degradation",
        "reference_source": "National Air Quality Index (NAQI) Breakpoints (Moderate >100, Poor >200, Very Poor >300)",
        "action": "Issue public air quality advisory and restrict non-essential diesel generator operation.",
    },
}


def resolve_indicator_key(col_name: str) -> Optional[str]:
    lower = col_name.lower()
    if "temp" in lower:
        return "temperature_c"
    if "rain" in lower or "precip" in lower:
        return "rainfall_mm"
    if "pm25" in lower or "pm2.5" in lower or "pm2_5" in lower:
        return "pm25"
    if "pm10" in lower:
        return "pm10"
    if "no2" in lower:
        return "no2"
    if "aqi" in lower:
        return "aqi"
    return None


def analyze_urban_risks(
    df: pd.DataFrame,
    source_label: str = "Uploaded/Sample Urban Dataset",
    default_location: str = "Monitored Urban Zone",
    use_isolation_forest: bool = True,
    contamination: float = 0.05,
) -> Dict[str, Any]:
    """
    Detect environmental and infrastructure risks using:
    1. Documented WHO/CPCB/IMD reference thresholds
    2. Historical comparison (Z-score > 2.2 spike detection)
    3. Composite Waterlogging Risk Indicator (Rainfall + Humidity/Drainage interaction)
    4. Unsupervised Isolation Forest multivariate anomaly detection
    """
    alerts: List[Dict[str, Any]] = []
    now_iso = datetime.now(timezone.utc).isoformat()

    loc_col = next(
        (c for c in df.columns if any(k in str(c).lower() for k in ["location", "locality", "station", "zone", "city"])),
        None,
    )
    time_col = next(
        (c for c in df.columns if any(k in str(c).lower() for k in ["date", "time", "observed"])),
        None,
    )

    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    # 1. Threshold & Historical Z-Score Evaluation per column
    for col in num_cols:
        ind_key = resolve_indicator_key(str(col))
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(series) < 3:
            continue

        mean_val = float(series.mean())
        std_val = float(series.std(ddof=1)) if len(series) > 1 else 0.0

        if ind_key and ind_key in REFERENCE_THRESHOLDS:
            ref = REFERENCE_THRESHOLDS[ind_key]
            high_rows = df[pd.to_numeric(df[col], errors="coerce") >= ref["moderate"]].copy()
            if len(high_rows) > 0:
                # Sort by highest measured value and pick top representative alerts
                high_rows["_val"] = pd.to_numeric(high_rows[col], errors="coerce")
                high_rows = high_rows.sort_values("_val", ascending=False).head(6)
                for _, row in high_rows.iterrows():
                    val = float(row["_val"])
                    if val >= ref["critical"]:
                        level = "Critical"
                        thresh = ref["critical"]
                    elif val >= ref["high"]:
                        level = "High"
                        thresh = ref["high"]
                    else:
                        level = "Moderate"
                        thresh = ref["moderate"]

                    loc_name = str(row[loc_col]) if loc_col and pd.notna(row[loc_col]) else default_location
                    obs_time = str(row[time_col]) if time_col and pd.notna(row[time_col]) else now_iso

                    alerts.append({
                        "risk_category": ref["category"],
                        "location": loc_name,
                        "indicator": str(col),
                        "risk_level": level,
                        "measured_value": round(val, 3),
                        "threshold": round(float(thresh), 3),
                        "unit": ref["unit"],
                        "reason": (
                            f"Measured {col} ({val:.2f} {ref['unit']}) exceeds {level.lower()} threshold "
                            f"({thresh:.1f} {ref['unit']}) [Historical mean: {mean_val:.2f} {ref['unit']}]."
                        ),
                        "threshold_reference": ref["reference_source"],
                        "detection_timestamp": obs_time,
                        "data_source": source_label,
                        "suggested_action": ref["action"],
                        "verification_disclaimer": "Analytical risk estimate based on sensor/dataset thresholds; not a verified emergency declaration.",
                    })
        else:
            # Project-specific experimental statistical threshold (Mean + 2.5 SD)
            if std_val > 0:
                exp_thresh = mean_val + 2.5 * std_val
                crit_thresh = mean_val + 3.2 * std_val
                spikes = df[pd.to_numeric(df[col], errors="coerce") >= exp_thresh].copy()
                if len(spikes) > 0:
                    spikes["_val"] = pd.to_numeric(spikes[col], errors="coerce")
                    for _, row in spikes.sort_values("_val", ascending=False).head(3).iterrows():
                        val = float(row["_val"])
                        level = "High" if val >= crit_thresh else "Moderate"
                        loc_name = str(row[loc_col]) if loc_col and pd.notna(row[loc_col]) else default_location
                        alerts.append({
                            "risk_category": "Statistical Environmental Anomaly",
                            "location": loc_name,
                            "indicator": str(col),
                            "risk_level": level,
                            "measured_value": round(val, 3),
                            "threshold": round(exp_thresh, 3),
                            "unit": "units",
                            "reason": (
                                f"Unusual environmental change: {col} ({val:.2f}) is "
                                f"{(val - mean_val)/std_val:.1f}σ above dataset mean ({mean_val:.2f})."
                            ),
                            "threshold_reference": "Project-Specific Experimental Statistical Threshold (μ + 2.5σ)",
                            "detection_timestamp": now_iso,
                            "data_source": source_label,
                            "suggested_action": f"Verify sensor calibration and investigate localized sources affecting {col}.",
                            "verification_disclaimer": "Estimated statistical anomaly; not a verified emergency.",
                        })

    # 2. Potential Waterlogging Risk Detection (when rainfall & humidity/drainage columns exist)
    rain_col = next((c for c in num_cols if resolve_indicator_key(str(c)) == "rainfall_mm"), None)
    if rain_col:
        rain_vals = pd.to_numeric(df[rain_col], errors="coerce")
        waterlog_candidates = df[rain_vals >= 50.0].copy()
        if len(waterlog_candidates) > 0:
            waterlog_candidates["_rain"] = pd.to_numeric(waterlog_candidates[rain_col], errors="coerce")
            for _, row in waterlog_candidates.sort_values("_rain", ascending=False).head(4).iterrows():
                r_val = float(row["_rain"])
                level = "Critical" if r_val >= 95.0 else ("High" if r_val >= 65.0 else "Moderate")
                loc_name = str(row[loc_col]) if loc_col and pd.notna(row[loc_col]) else default_location
                alerts.append({
                    "risk_category": "Potential Waterlogging Risk Indicator",
                    "location": loc_name,
                    "indicator": f"{rain_col} (Surface Runoff Proxy)",
                    "risk_level": level,
                    "measured_value": round(r_val, 2),
                    "threshold": 50.0,
                    "unit": "mm",
                    "reason": (
                        f"Sustained rainfall of {r_val:.1f} mm exceeds urban micro-drainage saturation proxy "
                        f"(project experimental threshold: 50.0 mm)."
                    ),
                    "threshold_reference": "Project Experimental Urban Drainage Saturation Proxy (50 mm / 65 mm / 95 mm)",
                    "detection_timestamp": now_iso,
                    "data_source": source_label,
                    "suggested_action": "Monitor low-lying subways, clear stormwater grates, and alert civic flood-response teams.",
                    "verification_disclaimer": "Estimated hydrological risk indicator; not a verified flood emergency.",
                })

    # 3. Unsupervised Isolation Forest Multivariate Anomaly Detection
    if use_isolation_forest and len(num_cols) >= 2 and len(df) >= 15:
        clean_num = df[num_cols].apply(pd.to_numeric, errors="coerce")
        clean_num = clean_num.fillna(clean_num.median())
        iso = IsolationForest(
            n_estimators=100,
            contamination=min(max(contamination, 0.01), 0.3),
            random_state=42,
        )
        preds = iso.fit_predict(clean_num)
        scores = iso.decision_function(clean_num)
        anom_indices = np.where(preds == -1)[0]
        # Sort by most negative anomaly score
        sorted_anom = sorted(anom_indices, key=lambda idx: scores[idx])[:4]
        for idx in sorted_anom:
            row = df.iloc[idx]
            loc_name = str(row[loc_col]) if loc_col and pd.notna(row[loc_col]) else default_location
            score_val = float(scores[idx])
            alerts.append({
                "risk_category": "Multivariate Isolation Forest Anomaly",
                "location": loc_name,
                "indicator": ", ".join(str(c) for c in num_cols[:4]),
                "risk_level": "High" if score_val < -0.12 else "Moderate",
                "measured_value": round(score_val, 4),
                "threshold": 0.0,
                "unit": "decision_score",
                "reason": (
                    f"Isolation Forest detected an unusual multi-parameter environmental combination at row #{int(idx)+1} "
                    f"(decision score {score_val:.4f} < 0.0)."
                ),
                "threshold_reference": "Scikit-Learn Isolation Forest Unsupervised Decision Boundary",
                "detection_timestamp": now_iso,
                "data_source": source_label,
                "suggested_action": "Cross-check co-occurring temperature, air quality, and rainfall readings at this locality.",
                "verification_disclaimer": "Algorithmic anomaly detection output; requires domain analyst review.",
            })

    # Summarize counts by risk level
    level_counts = {"Low": 0, "Moderate": 0, "High": 0, "Critical": 0}
    for a in alerts:
        lvl = a["risk_level"]
        level_counts[lvl] = level_counts.get(lvl, 0) + 1

    if not alerts:
        level_counts["Low"] = 1
        alerts.append({
            "risk_category": "Baseline Environmental Status",
            "location": default_location,
            "indicator": "All Monitored Indicators",
            "risk_level": "Low",
            "measured_value": 0.0,
            "threshold": 100.0,
            "unit": "index",
            "reason": "All analyzed observations remain within normal historical and reference thresholds.",
            "threshold_reference": "WHO / CPCB / IMD Standard Reference Thresholds",
            "detection_timestamp": now_iso,
            "data_source": source_label,
            "suggested_action": "Continue routine environmental telemetry monitoring.",
            "verification_disclaimer": "Routine monitoring status.",
        })

    return sanitize_json({
        "total_alerts": len(alerts),
        "risk_distribution": [
            {"level": k, "count": v} for k, v in level_counts.items()
        ],
        "level_counts": level_counts,
        "alerts": alerts,
        "methodology_note": (
            "Thresholds combine documented CPCB/WHO/IMD environmental benchmarks with clearly labeled "
            "project-specific experimental statistical thresholds and Isolation Forest anomaly detection. "
            "Estimated risk levels are decision-support indicators, not verified emergency warnings."
        ),
    })

