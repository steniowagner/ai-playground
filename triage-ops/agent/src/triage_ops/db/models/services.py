from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ServicesRecord(Base):
    __tablename__ = "services"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    title: Mapped[str] = mapped_column(String, primary_key=True)

    services: Mapped[list[str]] = mapped_column(JSONB, nullable=False)

    environment: Mapped[str] = mapped_column(String, nullable=False)

    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    expected_effects: Mapped[list[str]] = mapped_column(JSONB, nullable=False)

    approved_by: Mapped[str] = mapped_column(String, nullable=False)

    status: Mapped[str] = mapped_column(String, nullable=False)
