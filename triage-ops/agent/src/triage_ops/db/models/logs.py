from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class LogsRecord(Base):
    __tablename__ = "logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    timestamp = Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    service: Mapped[str] = mapped_column(String, nullable=False)

    environment: Mapped[str] = mapped_column(String, nullable=False)

    severity: Mapped[str] = mapped_column(String, nullable=False)

    message: Mapped[str] = mapped_column(String, nullable=False)

    trace_id: Mapped[str] = mapped_column(String, nullable=True)

    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
