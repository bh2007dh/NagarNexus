from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class MLModel(Base):
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    model_name = Column(String(200), nullable=False, index=True)
    model_type = Column(String(100), nullable=False, index=True)  # regression | classification | clustering | anomaly_detection | time_series
    algorithm = Column(String(100), nullable=False)  # linear_regression, random_forest_regressor, etc.
    model_version = Column(String(50), nullable=False, default="1.0.0")
    feature_columns = Column(JSON, nullable=False)
    target_column = Column(String(200), nullable=True)
    hyperparameters_json = Column(JSON, nullable=True)
    metrics_json = Column(JSON, nullable=False)
    model_path = Column(String(500), nullable=False)
    is_public = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="ml_models")
    dataset = relationship("Dataset", back_populates="ml_models")
    predictions = relationship("Prediction", back_populates="model", cascade="all, delete-orphan")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("ml_models.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    category = Column(String(100), nullable=True, default="environmental")
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    input_json = Column(JSON, nullable=False)
    predicted_value = Column(String(255), nullable=False)
    numeric_prediction = Column(Float, nullable=True)
    actual_value = Column(Float, nullable=True)
    confidence_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    model = relationship("MLModel", back_populates="predictions")
    user = relationship("User", back_populates="predictions")

    __table_args__ = (
        Index("ix_predictions_model_created", "model_id", "created_at"),
    )

