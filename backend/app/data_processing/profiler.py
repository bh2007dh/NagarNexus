from pathlib import Path
from typing import Dict, Any, List
import warnings
import numpy as np
import pandas as pd
from fastapi import HTTPException, status

from app.utils.activity import sanitize_json


def load_dataframe(file_path: str) -> pd.DataFrame:
    """Load a CSV, XLSX, or XLS file into a Pandas DataFrame with robust error handling."""
    path = Path(file_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset file not found on disk: {path.name}",
        )
    ext = path.suffix.lower()
    try:
        if ext == ".csv":
            try:
                df = pd.read_csv(path, encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(path, encoding="latin-1")
        elif ext == ".xlsx":
            df = pd.read_excel(path, engine="openpyxl")
        elif ext == ".xls":
            try:
                df = pd.read_excel(path, engine="xlrd")
            except Exception:
                df = pd.read_excel(path, engine="openpyxl")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported dataset format: {ext}",
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse dataset file: {str(exc)}",
        )

    if df.empty or len(df.columns) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset contains no records or columns.",
        )
    return df


def classify_column_type(series: pd.Series, col_name: str) -> str:
    """Detect whether a column is numerical, datetime, boolean, or categorical."""
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_numeric_dtype(series):
        return "numerical"

    # Check if string column is predominantly dates
    non_null = series.dropna().astype(str).head(100)
    if len(non_null) > 0:
        lower_name = col_name.lower()
        date_hint = any(k in lower_name for k in ["date", "time", "timestamp", "observed", "day", "month", "year"])
        if date_hint:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                parsed = pd.to_datetime(non_null, errors="coerce")
                if parsed.notna().mean() >= 0.75:
                    return "datetime"

    return "categorical"


def profile_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform automated 12-point dataset profiling and data quality scoring:
    1. Row count
    2. Column count
    3. Numerical columns
    4. Categorical columns
    5. Date columns
    6. Missing values per column & total
    7. Duplicate records
    8. Inconsistent values (mixed casing, leading/trailing spaces, domain anomalies)
    9. Invalid data types (numeric strings, malformed dates)
    10. Column-level summary metadata
    11. Outlier counts (IQR method)
    12. Composite data quality metrics
    """
    row_count = int(len(df))
    col_count = int(len(df.columns))
    total_cells = max(row_count * col_count, 1)

    numerical_cols: List[str] = []
    categorical_cols: List[str] = []
    date_cols: List[str] = []
    column_details: List[Dict[str, Any]] = []
    inconsistencies: List[Dict[str, Any]] = []
    invalid_types: List[Dict[str, Any]] = []

    total_missing = int(df.isna().sum().sum())
    duplicate_rows = int(df.duplicated().sum())
    total_outliers = 0

    for col in df.columns:
        col_str = str(col)
        series = df[col]
        col_type = classify_column_type(series, col_str)

        if col_type == "numerical":
            numerical_cols.append(col_str)
        elif col_type == "datetime":
            date_cols.append(col_str)
        else:
            categorical_cols.append(col_str)

        missing_cnt = int(series.isna().sum())
        unique_cnt = int(series.nunique(dropna=True))
        non_null = series.dropna()
        sample_vals = [str(v) for v in non_null.head(5).tolist()]

        col_info: Dict[str, Any] = {
            "column_name": col_str,
            "data_type": col_type,
            "raw_dtype": str(series.dtype),
            "missing_count": missing_cnt,
            "missing_pct": round((missing_cnt / max(row_count, 1)) * 100.0, 2),
            "unique_count": unique_cnt,
            "sample_values": sample_vals,
        }

        if col_type == "numerical" and len(non_null) > 0:
            num_series = pd.to_numeric(non_null, errors="coerce").dropna()
            if len(num_series) > 0:
                q1 = float(num_series.quantile(0.25))
                q3 = float(num_series.quantile(0.75))
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                outlier_cnt = int(((num_series < lower) | (num_series > upper)).sum()) if iqr > 0 else 0
                total_outliers += outlier_cnt

                col_info.update({
                    "mean": round(float(num_series.mean()), 4),
                    "std": round(float(num_series.std(ddof=1)) if len(num_series) > 1 else 0.0, 4),
                    "min": round(float(num_series.min()), 4),
                    "median": round(float(num_series.median()), 4),
                    "max": round(float(num_series.max()), 4),
                    "outlier_count": outlier_cnt,
                })

                # Check domain-level inconsistencies (e.g., negative rainfall, negative PM2.5, humidity > 100)
                lower_col = col_str.lower()
                if any(k in lower_col for k in ["rain", "precip", "pm2", "pm10", "no2", "o3", "co", "aqi", "wind", "humid"]):
                    neg_count = int((num_series < 0).sum())
                    if neg_count > 0:
                        inconsistencies.append({
                            "column": col_str,
                            "issue": "Negative physical measurement values",
                            "affected_rows": neg_count,
                        })
                if "humid" in lower_col:
                    over_100 = int((num_series > 100).sum())
                    if over_100 > 0:
                        inconsistencies.append({
                            "column": col_str,
                            "issue": "Relative humidity exceeding 100%",
                            "affected_rows": over_100,
                        })
        else:
            # Categorical or object column checks
            str_vals = non_null.astype(str)
            if len(str_vals) > 0:
                # Check whitespace inconsistencies
                whitespace_issues = int((str_vals != str_vals.str.strip()).sum())
                if whitespace_issues > 0:
                    inconsistencies.append({
                        "column": col_str,
                        "issue": "Leading or trailing whitespace in categorical values",
                        "affected_rows": whitespace_issues,
                    })

                # Check case inconsistencies
                lower_nunique = int(str_vals.str.strip().str.lower().nunique())
                stripped_nunique = int(str_vals.str.strip().nunique())
                if stripped_nunique > lower_nunique:
                    inconsistencies.append({
                        "column": col_str,
                        "issue": f"Inconsistent letter casing ({stripped_nunique} variants for {lower_nunique} distinct terms)",
                        "affected_rows": stripped_nunique - lower_nunique,
                    })

                # Check if an object column is actually mostly numbers (invalid data type / mixed values)
                if col_type == "categorical":
                    coerced_num = pd.to_numeric(str_vals, errors="coerce")
                    num_ratio = float(coerced_num.notna().mean())
                    if 0.5 <= num_ratio < 1.0:
                        bad_count = int(coerced_num.isna().sum())
                        invalid_types.append({
                            "column": col_str,
                            "expected_type": "numerical",
                            "current_type": str(series.dtype),
                            "invalid_rows": bad_count,
                            "description": f"{bad_count} non-numeric entries preventing numerical dtype inference",
                        })

        column_details.append(col_info)

    # Calculate Data Quality Metrics (0-100 scale)
    completeness_score = max(0.0, 100.0 * (1.0 - (total_missing / total_cells)))
    uniqueness_score = max(0.0, 100.0 * (1.0 - (duplicate_rows / max(row_count, 1))))
    inconsistency_cells = sum(item.get("affected_rows", 0) for item in inconsistencies)
    consistency_score = max(0.0, 100.0 * (1.0 - (inconsistency_cells / total_cells)))
    invalid_cells = sum(item.get("invalid_rows", 0) for item in invalid_types)
    validity_score = max(0.0, 100.0 * (1.0 - (invalid_cells / total_cells)))

    quality_score = round(
        0.40 * completeness_score
        + 0.25 * uniqueness_score
        + 0.20 * consistency_score
        + 0.15 * validity_score,
        2,
    )

    profile = {
        "row_count": row_count,
        "column_count": col_count,
        "numerical_columns": numerical_cols,
        "categorical_columns": categorical_cols,
        "date_columns": date_cols,
        "missing_values_total": total_missing,
        "missing_values_pct": round((total_missing / total_cells) * 100.0, 2),
        "duplicate_records": duplicate_rows,
        "duplicate_pct": round((duplicate_rows / max(row_count, 1)) * 100.0, 2),
        "total_outliers_detected": total_outliers,
        "inconsistent_values": inconsistencies,
        "invalid_data_types": invalid_types,
        "data_quality": {
            "overall_score": quality_score,
            "completeness": round(completeness_score, 2),
            "uniqueness": round(uniqueness_score, 2),
            "consistency": round(consistency_score, 2),
            "validity": round(validity_score, 2),
        },
        "columns": column_details,
    }
    return sanitize_json(profile)

