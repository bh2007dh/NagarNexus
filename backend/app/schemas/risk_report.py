from typing import Optional, List
from pydantic import BaseModel


class RiskAnalyzeRequest(BaseModel):
    dataset_id: Optional[int] = None
    location_id: Optional[int] = None
    use_isolation_forest: bool = True
    contamination: float = 0.05


class InsightGenerateRequest(BaseModel):
    dataset_id: Optional[int] = None
    location_id: Optional[int] = None
    model_id: Optional[int] = None
    comparison_location_ids: Optional[List[int]] = None


class ReportGenerateRequest(BaseModel):
    title: str
    report_type: str = "dataset"  # dataset | eda | statistical | ml | prediction | comparison | risk
    dataset_id: Optional[int] = None
    model_id: Optional[int] = None
    location_ids: Optional[List[int]] = None
    include_csv_export: bool = True
    notes: Optional[str] = None

