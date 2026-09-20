import json
from logging import Logger
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from triage_ops.db import FeatureFlagsRecord, SessionFactory
from triage_ops.repositories.feature_flags import (
    FeatureFlag,
)

from .exceptions import SeedDatabaseException

FEATURE_FLAGS_FILE = (
    Path(__file__).resolve().parents[4] / "data" / "fixtures" / "feature_flags.json"
)

from triage_ops.repositories.feature_flags import FeatureFlagsFixture


def parse_fixture(fixture_json: Any) -> FeatureFlagsFixture:
    try:
        return FeatureFlagsFixture.model_validate(fixture_json)
    except ValidationError as exc:
        raise SeedDatabaseException(
            "Feature-flags repository data is invalid."
        ) from exc


def read_feature_flags() -> list[FeatureFlag]:
    try:
        with open(FEATURE_FLAGS_FILE, "r", encoding="utf-8") as f:
            feature_flags_json = json.load(f)
    except UnicodeDecodeError as exc:
        raise SeedDatabaseException(
            "Feature-flags repository contains invalid text data."
        ) from exc
    except json.JSONDecodeError as exc:
        raise SeedDatabaseException(
            "Feature-flags repository contains invalid JSON."
        ) from exc
    except OSError as exc:
        raise SeedDatabaseException("Feature-flags repository is unavailable.") from exc

    fixture = parse_fixture(feature_flags_json)
    return fixture.feature_flags


def save_feature_flags(
    session_factory: SessionFactory, feature_flags: list[FeatureFlag]
) -> None:
    records = [
        FeatureFlagsRecord(
            id=uuid4(),
            flag=feature_flag.flag,
            service=feature_flag.service,
            environment=feature_flag.environment,
            enabled=feature_flag.enabled,
            owner_team=feature_flag.owner_team,
            changed_at=feature_flag.changed_at,
            changed_by_deployment=feature_flag.changed_by_deployment,
        )
        for feature_flag in feature_flags
    ]

    try:
        with session_factory.begin() as session:
            session.execute(delete(FeatureFlagsRecord))
            session.add_all(records)
    except SQLAlchemyError as exc:
        raise SeedDatabaseException("Failed to save incident fixture data.") from exc


def seed_feature_flags(session_factory: SessionFactory, logger: Logger) -> None:
    feature_flags = read_feature_flags()
    save_feature_flags(session_factory, feature_flags)
    logger.warning("Feature-flags seeded ✓")
