from datetime import datetime

from sqlalchemy import UUID, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class FeatureFlagsRecord(Base):
    __tablename__ = "feature_flags"

    id: Mapped[UUID] = mapped_column(UUID, primary_key=True)

    flag: Mapped[str] = mapped_column(String, primary_key=True)

    service: Mapped[str] = mapped_column(String, primary_key=True)

    environment: Mapped[str] = mapped_column(String, primary_key=True)

    enabled: Mapped[bool] = mapped_column(Boolean, primary_key=True)

    owner_team: Mapped[str] = mapped_column(String, primary_key=True)

    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    changed_by_deployment: Mapped[str] = mapped_column(String, primary_key=True)
