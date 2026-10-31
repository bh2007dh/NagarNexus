from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class RiskAlert(Base):
    __tablename__ = "risk_alerts"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="CASCADE"), nullable=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True, index=True)
    risk_category = Column(String(100), nullable=False, default="Environmental Threshold")
    indicator = Column(String(100), nullable=False, index=True)
    risk_level = Column(String(50), nullable=False, index=True)  # Low | Moderate | High | Critical
    measured_value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    unit = Column(String(50), nullable=True, default="")
    explanation = Column(Text, nullable=False)
    suggested_action = Column(Text, nullable=True)
    data_source = Column(String(255), nullable=True, default="NagarNexus Statistical & ML Risk Engine")
    threshold_type = Column(String(100), nullable=True, default="WHO/CPCB Reference & Project Statistical Threshold")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    location = relationship("Location", back_populates="risk_alerts")

    __table_args__ = (
        Index("ix_risk_alerts_level_created", "risk_level", "created_at"),
    )

