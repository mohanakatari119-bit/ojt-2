import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Float, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Condition: field operator threshold  e.g. status_code >= 500
    condition_field: Mapped[str] = mapped_column(String(64), nullable=False)   # status_code | latency_ms | error
    condition_operator: Mapped[str] = mapped_column(String(8), nullable=False)  # >=, <=, ==, !=, >  <
    condition_value: Mapped[str] = mapped_column(String(128), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    service: Mapped["Service"] = relationship("Service", back_populates="alerts")
    events: Mapped[list["AlertEvent"]] = relationship("AlertEvent", back_populates="alert", cascade="all, delete-orphan")
