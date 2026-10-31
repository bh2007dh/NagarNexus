from typing import Dict, Any, List
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

from app.schemas.analysis import StatisticalCalculationRequest
from app.utils.activity import sanitize_json


def perform_statistical_analysis(df: pd.DataFrame, req: StatisticalCalculationRequest) -> Dict[str, Any]:
    """
    Execute all 10 statistical analyses with formulas, calculated values,
    interpretations, simple English explanations, and visualization series:
    1. Descriptive statistics
    2. Probability distributions
    3. Normal distribution analysis
    4. Z-score calculation
    5. Correlation analysis
    6. Covariance analysis
    7. Hypothesis testing (selected based on data & assumptions)
    8. Confidence intervals
    9. Outlier detection
    10. Trend analysis (OLS regression via statsmodels)
    """
    num_cols = [str(c) for c in df.select_dtypes(include=[np.number]).columns]
    target_col = req.target_column if req.target_column in df.columns else (num_cols[0] if num_cols else str(df.columns[0]))

    series = pd.to_numeric(df[target_col], errors="coerce").dropna()
    if len(series) < 3:
        raise ValueError(f"Column '{target_col}' requires at least 3 numeric observations for statistical testing.")

    n = int(len(series))
    mean_val = float(series.mean())
    median_val = float(series.median())
    modes = series.mode()
    mode_val = float(modes.iloc[0]) if len(modes) > 0 else median_val
    var_val = float(series.var(ddof=1))
    std_val = float(series.std(ddof=1))
    se_val = std_val / np.sqrt(n) if n > 0 else 0.0
    q1, q3 = float(series.quantile(0.25)), float(series.quantile(0.75))
    iqr_val = q3 - q1
    skew_val = float(stats.skew(series))
    kurt_val = float(stats.kurtosis(series))

    # 1. Descriptive Statistics
    descriptive_section = {
        "title": "1. Descriptive Statistics",
        "formula": "μ = (1/n) Σxᵢ,  s² = [1/(n-1)] Σ(xᵢ - x̄)²,  IQR = Q₃ - Q₁",
        "calculated_value": {
            "sample_size_n": n,
            "mean": round(mean_val, 4),
            "median": round(median_val, 4),
            "mode": round(mode_val, 4),
            "variance": round(var_val, 4),
            "std_deviation": round(std_val, 4),
            "standard_error": round(se_val, 4),
            "min": round(float(series.min()), 4),
            "q1": round(q1, 4),
            "q3": round(q3, 4),
            "iqr": round(iqr_val, 4),
            "max": round(float(series.max()), 4),
            "skewness": round(skew_val, 4),
            "kurtosis": round(kurt_val, 4),
        },
        "interpretation": (
            f"Across {n} valid observations of {target_col}, the central tendency is {mean_val:.2f} "
            f"(median {median_val:.2f}) with a standard deviation of {std_val:.2f}."
        ),
        "simple_english": (
            f"On average, {target_col} is around {mean_val:.2f}. Most typical measurements fall between "
            f"{q1:.2f} and {q3:.2f}."
        ),
    }

    # 2 & 3. Probability & Normal Distribution Analysis
    shapiro_Sample = series.sample(min(len(series), 5000), random_state=42)
    shapiro_stat, shapiro_p = stats.shapiro(shapiro_Sample)
    is_normal = bool(shapiro_p > 0.05)

    x_grid = np.linspace(float(series.min()), float(series.max()), 30)
    pdf_vals = stats.norm.pdf(x_grid, loc=mean_val, scale=max(std_val, 1e-6))
    hist_counts, hist_edges = np.histogram(series, bins=15, density=True)
    normal_curve_data = [
        {
            "x": round(float((hist_edges[i] + hist_edges[i + 1]) / 2.0), 3),
            "empirical_density": round(float(hist_counts[i]), 5),
            "normal_pdf": round(
                float(stats.norm.pdf((hist_edges[i] + hist_edges[i + 1]) / 2.0, loc=mean_val, scale=max(std_val, 1e-6))),
                5,
            ),
        }
        for i in range(len(hist_counts))
    ]

    normal_section = {
        "title": "2 & 3. Probability & Normal Distribution Fit",
        "formula": "f(x) = [1 / (σ√(2π))] · exp(-½((x - μ)/σ)²),  Shapiro-Wilk W-Statistic",
        "calculated_value": {
            "shapiro_wilk_w": round(float(shapiro_stat), 4),
            "p_value": round(float(shapiro_p), 6),
            "follows_normal_distribution": is_normal,
            "prob_within_1sigma_pct": round(float(((series >= mean_val - std_val) & (series <= mean_val + std_val)).mean() * 100.0), 2),
            "prob_within_2sigma_pct": round(float(((series >= mean_val - 2 * std_val) & (series <= mean_val + 2 * std_val)).mean() * 100.0), 2),
        },
        "interpretation": (
            f"Shapiro-Wilk normality test yielded W = {shapiro_stat:.4f} (p = {shapiro_p:.4g}). "
            + (
                "Fail to reject H₀: data is consistent with a Gaussian normal distribution (p > 0.05)."
                if is_normal
                else "Reject H₀: data exhibits statistically significant departure from normality (p ≤ 0.05); non-parametric metrics (median/IQR) are also advisable."
            )
        ),
        "simple_english": (
            f"The bell-curve test shows that {target_col} "
            + ("closely follows a classic bell curve." if is_normal else "is skewed or has heavier tails than a standard bell curve.")
        ),
        "visualization_data": normal_curve_data,
    }

    # 4. Z-Score Analysis
    z_scores = (series - mean_val) / max(std_val, 1e-9)
    extreme_z = series[np.abs(z_scores) > 2.5]
    z_distribution = [
        {
            "index": int(idx),
            "value": round(float(series.loc[idx]), 4),
            "z_score": round(float(z_scores.loc[idx]), 4),
        }
        for idx in series.index[:80]
    ]
    zscore_section = {
        "title": "4. Z-Score Standardization Analysis",
        "formula": "Z = (x - μ) / σ",
        "calculated_value": {
            "max_positive_z": round(float(z_scores.max()), 4),
            "min_negative_z": round(float(z_scores.min()), 4),
            "count_abs_z_gt_2": int((np.abs(z_scores) > 2.0).sum()),
            "count_abs_z_gt_3": int((np.abs(z_scores) > 3.0).sum()),
            "extreme_observations_gt_2_5sigma": int(len(extreme_z)),
        },
        "interpretation": (
            f"Z-scores standardize {target_col} in units of standard deviation. "
            f"{int((np.abs(z_scores) > 3.0).sum())} observation(s) exceed |Z| > 3.0."
        ),
        "simple_english": (
            f"Z-scores tell us how unusual each reading is compared to the average. "
            f"We found {int((np.abs(z_scores) > 2.0).sum())} readings that are more than 2 standard steps away from normal."
        ),
        "visualization_data": z_distribution,
    }

    # 5 & 6. Correlation & Covariance Analysis
    comp_col = req.comparison_column
    if not comp_col or comp_col not in df.columns or comp_col == target_col:
        other_nums = [c for c in num_cols if c != target_col]
        comp_col = other_nums[0] if other_nums else target_col

    paired = pd.DataFrame({
        "x": pd.to_numeric(df[target_col], errors="coerce"),
        "y": pd.to_numeric(df[comp_col], errors="coerce"),
    }).dropna()

    if len(paired) >= 3 and target_col != comp_col:
        pearson_r, pearson_p = stats.pearsonr(paired["x"], paired["y"])
        spearman_rho, spearman_p = stats.spearmanr(paired["x"], paired["y"])
        cov_val = float(np.cov(paired["x"], paired["y"], ddof=1)[0, 1])
    else:
        pearson_r, pearson_p, spearman_rho, spearman_p, cov_val = 1.0, 0.0, 1.0, 0.0, var_val

    correlation_section = {
        "title": f"5 & 6. Correlation & Covariance ({target_col} vs {comp_col})",
        "formula": "r = Cov(X,Y) / (σ_X · σ_Y),  Cov(X,Y) = [1/(n-1)] Σ(xᵢ - x̄)(yᵢ - ȳ)",
        "calculated_value": {
            "feature_x": target_col,
            "feature_y": comp_col,
            "pearson_r": round(float(pearson_r), 4),
            "pearson_p_value": round(float(pearson_p), 6),
            "spearman_rho": round(float(spearman_rho), 4),
            "spearman_p_value": round(float(spearman_p), 6),
            "covariance": round(cov_val, 4),
            "shared_variance_r2_pct": round(float(pearson_r ** 2) * 100.0, 2),
        },
        "interpretation": (
            f"Pearson r = {pearson_r:.4f} (p = {pearson_p:.4g}), Spearman ρ = {spearman_rho:.4f}, "
            f"and sample covariance = {cov_val:.4f}."
        ),
        "simple_english": (
            f"When {target_col} changes, {comp_col} shows a "
            f"{'strong' if abs(pearson_r) >= 0.7 else ('moderate' if abs(pearson_r) >= 0.4 else 'weak')} "
            f"{'positive (moves together)' if pearson_r >= 0 else 'negative (moves opposite)'} relationship "
            f"(explaining {pearson_r**2 * 100:.1f}% of shared movement)."
        ),
        "visualization_data": [
            {"x": round(float(r["x"]), 3), "y": round(float(r["y"]), 3)}
            for _, r in paired.head(120).iterrows()
        ],
    }

    # 7. Hypothesis Testing (Selected based on data & statistical assumptions)
    test_choice = (req.hypothesis_test or "auto").lower()
    if test_choice == "auto":
        if req.group_column and req.group_column in df.columns:
            groups = [
                pd.to_numeric(g[target_col], errors="coerce").dropna().values
                for _, g in df.groupby(req.group_column)
            ]
            groups = [g for g in groups if len(g) >= 2]
            if len(groups) == 2:
                test_choice = "t_test_ind" if is_normal else "mann_whitney"
            elif len(groups) > 2:
                test_choice = "anova"
            else:
                test_choice = "t_test_1samp"
        elif target_col != comp_col and len(paired) >= 3:
            test_choice = "t_test_ind" if is_normal else "mann_whitney"
        else:
            test_choice = "t_test_1samp"

    if test_choice == "anova" and req.group_column and req.group_column in df.columns:
        groups = [
            pd.to_numeric(g[target_col], errors="coerce").dropna().values
            for _, g in df.groupby(req.group_column)
        ]
        groups = [g for g in groups if len(g) >= 2]
        if len(groups) >= 2:
            stat_val, p_val = stats.f_oneway(*groups)
            test_name = f"One-Way ANOVA across {req.group_column} ({len(groups)} groups)"
            formula_str = "F = MS_between / MS_within"
        else:
            stat_val, p_val = stats.ttest_1samp(series, popmean=req.population_mean or median_val)
            test_name = "One-Sample Student's t-Test"
            formula_str = "t = (x̄ - μ₀) / (s / √n)"
    elif test_choice == "mann_whitney" and len(paired) >= 3 and target_col != comp_col:
        stat_val, p_val = stats.mannwhitneyu(paired["x"], paired["y"], alternative="two-sided")
        test_name = f"Mann-Whitney U Non-Parametric Test ({target_col} vs {comp_col})"
        formula_str = "U = n₁n₂ + [n₁(n₁+1)/2] - R₁ (Selected due to non-normality)"
    elif test_choice == "t_test_ind" and len(paired) >= 3 and target_col != comp_col:
        stat_val, p_val = stats.ttest_ind(paired["x"], paired["y"], equal_var=False)
        test_name = f"Welch's Two-Sample t-Test ({target_col} vs {comp_col})"
        formula_str = "t = (x̄₁ - x̄₂) / √(s₁²/n₁ + s₂²/n₂)"
    else:
        ref_mu = req.population_mean if req.population_mean is not None else round(median_val, 2)
        stat_val, p_val = stats.ttest_1samp(series, popmean=ref_mu)
        test_name = f"One-Sample t-Test against benchmark μ₀ = {ref_mu}"
        formula_str = "t = (x̄ - μ₀) / (s / √n)"

    significant = bool(p_val < (1.0 - req.confidence_level))
    hypothesis_section = {
        "title": "7. Hypothesis Testing",
        "formula": formula_str,
        "calculated_value": {
            "selected_test": test_name,
            "test_statistic": round(float(stat_val), 4),
            "p_value": round(float(p_val), 6),
            "alpha": round(1.0 - req.confidence_level, 4),
            "statistically_significant": significant,
            "normality_assumption_met": is_normal,
        },
        "interpretation": (
            f"Executed {test_name}. Statistic = {stat_val:.4f}, p-value = {p_val:.4g}. "
            + (
                f"Statistically significant difference detected at α = {1.0 - req.confidence_level:.2f} (reject null hypothesis H₀)."
                if significant
                else f"No statistically significant difference at α = {1.0 - req.confidence_level:.2f} (fail to reject null hypothesis H₀)."
            )
        ),
        "simple_english": (
            "The statistical test confirms the observed difference is real and unlikely due to random chance."
            if significant
            else "The observed difference is small enough that it could happen by normal everyday fluctuation."
        ),
    }

    # 8. Confidence Intervals
    ci_low, ci_high = stats.t.interval(
        req.confidence_level,
        df=max(n - 1, 1),
        loc=mean_val,
        scale=max(se_val, 1e-9),
    )
    ci_section = {
        "title": f"8. Confidence Interval ({int(req.confidence_level * 100)}% Level)",
        "formula": "CI = x̄ ± t_(α/2, n-1) · (s / √n)",
        "calculated_value": {
            "confidence_level_pct": round(req.confidence_level * 100.0, 1),
            "sample_mean": round(mean_val, 4),
            "lower_bound": round(float(ci_low), 4),
            "upper_bound": round(float(ci_high), 4),
            "margin_of_error": round(float(ci_high - mean_val), 4),
        },
        "interpretation": (
            f"With {req.confidence_level*100:.1f}% confidence, the true population mean of {target_col} "
            f"lies within [{ci_low:.4f}, {ci_high:.4f}]."
        ),
        "simple_english": (
            f"We are {req.confidence_level*100:.0f}% sure the true average of {target_col} is between "
            f"{ci_low:.2f} and {ci_high:.2f}."
        ),
    }

    # 9. Outlier Detection
    low_fence = q1 - 1.5 * iqr_val
    high_fence = q3 + 1.5 * iqr_val
    iqr_outliers = series[(series < low_fence) | (series > high_fence)] if iqr_val > 0 else pd.Series(dtype=float)
    z_outliers = series[np.abs(z_scores) > 3.0]
    outlier_section = {
        "title": "9. Statistical Outlier Detection (Tukey IQR & 3-Sigma)",
        "formula": "IQR Fences: [Q₁ - 1.5·IQR, Q₃ + 1.5·IQR];  Z-Fence: |Z| > 3.0",
        "calculated_value": {
            "iqr_lower_fence": round(low_fence, 4),
            "iqr_upper_fence": round(high_fence, 4),
            "iqr_outlier_count": int(len(iqr_outliers)),
            "zscore_outlier_count": int(len(z_outliers)),
            "sample_outlier_values": [round(float(v), 4) for v in iqr_outliers.head(10).tolist()],
        },
        "interpretation": (
            f"Tukey's 1.5×IQR rule identified {len(iqr_outliers)} outlier(s) outside [{low_fence:.2f}, {high_fence:.2f}], "
            f"while the 3σ rule identified {len(z_outliers)} extreme observation(s)."
        ),
        "simple_english": (
            f"We detected {len(iqr_outliers)} unusually high or low readings in {target_col} outside the normal range "
            f"of {low_fence:.2f} to {high_fence:.2f}."
        ),
    }

    # 10. Trend Analysis (OLS Linear Regression via Statsmodels)
    time_idx = np.arange(len(series), dtype=float)
    X_ols = sm.add_constant(time_idx)
    ols_model = sm.OLS(series.values, X_ols).fit()
    intercept = float(ols_model.params[0])
    slope = float(ols_model.params[1])
    r_squared = float(ols_model.rsquared)
    slope_p = float(ols_model.pvalues[1]) if len(ols_model.pvalues) > 1 else 1.0
    fitted_vals = intercept + slope * time_idx

    trend_direction = (
        "Statistically Significant Upward Trend"
        if slope > 0 and slope_p < 0.05
        else (
            "Statistically Significant Downward Trend"
            if slope < 0 and slope_p < 0.05
            else "Stable / No Statistically Significant Monotonic Trend"
        )
    )
    step = max(1, len(series) // 60)
    trend_chart = [
        {
            "step": int(i + 1),
            "actual": round(float(series.iloc[i]), 4),
            "trend_line": round(float(fitted_vals[i]), 4),
        }
        for i in range(0, len(series), step)
    ]

    trend_section = {
        "title": "10. Linear Trend Analysis (Statsmodels OLS)",
        "formula": "ŷ_t = β₀ + β₁·t + ε_t",
        "calculated_value": {
            "slope_beta1": round(slope, 6),
            "intercept_beta0": round(intercept, 4),
            "r_squared": round(r_squared, 4),
            "slope_p_value": round(slope_p, 6),
            "direction": trend_direction,
        },
        "interpretation": (
            f"OLS regression over observation index gives slope β₁ = {slope:.5f} per step "
            f"(p = {slope_p:.4g}, R² = {r_squared:.4f}): {trend_direction}."
        ),
        "simple_english": (
            f"Over the dataset sequence, {target_col} shows a {trend_direction.lower()} "
            f"(changing by {slope:+.4f} units per observation step)."
        ),
        "visualization_data": trend_chart,
    }

    return sanitize_json({
        "target_column": target_col,
        "comparison_column": comp_col,
        "Descriptive_Statistics": descriptive_section,
        "Normal_Distribution": normal_section,
        "Z_Score_Analysis": zscore_section,
        "Correlation_And_Covariance": correlation_section,
        "Hypothesis_Testing": hypothesis_section,
        "Confidence_Intervals": ci_section,
        "Outlier_Detection": outlier_section,
        "Trend_Analysis": trend_section,
    })

