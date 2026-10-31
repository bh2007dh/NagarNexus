from typing import List, Optional
from pydantic import BaseModel


class LocationCreateRequest(BaseModel):
    name: str
    city: str
    state: Optional[str] = "Tamil Nadu"
    country: Optional[str] = "India"
    latitude: float
    longitude: float
    geographical_resolution: str = "locality"
    zone_type: Optional[str] = "Urban Mixed"


class ComparisonRunRequest(BaseModel):
    location_ids: List[int]
    indicators: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

