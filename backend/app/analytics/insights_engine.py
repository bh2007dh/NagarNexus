from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from app.analytics.risk_engine import analyze_urban_risks
from app.utils.activity import sanitize_json


def generate_intelligent_insights(
    df: Optional[pd.DataFrame] = None,
    dataset_name: str = "Urban Environmental Dataset",
    model_metrics: Optional[Dict[str, Any]] = None,
    comparison_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Evidence-backed Intelligent Insight & Recommendation Engine.
    Synthesizes real outputs from statistical trends, correlations, ML models,
    risk detection, and location comparisons.
    """
    insights: List[Dict[str, Any]] = []
    recommendations: List[Dict[str, Any]] = []

    if df is not None and not df.empty:
        num_df = df.select_dtypes(include=[np.number])

        # 1. Temporal / Period Change Insights
        for col in num_df.columns:
            s = num_df[col].dropna()
            if len(s) < 6:
                continue
            mid = len(s) // 2
            first_half_mean = float(s.iloc[:mid].mean())
            second_half_mean = float(s.iloc[mid:].mean())
            delta = second_half_mean - first_half_mean
            pct_change = (delta / max(abs(first_half_mean), 1e-6)) * 100.0

            if abs(pct_change) >= 5.0:
                direction = "increased" if delta > 0 else "decreased"
                insights.append({
                    "category": "Statistical Period Trend",
                    "headline": f"The average {col} {direction} by {abs(pct_change):.1f}% compared with the earlier observation period.",
                    "explanation": (
                        f"In {dataset_name}, {col} shifted from a mean of {first_half_mean:.2f} in the first half "
                        f"({mid} observations) to {second_half_mean:.2f} in the recent half ({len(s) - mid} observations)."
                    ),
                    "evidence": {
                        "indicator": str(col),
                        "previous_period_mean": round(first_half_mean, 3),
                        "recent_period_mean": round(second_half_mean, 3),
                        "absolute_change": round(delta, 3),
                        "percent_change": round(pct_change, 2),
                        "sample_size": int(len(s)),
                    },
                    "confidence": "High" if len(s) >= 30 else "Moderate (Limited historical observations)",
                })

        # 2. Correlation Evidence Insights
        if len(num_df.columns) >= 2:
            corr = num_df.corr().fillna(0.0)
            cols = list(corr.columns)
            for i in range(len(cols)):
                for j in range(i + 1, len(cols)):
                    r_val = float(corr.iloc[i, j])
                    if abs(r_val) >= 0.45:
                        c1, c2 = str(cols[i]), str(cols[j])
                        rel_dir = "positive" if r_val > 0 else "inverse (negative)"
                        insights.append({
                            "category": "Bivariate Correlation Discovery",
                            "headline": f"Strong {rel_dir} relationship detected between {c1} and {c2} (r = {r_val:.2f}).",
                            "explanation": (
                                f"Statistical correlation analysis shows that {c1} and {c2} co-vary with "
                                f"Pearson r = {r_val:.3f} (explaining {r_val**2 * 100:.1f}% of shared variance)."
                            ),
                            "evidence": {
                                "feature_a": c1,
                                "feature_b": c2,
                                "pearson_r": round(r_val, 4),
                                "r_squared_pct": round(float(r_val**2 * 100.0), 2),
                            },
                            "confidence": "High",
                        })

        # 3. Risk & Threshold Insights
        risk_res = analyze_urban_risks(df, source_label=dataset_name)
        high_alerts = [
            a for a in risk_res.get("alerts", [])
            if a.get("risk_level") in ("High", "Critical", "Moderate")
        ]
        for alert in high_alerts[:4]:
            insights.append({
                "category": f"Urban Risk Alert ({alert['risk_level']})",
                "headline": (
                    f"The {alert['indicator']} measurements at {alert['location']} "
                    f"({alert['measured_value']} {alert['unit']}) are higher than the selected reference threshold ({alert['threshold']} {alert['unit']})."
                ),
                "explanation": alert["reason"],
                "evidence": {
                    "location": alert["location"],
                    "indicator": alert["indicator"],
                    "measured_value": alert["measured_value"],
                    "reference_threshold": alert["threshold"],
                    "reference_standard": alert["threshold_reference"],
                },
                "confidence": "High",
            })
            recommendations.append({
                "priority": alert["risk_level"],
                "target_area": alert["location"],
                "focus_indicator": alert["indicator"],
                "recommendation": alert["suggested_action"],
                "rationale": alert["reason"],
            })

    # 4. Machine Learning Model Insights
    if model_metrics:
        task_type = model_metrics.get("task_type", "regression")
        if task_type in ("regression", "time_series"):
            r2 = model_metrics.get("R2_score", 0.0)
            rmse = model_metrics.get("RMSE", 0.0)
            test_n = model_metrics.get("test_samples", 0)
            limitation_clause = (
                "with strong holdout validation coverage."
                if test_n >= 30
                else "but the available historical holdout observations are limited."
            )
            insights.append({
                "category": "Machine Learning Evaluation Insight",
                "headline": f"The trained regression model achieves R² = {r2:.3f} (RMSE = {rmse:.3f}), {limitation_clause}",
                "explanation": (
                    f"Evaluated on {test_n} unseen holdout records using leak-free preprocessing pipelines. "
                    f"Top predictive driver: "
                    + (
                        model_metrics["feature_importances"][0]["feature"]
                        if model_metrics.get("feature_importances")
                        else "combined environmental features"
                    )
                ),
                "evidence": {
                    "R2_score": r2,
                    "RMSE": rmse,
                    "MAE": model_metrics.get("MAE"),
                    "test_samples": test_n,
                },
                "confidence": "High" if r2 >= 0.6 and test_n >= 20 else "Moderate",
            })

    # 5. Location Comparison Insights
    if comparison_data and comparison_data.get("comparison_table"):
        table = comparison_data["comparison_table"]
        if len(table) >= 2:
            loc_a, loc_b = table[0], table[1]
            for ind_key in ["temperature_c", "pm25", "rainfall_mm", "aqi"]:
                a_ind = loc_a.get("indicators", {}).get(ind_key)
                b_ind = loc_b.get("indicators", {}).get(ind_key)
                if a_ind and b_ind:
                    diff = round(a_ind["average"] - b_ind["average"], 2)
                    higher_loc = loc_a["name"] if diff >= 0 else loc_b["name"]
                    lower_loc = loc_b["name"] if diff >= 0 else loc_a["name"]
                    insights.append({
                        "category": "Cross-Locality Comparison",
                        "headline": (
                            f"{higher_loc} exhibits {abs(diff):.2f} {a_ind['unit']} higher average {ind_key} than {lower_loc}."
                        ),
                        "explanation": (
                            f"Mean {ind_key} in {loc_a['name']} is {a_ind['average']} {a_ind['unit']} vs "
                            f"{b_ind['average']} {b_ind['unit']} in {loc_b['name']}."
                        ),
                        "evidence": {
                            "indicator": ind_key,
                            loc_a["name"]: a_ind["average"],
                            loc_b["name"]: b_ind["average"],
                            "difference": abs(diff),
                            "unit": a_ind["unit"],
                        },
                        "confidence": "High",
                    })

    if not recommendations:
        recommendations.append({
            "priority": "Moderate",
            "target_area": "Citywide Monitoring Grid",
            "focus_indicator": "Multi-Parameter Urban Telemetry",
            "recommendation": "Increase hourly telemetry density across heat-island and high-traffic corridors to improve localized forecasting.",
            "rationale": "Expanding spatial-temporal observation density reduces model prediction uncertainty.",
        })

    return sanitize_json({
        "dataset_analyzed": dataset_name,
        "total_insights": len(insights),
        "insights": insights,
        "recommendations": recommendations,
        "explanation_engine_mode": "Deterministic Statistical & ML Evidence Synthesizer (No external API keys exposed)",
    })

