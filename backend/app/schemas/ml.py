from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MLTrainRequest(BaseModel):
    dataset_id: int
    model_name: Optional[str] = None
    algorithm: str = Field(
        ...,
        description=(
            "linear_regression | decision_tree_regressor | random_forest_regressor | "
            "logistic_regression | decision_tree_classifier | random_forest_classifier | "
            "kmeans | isolation_forest | time_series_lag_rf"
        ),
    )
    feature_columns: List[str]
    target_column: Optional[str] = None
    test_size: float = Field(default=0.2, ge=0.1, le=0.5)
    chronological_split: bool = False
    date_column: Optional[str] = None
    n_clusters: int = Field(default=3, ge=2, le=12)
    contamination: float = Field(default=0.05, ge=0.01, le=0.4)
    n_estimators: int = Field(default=100, ge=10, le=500)
    max_depth: Optional[int] = Field(default=10, ge=2, le=50)


class MLPredictRequest(BaseModel):
    features: Dict[str, Any]
    category: Optional[str] = "environmental"
    location_id: Optional[int] = None
    actual_value: Optional[float] = None


class PredictiveRunRequest(BaseModel):
    model_id: int
    features: Dict[str, Any]
    category: str = "temperature"
    location_id: Optional[int] = None
    actual_value: Optional[float] = None
    horizon_steps: int = Field(default=7, ge=1, le=30)

