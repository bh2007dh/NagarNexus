from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, BigInteger, Float, DateTime, ForeignKey, JSON, Boolean, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    file_path = Column(String(500), nullable=False)
    processed_file_path = Column(String(500), nullable=True)
    file_type = Column(String(50), nullable=False)
    file_size = Column(BigInteger, nullable=False, default=0)
    row_count = Column(Integer, nullable=False, default=0)
    column_count = Column(Integer, nullable=False, default=0)
    source_type = Column(String(100), nullable=False, default="user_upload")  # user_upload | sample | open_meteo | openaq
    is_public = Column(Boolean, default=False, nullable=False)
    quality_score = Column(Float, nullable=True, default=100.0)
    profile_json = Column(JSON, nullable=True)
    upload_timestamp = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    processing_status = Column(String(50), nullable=False, default="ready")

    owner = relationship("User", back_populates="datasets")
    columns = relationship("DatasetColumn", back_populates="dataset", cascade="all, delete-orphan")
    observations = relationship("Observation", back_populates="dataset", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="dataset", cascade="all, delete-orphan")
    ml_models = relationship("MLModel", back_populates="dataset", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_datasets_user_source", "user_id", "source_type"),
    )


class DatasetColumn(Base):
    __tablename__ = "dataset_columns"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    column_name = Column(String(255), nullable=False)
    data_type = Column(String(100), nullable=False)  # numerical | categorical | datetime | boolean
    raw_dtype = Column(String(100), nullable=True)
    missing_count = Column(Integer, nullable=False, default=0)
    unique_count = Column(Integer, nullable=False, default=0)
    sample_values = Column(JSON, nullable=True)

    dataset = relationship("Dataset", back_populates="columns")

