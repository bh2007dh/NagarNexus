# NagarNexus Machine Learning Models Directory

- `trained/`: Persisted `.joblib` scikit-learn `Pipeline` bundles containing fitted `ColumnTransformer` preprocessors, trained estimators, feature defaults, residual uncertainty metadata, and semantic version tags.
- `evaluation/`: Companion JSON files storing holdout validation metrics (`MAE`, `MSE`, `RMSE`, `R2_score`, `accuracy`, `precision`, `recall`, `f1_score`, `confusion_matrix`, `silhouette_score`, or `anomaly_ratio_pct`).

## Leak-Free Training Guarantee

Every supervised model in NagarNexus splits the dataset into `X_train` and `X_test` **before** fitting imputation, scaling, and categorical encoding steps inside a unified `sklearn.pipeline.Pipeline`. For temporal forecasting, chronological ordering (`shuffle=False`) is enforced to prevent future-data leakage.

