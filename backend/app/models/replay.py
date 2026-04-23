import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Float, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class Replay(Base):
    __tablename__ = "replays"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_log_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("request_logs.id", ondelete="CASCADE"), nullable=False)

    # Overrides applied for this replay
    override_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    override_headers: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    override_body: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Replay result
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_headers: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)  # pending | success | failed

    replayed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    original_log: Mapped["RequestLog"] = relationship("RequestLog", back_populates="replays")
