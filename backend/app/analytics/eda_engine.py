import base64
import io
from typing import Dict, Any, List
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

from app.schemas.analysis import EDAVisualizationRequest
from app.utils.activity import sanitize_json


def run_automated_eda(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Execute comprehensive Exploratory Data Analysis on a DataFrame:
    - Overview
    - Descriptive statistics (Mean, Median, Mode, Variance, Std Dev, Q1, Q2, Q3, IQR, Min, Max, Skewness, Kurtosis)
    - Correlation & Covariance matrices
    - Distribution analysis
    - Missing value analysis
    - Outlier analysis
    """
    row_count, col_count = df.shape
    num_df = df.select_dtypes(include=[np.number])
    cat_df = df.select_dtypes(exclude=[np.number])

    descriptive_stats: Dict[str, Dict[str, Any]] = {}
    outlier_summary: List[Dict[str, Any]] = []
    distribution_summary: List[Dict[str, Any]] = []

    for col in num_df.columns:
        s = num_df[col].dropna()
        if len(s) == 0:
            continue
        mean_val = float(s.mean())
        median_val = float(s.median())
        modes = s.mode()
        mode_val = float(modes.iloc[0]) if len(modes) > 0 else median_val
        var_val = float(s.var(ddof=1)) if len(s) > 1 else 0.0
        std_val = float(s.std(ddof=1)) if len(s) > 1 else 0.0
        q1 = float(s.quantile(0.25))
        q2 = float(s.quantile(0.50))
        q3 = float(s.quantile(0.75))
        iqr = q3 - q1
        min_val = float(s.min())
        max_val = float(s.max())
        skew_val = float(s.skew()) if len(s) > 2 else 0.0
        kurt_val = float(s.kurtosis()) if len(s) > 3 else 0.0

        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr
        outliers = s[(s < lower_fence) | (s > upper_fence)] if iqr > 0 else pd.Series(dtype=float)

        descriptive_stats[str(col)] = {
            "count": int(len(s)),
            "mean": round(mean_val, 4),
            "median": round(median_val, 4),
            "mode": round(mode_val, 4),
            "variance": round(var_val, 4),
            "std_dev": round(std_val, 4),
            "q1": round(q1, 4),
            "q2": round(q2, 4),
            "q3": round(q3, 4),
            "iqr": round(iqr, 4),
            "min": round(min_val, 4),
            "max": round(max_val, 4),
            "range": round(max_val - min_val, 4),
            "skewness": round(skew_val, 4),
            "kurtosis": round(kurt_val, 4),
        }

        outlier_summary.append({
            "column": str(col),
            "outlier_count": int(len(outliers)),
            "outlier_pct": round((len(outliers) / max(len(s), 1)) * 100.0, 2),
            "lower_fence": round(lower_fence, 4),
            "upper_fence": round(upper_fence, 4),
            "min_observed": round(min_val, 4),
            "max_observed": round(max_val, 4),
        })

        # Histogram bins for distribution analysis
        counts, bin_edges = np.histogram(s, bins=min(15, max(5, int(np.sqrt(len(s))))))
        bins_data = [
            {
                "bin": f"{bin_edges[i]:.1f} to {bin_edges[i+1]:.1f}",
                "midpoint": round(float((bin_edges[i] + bin_edges[i+1]) / 2.0), 3),
                "count": int(counts[i]),
            }
            for i in range(len(counts))
        ]
        shape_desc = (
            "Approximately Symmetric"
            if abs(skew_val) < 0.5
            else ("Right-Skewed (Positive Skew)" if skew_val >= 0.5 else "Left-Skewed (Negative Skew)")
        )
        distribution_summary.append({
            "column": str(col),
            "skewness": round(skew_val, 4),
            "kurtosis": round(kurt_val, 4),
            "shape": shape_desc,
            "histogram": bins_data,
        })

    # Correlation and Covariance Matrices
    correlation_matrix: Dict[str, Dict[str, float]] = {}
    covariance_matrix: Dict[str, Dict[str, float]] = {}
    top_correlations: List[Dict[str, Any]] = []

    if len(num_df.columns) >= 2:
        corr_df = num_df.corr(numeric_only=True).fillna(0.0)
        cov_df = num_df.cov(numeric_only=True).fillna(0.0)
        correlation_matrix = {
            str(r): {str(c): round(float(corr_df.loc[r, c]), 4) for c in corr_df.columns}
            for r in corr_df.index
        }
        covariance_matrix = {
            str(r): {str(c): round(float(cov_df.loc[r, c]), 4) for c in cov_df.columns}
            for r in cov_df.index
        }
        cols_list = list(corr_df.columns)
        for i in range(len(cols_list)):
            for j in range(i + 1, len(cols_list)):
                c1, c2 = str(cols_list[i]), str(cols_list[j])
                r_val = float(corr_df.iloc[i, j])
                top_correlations.append({
                    "feature_a": c1,
                    "feature_b": c2,
                    "correlation": round(r_val, 4),
                    "abs_correlation": round(abs(r_val), 4),
                    "covariance": round(float(cov_df.iloc[i, j]), 4),
                    "strength": (
                        "Strong" if abs(r_val) >= 0.7 else ("Moderate" if abs(r_val) >= 0.4 else "Weak")
                    ),
                })
        top_correlations.sort(key=lambda x: x["abs_correlation"], reverse=True)

    # Missing Value Analysis
    missing_analysis = [
        {
            "column": str(col),
            "missing_count": int(df[col].isna().sum()),
            "present_count": int(df[col].notna().sum()),
            "missing_pct": round(float(df[col].isna().mean() * 100.0), 2),
        }
        for col in df.columns
    ]

    # Categorical Summaries
    categorical_summaries: Dict[str, List[Dict[str, Any]]] = {}
    for col in cat_df.columns:
        vc = cat_df[col].dropna().astype(str).value_counts().head(10)
        categorical_summaries[str(col)] = [
            {"category": str(k), "count": int(v), "pct": round((int(v) / max(row_count, 1)) * 100.0, 2)}
            for k, v in vc.items()
        ]

    return sanitize_json({
        "overview": {
            "row_count": int(row_count),
            "column_count": int(col_count),
            "numerical_column_count": int(len(num_df.columns)),
            "categorical_column_count": int(len(cat_df.columns)),
            "numerical_columns": [str(c) for c in num_df.columns],
            "categorical_columns": [str(c) for c in cat_df.columns],
            "total_missing": int(df.isna().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
        },
        "descriptive_statistics": descriptive_stats,
        "correlation_matrix": correlation_matrix,
        "covariance_matrix": covariance_matrix,
        "top_correlations": top_correlations[:15],
        "distribution_analysis": distribution_summary,
        "missing_value_analysis": missing_analysis,
        "outlier_analysis": outlier_summary,
        "categorical_summaries": categorical_summaries,
    })


def generate_eda_visualization(df: pd.DataFrame, req: EDAVisualizationRequest) -> Dict[str, Any]:
    """
    Generate both interactive chart series (from real dataset rows) and a rendered
    Matplotlib/Seaborn high-DPI base64 PNG chart for download & inspection.
    """
    work_df = df.copy()

    if req.filter_column and req.filter_value is not None and req.filter_column in work_df.columns:
        work_df = work_df[work_df[req.filter_column].astype(str) == str(req.filter_value)]

    if work_df.empty:
        work_df = df.copy()

    num_cols = [str(c) for c in work_df.select_dtypes(include=[np.number]).columns]
    all_cols = [str(c) for c in work_df.columns]

    x_col = req.x_column if req.x_column in all_cols else (num_cols[0] if num_cols else all_cols[0])
    y_col = req.y_column if req.y_column in all_cols else (num_cols[1] if len(num_cols) > 1 else x_col)
    chart_type = (req.chart_type or "histogram").lower()

    sns.set_theme(style="darkgrid")
    fig, ax = plt.subplots(figsize=(9, 5), dpi=130)
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#1e293b")
    ax.tick_params(colors="#cbd5e1")
    ax.xaxis.label.set_color("#e2e8f0")
    ax.yaxis.label.set_color("#e2e8f0")
    ax.title.set_color("#f8fafc")

    chart_data: List[Dict[str, Any]] = []
    summary_stats: Dict[str, Any] = {}

    if chart_type in ("histogram", "distribution"):
        series = pd.to_numeric(work_df[x_col], errors="coerce").dropna()
        if len(series) > 0:
            bins = min(max(req.bins, 5), 50)
            sns.histplot(
                series,
                bins=bins,
                kde=(chart_type == "distribution"),
                color="#38bdf8",
                edgecolor="#0f172a",
                ax=ax,
            )
            ax.set_title(f"{'Distribution & KDE' if chart_type == 'distribution' else 'Histogram'} of {x_col}")
            ax.set_xlabel(x_col)
            ax.set_ylabel("Frequency")

            counts, edges = np.histogram(series, bins=bins)
            chart_data = [
                {
                    "bin": f"{edges[i]:.1f}-{edges[i+1]:.1f}",
                    "x": round(float((edges[i] + edges[i + 1]) / 2.0), 3),
                    "count": int(counts[i]),
                }
                for i in range(len(counts))
            ]
            summary_stats = {
                "mean": round(float(series.mean()), 3),
                "median": round(float(series.median()), 3),
                "std": round(float(series.std(ddof=1)) if len(series) > 1 else 0.0, 3),
            }

    elif chart_type == "bar":
        if x_col in num_cols and y_col in num_cols and x_col != y_col:
            grouped = work_df[[x_col, y_col]].dropna().head(30)
            chart_data = [
                {"name": str(row[x_col]), "value": round(float(row[y_col]), 3)}
                for _, row in grouped.iterrows()
            ]
            ax.bar([d["name"] for d in chart_data[:15]], [d["value"] for d in chart_data[:15]], color="#38bdf8")
        else:
            if y_col in num_cols and x_col != y_col:
                agg = work_df.groupby(work_df[x_col].astype(str))[y_col].mean().sort_values(ascending=False).head(15)
                chart_data = [{"name": str(k), "value": round(float(v), 3)} for k, v in agg.items()]
                ax.bar([d["name"] for d in chart_data], [d["value"] for d in chart_data], color="#38bdf8")
                ax.set_ylabel(f"Mean {y_col}")
            else:
                vc = work_df[x_col].dropna().astype(str).value_counts().head(15)
                chart_data = [{"name": str(k), "value": int(v)} for k, v in vc.items()]
                ax.bar([d["name"] for d in chart_data], [d["value"] for d in chart_data], color="#38bdf8")
                ax.set_ylabel("Count")
        plt.xticks(rotation=30, ha="right")
        ax.set_title(f"Bar Chart: {x_col} vs {y_col}")

    elif chart_type == "line":
        sub = work_df[[x_col, y_col]].dropna().head(150)
        y_num = pd.to_numeric(sub[y_col], errors="coerce")
        valid = sub[y_num.notna()].copy()
        valid[y_col] = y_num[y_num.notna()]
        chart_data = [
            {"x": str(row[x_col]), "y": round(float(row[y_col]), 4)}
            for _, row in valid.iterrows()
        ]
        ax.plot(range(len(chart_data)), [d["y"] for d in chart_data], color="#38bdf8", linewidth=2, marker="o", markersize=3)
        ax.set_title(f"Line Trend: {y_col} over {x_col}")
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)

    elif chart_type == "scatter":
        s_x = pd.to_numeric(work_df[x_col], errors="coerce")
        s_y = pd.to_numeric(work_df[y_col], errors="coerce")
        valid = pd.DataFrame({x_col: s_x, y_col: s_y}).dropna().head(300)
        chart_data = [
            {"x": round(float(row[x_col]), 4), "y": round(float(row[y_col]), 4)}
            for _, row in valid.iterrows()
        ]
        ax.scatter(valid[x_col], valid[y_col], color="#38bdf8", alpha=0.75, edgecolors="#0284c7")
        ax.set_title(f"Scatter Plot: {x_col} vs {y_col}")
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        if len(valid) > 2:
            corr_v = float(valid[x_col].corr(valid[y_col]))
            summary_stats = {"pearson_r": round(corr_v, 4), "sample_size": len(valid)}

    elif chart_type == "boxplot":
        target_c = y_col if y_col in num_cols else (num_cols[0] if num_cols else x_col)
        s = pd.to_numeric(work_df[target_c], errors="coerce").dropna()
        if len(s) > 0:
            sns.boxplot(x=s, color="#38bdf8", ax=ax)
            ax.set_title(f"Box Plot & Quartile Spread: {target_c}")
            q1, med, q3 = float(s.quantile(0.25)), float(s.median()), float(s.quantile(0.75))
            iqr = q3 - q1
            chart_data = [
                {
                    "column": target_c,
                    "min": round(float(s.min()), 3),
                    "lower_fence": round(float(max(s.min(), q1 - 1.5 * iqr)), 3),
                    "q1": round(q1, 3),
                    "median": round(med, 3),
                    "q3": round(q3, 3),
                    "upper_fence": round(float(min(s.max(), q3 + 1.5 * iqr)), 3),
                    "max": round(float(s.max()), 3),
                }
            ]
            summary_stats = chart_data[0]

    elif chart_type == "pie":
        vc = work_df[x_col].dropna().astype(str).value_counts().head(8)
        chart_data = [{"name": str(k), "value": int(v)} for k, v in vc.items()]
        if chart_data:
            ax.pie(
                [d["value"] for d in chart_data],
                labels=[d["name"] for d in chart_data],
                autopct="%1.1f%%",
                textprops={"color": "#f8fafc"},
            )
            ax.set_title(f"Proportional Breakdown: {x_col}")

    elif chart_type == "correlation_heatmap":
        num_only = work_df.select_dtypes(include=[np.number])
        if len(num_only.columns) >= 2:
            corr = num_only.corr().fillna(0.0)
            sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax, cbar=True)
            ax.set_title("Feature Correlation Matrix Heatmap")
            for r in corr.index:
                row_item: Dict[str, Any] = {"feature": str(r)}
                for c in corr.columns:
                    row_item[str(c)] = round(float(corr.loc[r, c]), 4)
                chart_data.append(row_item)

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    image_base64 = "data:image/png;base64," + base64.b64encode(buf.read()).decode("utf-8")

    return sanitize_json({
        "chart_type": chart_type,
        "x_column": x_col,
        "y_column": y_col,
        "chart_data": chart_data,
        "summary_statistics": summary_stats,
        "matplotlib_image": image_base64,
    })

