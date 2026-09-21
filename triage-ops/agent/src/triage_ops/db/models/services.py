from typing import Any

from sqlalchemy import UUID, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ServicesRecord(Base):
    __tablename__ = "services"

    id: Mapped[UUID] = mapped_column(UUID, primary_key=True)

    service: Mapped[str] = mapped_column(String, nullable=False)

    display_name: Mapped[str] = mapped_column(String, nullable=False)

    description: Mapped[str] = mapped_column(String, nullable=False)

    tier: Mapped[int] = mapped_column(Integer, nullable=False)

    owner_team: Mapped[str] = mapped_column(String, nullable=False)

    on_call: Mapped[str] = mapped_column(String, nullable=False)

    environments: Mapped[list[str]] = mapped_column(JSONB, nullable=False)

    dependencies: Mapped[list[str]] = mapped_column(JSONB, nullable=False)

    runbook_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False)

    slo: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
