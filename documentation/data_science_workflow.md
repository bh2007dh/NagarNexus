# NagarNexus Data Science & Machine Learning Workflow

## 1. Data Ingestion & 12-Point Profiling (`app/data_processing/profiler.py`)

Upon upload or ingestion, every dataset is automatically inspected across 12 dimensions:
1. Row count
2. Column count
3. Numerical feature detection
4. Categorical feature detection
5. Temporal/Date column detection
6. Missing value counts and percentages
7. Exact duplicate record detection
8. Domain and formatting inconsistency detection (whitespace padding, casing mismatches, negative physical measurements, >100% humidity)
9. Invalid dtype detection (numeric columns polluted by text tokens)
10. Quartile & summary profiling
11. Tukey $1.5 \times \text{IQR}$ outlier quantification
12. Composite Data Quality Score ($0.40 \times \text{Completeness} + 0.25 \times \text{Uniqueness} + 0.20 \times \text{Consistency} + 0.15 \times \text{Validity}$)

## 2. Non-Destructive Data Cleaning (`app/data_processing/cleaner.py`)

- Original uploaded files in `backend/uploads/` and sample files in `datasets/sample/` are **never overwritten**.
- Cleaned datasets are written to `datasets/processed/cleaned_<name>_<uid>.csv` with full before-and-after metrics.

## 3. Statistical Hypothesis Selection (`app/analytics/statistics_engine.py`)

- Runs **Shapiro-Wilk normality testing** ($W$-statistic and $p$-value) first.
- When `hypothesis_test="auto"`:
  - Selects parametric **Welch's Two-Sample $t$-Test** when normality holds ($p > 0.05$).
  - Selects non-parametric **Mann-Whitney $U$ Test** when data departs from normality ($p \le 0.05$).
  - Selects **One-Way ANOVA ($F$-Test)** when comparing 3+ categorical groups.
- Computes **Statsmodels OLS Linear Regression** ($\hat{y}_t = \beta_0 + \beta_1 t$) for monotonic trend detection.

## 4. Machine Learning Pipeline & Leakage Prevention (`app/machine_learning/ml_engine.py`)

- **Strict Split Before Featurization**:
  - For all supervised models, `train_test_split` is executed **before** fitting `SimpleImputer`, `StandardScaler`, or `OneHotEncoder`.
  - Preprocessing and estimation are encapsulated in a single `sklearn.pipeline.Pipeline` so test data is transformed strictly using training set parameters.
- **Chronological Validation for Time-Series**:
  - Temporal forecasting (`time_series_lag_rf` or `chronological_split=True`) sorts observations chronologically and sets `shuffle=False` during splitting so future observations never leak into training.
- **Supported Models**:
  - **Regression**: Linear Regression, Decision Tree Regressor, Random Forest Regressor, Chronological Time-Series Forecaster.
  - **Classification**: Logistic Regression, Decision Tree Classifier, Random Forest Classifier.
  - **Clustering**: K-Means with Silhouette curve ($k=2\dots 7$) and 2D PCA projection.
  - **Anomaly Detection**: Isolation Forest with decision function scoring.

## 5. Future Enhancements Roadmap

- Integration with real-time municipal IoT LoRaWAN rain-gauge and flood-depth ultrasonic sensors.
- Spatial kriging interpolation across irregular urban sensor grids.
- Automated hyperparameter tuning via Optuna with time-series cross-validation (`TimeSeriesSplit`).

