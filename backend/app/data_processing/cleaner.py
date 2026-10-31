from pathlib import Path
from typing import Dict, Any, List
import uuid
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler, LabelEncoder

from app.core.config import settings
from app.data_processing.profiler import profile_dataframe
from app.schemas.analysis import CleaningOperationRequest
from app.utils.activity import sanitize_json


def execute_data_cleaning(
    df: pd.DataFrame,
    dataset_name: str,
    config: CleaningOperationRequest,
) -> Dict[str, Any]:
    """
    Execute user-configured data cleaning operations on a copy of the DataFrame.
    Never modifies the original uploaded file; saves cleaned dataset to datasets/processed/.
    Returns before-and-after profiles, applied operations log, and saved processed path.
    """
    before_profile = profile_dataframe(df)
    cleaned_df = df.copy()
    operations_log: List[str] = []

    # 1. Column Renaming
    if config.rename_columns:
        valid_renames = {
            old_col: new_col.strip()
            for old_col, new_col in config.rename_columns.items()
            if old_col in cleaned_df.columns and new_col and new_col.strip()
        }
        if valid_renames:
            cleaned_df = cleaned_df.rename(columns=valid_renames)
            operations_log.append(f"Renamed {len(valid_renames)} column(s): {valid_renames}")

    # 2. Duplicate Removal
    if config.remove_duplicates:
        before_rows = len(cleaned_df)
        cleaned_df = cleaned_df.drop_duplicates().reset_index(drop=True)
        removed = before_rows - len(cleaned_df)
        operations_log.append(f"Removed {removed} duplicate row(s)")

    # 3. Date Formatting
    if config.date_columns:
        for col in config.date_columns:
            if col in cleaned_df.columns:
                parsed = pd.to_datetime(cleaned_df[col], errors="coerce")
                cleaned_df[col] = parsed.dt.strftime("%Y-%m-%d %H:%M:%S").str.replace(" 00:00:00", "", regex=False)
                operations_log.append(f"Formatted date column '{col}' to ISO-8601 standard")

    # 4. Data Type Conversion
    if config.convert_types:
        for col, target_type in config.convert_types.items():
            if col not in cleaned_df.columns:
                continue
            t = target_type.lower()
            try:
                if t in ("float", "numeric", "number"):
                    cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors="coerce").astype(float)
                    operations_log.append(f"Converted column '{col}' to float")
                elif t in ("int", "integer"):
                    num_s = pd.to_numeric(cleaned_df[col], errors="coerce")
                    cleaned_df[col] = num_s.fillna(0).round().astype(int)
                    operations_log.append(f"Converted column '{col}' to integer")
                elif t in ("str", "string", "text", "categorical"):
                    cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
                    operations_log.append(f"Converted column '{col}' to stripped string")
                elif t in ("datetime", "date"):
                    cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors="coerce").dt.strftime("%Y-%m-%d")
                    operations_log.append(f"Converted column '{col}' to date")
            except Exception as exc:
                operations_log.append(f"Skipped type conversion on '{col}': {str(exc)}")

    # 5. Missing Value Imputation
    strategy = (config.missing_strategy or "none").lower()
    target_cols = config.target_columns or list(cleaned_df.columns)
    target_cols = [c for c in target_cols if c in cleaned_df.columns]

    if strategy != "none" and target_cols:
        if strategy == "drop_rows":
            before_rows = len(cleaned_df)
            cleaned_df = cleaned_df.dropna(subset=target_cols).reset_index(drop=True)
            operations_log.append(f"Dropped {before_rows - len(cleaned_df)} row(s) with missing values in selected columns")
        elif strategy == "forward_fill":
            missing_before = int(cleaned_df[target_cols].isna().sum().sum())
            cleaned_df[target_cols] = cleaned_df[target_cols].ffill().bfill()
            operations_log.append(f"Forward/backward filled {missing_before} missing value(s)")
        else:
            imputed_count = 0
            for col in target_cols:
                na_cnt = int(cleaned_df[col].isna().sum())
                if na_cnt == 0:
                    continue
                if pd.api.types.is_numeric_dtype(cleaned_df[col]):
                    if strategy == "mean":
                        fill_val = float(cleaned_df[col].mean())
                    elif strategy == "median":
                        fill_val = float(cleaned_df[col].median())
                    else:  # mode
                        modes = cleaned_df[col].mode(dropna=True)
                        fill_val = float(modes.iloc[0]) if len(modes) > 0 else 0.0
                    cleaned_df[col] = cleaned_df[col].fillna(round(fill_val, 4))
                    imputed_count += na_cnt
                else:
                    modes = cleaned_df[col].mode(dropna=True)
                    fill_val = modes.iloc[0] if len(modes) > 0 else "Unknown"
                    cleaned_df[col] = cleaned_df[col].fillna(fill_val)
                    imputed_count += na_cnt
            operations_log.append(f"Imputed {imputed_count} missing value(s) using '{strategy}' strategy")

    # 6. Outlier Identification and Handling
    outlier_action = (config.outlier_action or "none").lower()
    if outlier_action != "none":
        num_cols = config.outlier_columns or [
            c for c in cleaned_df.columns if pd.api.types.is_numeric_dtype(cleaned_df[c])
        ]
        num_cols = [c for c in num_cols if c in cleaned_df.columns and pd.api.types.is_numeric_dtype(cleaned_df[c])]
        if outlier_action == "clip_iqr":
            clipped_total = 0
            for col in num_cols:
                s = cleaned_df[col].dropna()
                if len(s) < 4:
                    continue
                q1, q3 = float(s.quantile(0.25)), float(s.quantile(0.75))
                iqr = q3 - q1
                if iqr <= 0:
                    continue
                low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                outliers = int(((cleaned_df[col] < low) | (cleaned_df[col] > high)).sum())
                cleaned_df[col] = cleaned_df[col].clip(lower=low, upper=high)
                clipped_total += outliers
            operations_log.append(f"Clipped {clipped_total} outlier value(s) to 1.5x IQR bounds across {len(num_cols)} column(s)")
        elif outlier_action == "remove_iqr":
            before_rows = len(cleaned_df)
            mask = pd.Series(True, index=cleaned_df.index)
            for col in num_cols:
                s = cleaned_df[col].dropna()
                if len(s) < 4:
                    continue
                q1, q3 = float(s.quantile(0.25)), float(s.quantile(0.75))
                iqr = q3 - q1
                if iqr <= 0:
                    continue
                low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                mask &= (cleaned_df[col].isna()) | ((cleaned_df[col] >= low) & (cleaned_df[col] <= high))
            cleaned_df = cleaned_df[mask].reset_index(drop=True)
            operations_log.append(f"Removed {before_rows - len(cleaned_df)} outlier row(s) exceeding 1.5x IQR bounds")
        elif outlier_action == "clip_zscore":
            clipped_total = 0
            for col in num_cols:
                s = cleaned_df[col].dropna()
                if len(s) < 4 or float(s.std()) == 0:
                    continue
                mean, std = float(s.mean()), float(s.std())
                low, high = mean - 3.0 * std, mean + 3.0 * std
                outliers = int(((cleaned_df[col] < low) | (cleaned_df[col] > high)).sum())
                cleaned_df[col] = cleaned_df[col].clip(lower=low, upper=high)
                clipped_total += outliers
            operations_log.append(f"Clipped {clipped_total} extreme value(s) outside +/- 3.0 Z-score")

    # 7. Data Normalization / Standardization
    scaling = (config.scaling_method or "none").lower()
    if scaling in ("normalize", "standardize"):
        scale_cols = config.scaling_columns or [
            c for c in cleaned_df.columns if pd.api.types.is_numeric_dtype(cleaned_df[c])
        ]
        scale_cols = [
            c for c in scale_cols
            if c in cleaned_df.columns and pd.api.types.is_numeric_dtype(cleaned_df[c])
        ]
        if scale_cols:
            scaler = MinMaxScaler() if scaling == "normalize" else StandardScaler()
            for col in scale_cols:
                non_na = cleaned_df[col].notna()
                if non_na.sum() > 1:
                    vals = cleaned_df.loc[non_na, [col]].values
                    cleaned_df.loc[non_na, col] = np.round(scaler.fit_transform(vals).flatten(), 6)
            operations_log.append(f"Applied '{scaling}' scaling to {len(scale_cols)} numerical column(s): {scale_cols}")

    # 8. Categorical Encoding
    encoding = (config.encoding_method or "none").lower()
    if encoding in ("label", "onehot"):
        enc_cols = config.encoding_columns or [
            c for c in cleaned_df.columns if not pd.api.types.is_numeric_dtype(cleaned_df[c])
        ]
        enc_cols = [c for c in enc_cols if c in cleaned_df.columns]
        if encoding == "label" and enc_cols:
            for col in enc_cols:
                le = LabelEncoder()
                cleaned_df[f"{col}_encoded"] = le.fit_transform(cleaned_df[col].astype(str))
            operations_log.append(f"Created label-encoded column(s) for: {enc_cols}")
        elif encoding == "onehot" and enc_cols:
            # Restrict one-hot encoding to columns with tractable cardinality (<= 20 unique values)
            valid_oh = [c for c in enc_cols if cleaned_df[c].nunique() <= 20]
            if valid_oh:
                cleaned_df = pd.get_dummies(cleaned_df, columns=valid_oh, drop_first=False, dtype=int)
                operations_log.append(f"Applied one-hot encoding to categorical column(s): {valid_oh}")

    after_profile = profile_dataframe(cleaned_df)

    # Save processed dataset separately in datasets/processed/
    processed_dir = Path(settings.PROCESSED_DIR)
    processed_dir.mkdir(parents=True, exist_ok=True)
    safe_base = "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in dataset_name)
    out_filename = f"cleaned_{safe_base}_{uuid.uuid4().hex[:8]}.csv"
    out_path = processed_dir / out_filename
    cleaned_df.to_csv(out_path, index=False)

    comparison_summary = {
        "rows_before": before_profile["row_count"],
        "rows_after": after_profile["row_count"],
        "rows_delta": after_profile["row_count"] - before_profile["row_count"],
        "columns_before": before_profile["column_count"],
        "columns_after": after_profile["column_count"],
        "missing_before": before_profile["missing_values_total"],
        "missing_after": after_profile["missing_values_total"],
        "duplicates_before": before_profile["duplicate_records"],
        "duplicates_after": after_profile["duplicate_records"],
        "outliers_before": before_profile["total_outliers_detected"],
        "outliers_after": after_profile["total_outliers_detected"],
        "quality_score_before": before_profile["data_quality"]["overall_score"],
        "quality_score_after": after_profile["data_quality"]["overall_score"],
    }

    return sanitize_json({
        "processed_file_path": str(out_path),
        "processed_filename": out_filename,
        "operations_applied": operations_log,
        "comparison": comparison_summary,
        "before_profile": before_profile,
        "after_profile": after_profile,
        "preview_rows": cleaned_df.head(25).replace({np.nan: None}).to_dict(orient="records"),
    })

