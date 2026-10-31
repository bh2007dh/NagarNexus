from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CleaningOperationRequest(BaseModel):
    missing_strategy: Optional[str] = Field(
        default="none",
        description="none | mean | median | mode | drop_rows | forward_fill",
    )
    target_columns: Optional[List[str]] = None
    remove_duplicates: bool = False
    convert_types: Optional[Dict[str, str]] = None  # {col: 'float' | 'int' | 'str' | 'datetime'}
    date_columns: Optional[List[str]] = None
    rename_columns: Optional[Dict[str, str]] = None
    outlier_action: Optional[str] = Field(
        default="none",
        description="none | clip_iqr | remove_iqr | clip_zscore",
    )
    outlier_columns: Optional[List[str]] = None
    scaling_method: Optional[str] = Field(
        default="none",
        description="none | normalize | standardize",
    )
    scaling_columns: Optional[List[str]] = None
    encoding_method: Optional[str] = Field(
        default="none",
        description="none | label | onehot",
    )
    encoding_columns: Optional[List[str]] = None


class EDAVisualizationRequest(BaseModel):
    chart_type: str = Field(
        default="histogram",
        description="histogram | bar | line | scatter | boxplot | pie | correlation_heatmap | distribution",
    )
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    group_by: Optional[str] = None
    filter_column: Optional[str] = None
    filter_value: Optional[str] = None
    bins: int = 20


class StatisticalCalculationRequest(BaseModel):
    target_column: str
    comparison_column: Optional[str] = None
    group_column: Optional[str] = None
    confidence_level: float = Field(default=0.95, ge=0.80, le=0.999)
    hypothesis_test: Optional[str] = Field(
        default="auto",
        description="auto | t_test_1samp | t_test_ind | mann_whitney | anova | pearson | spearman | normality_shapiro",
    )
    population_mean: Optional[float] = None

