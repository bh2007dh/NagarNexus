from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    city = Column(String(150), nullable=False, index=True)
    state = Column(String(150), nullable=True, default="Tamil Nadu")
    country = Column(String(100), nullable=True, default="India")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geographical_resolution = Column(String(100), nullable=False, default="locality")  # station | locality | city | grid_cell
    elevation_m = Column(Float, nullable=True)
    zone_type = Column(String(100), nullable=True, default="Urban Mixed")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    observations = relationship("Observation", back_populates="location", cascade="all, delete-orphan")
    risk_alerts = relationship("RiskAlert", back_populates="location", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_locations_city_name", "city", "name"),
        Index("ix_locations_coords", "latitude", "longitude"),
    )


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(200), nullable=False, index=True)
    source_url = Column(String(500), nullable=False)
    source_type = Column(String(100), nullable=False)  # api | sample_synthetic | government | user_upload
    retrieved_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    attribution = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    observations = relationship("Observation", back_populates="source")


class Observation(Base):
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True, index=True)
    indicator = Column(String(100), nullable=False, index=True)  # temperature_c, rainfall_mm, humidity_pct, pm25, pm10, no2, o3, aqi, wind_speed_kmh
    value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    observed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    location = relationship("Location", back_populates="observations")
    dataset = relationship("Dataset", back_populates="observations")
    source = relationship("DataSource", back_populates="observations")

    __table_args__ = (
        Index("ix_observations_loc_ind_time", "location_id", "indicator", "observed_at"),
    )

