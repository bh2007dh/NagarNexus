from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class DatasetColumnResponse(BaseModel):
    id: int
    column_name: str
    data_type: str
    raw_dtype: Optional[str] = None
    missing_count: int
    unique_count: int
    sample_values: Optional[List[Any]] = None

    model_config = ConfigDict(from_attributes=True)


class DatasetResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    file_type: str
    file_size: int
    row_count: int
    column_count: int
    source_type: str
    is_public: bool
    quality_score: Optional[float] = 100.0
    profile_json: Optional[Dict[str, Any]] = None
    upload_timestamp: datetime
    processing_status: str
    has_processed_version: bool = False
    columns: List[DatasetColumnResponse] = []

    model_config = ConfigDict(from_attributes=True)

