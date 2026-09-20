from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class IncidentsRecord(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    title: Mapped[str] = mapped_column(String, nullable=False)

    environment: Mapped[str] = mapped_column(String, nullable=False)

    primary_service: Mapped[str] = mapped_column(String, nullable=False)

    alert_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    status: Mapped[str] = mapped_column(String, nullable=False)

    severity: Mapped[str] = mapped_column(String, nullable=False)

    reported_symptoms: Mapped[list[str]] = mapped_column(JSONB, nullable=False)

    alert: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
