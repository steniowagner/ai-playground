from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class DeploymentsRecord(Base):
    __tablename__ = "deployments"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    service: Mapped[str] = mapped_column(String, nullable=False)

    environment: Mapped[str] = mapped_column(String, nullable=False)

    version: Mapped[str] = mapped_column(String, nullable=False)

    commit: Mapped[str] = mapped_column(String, nullable=False)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    status: Mapped[str] = mapped_column(String, nullable=False)

    summary: Mapped[str] = mapped_column(String, nullable=False)
