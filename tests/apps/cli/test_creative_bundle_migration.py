from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from typing import Protocol, cast

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

from src.contexts.studio.infrastructure.models import (
    Base,
    CreativeBriefRecord,
    IdeaCandidateRecord,
    IdempotencyRecord,
    SelectionDecisionItemRecord,
    SelectionDecisionRecord,
    StorySeedRecord,
)

ROOT = Path(__file__).resolve().parents[3]
MIGRATION_PATH = ROOT / "alembic/versions/0004_creative_bundle_persistence.py"
APPROVAL_PATH = ROOT / "scripts/ai/approved_migrations.txt"
CREATIVE_TABLES = {
    "creative_briefs",
    "idea_candidates",
    "selection_decisions",
    "selection_decision_items",
    "story_seeds",
    "idempotency_records",
}
CREATIVE_MODELS = {
    "creative_briefs": CreativeBriefRecord,
    "idea_candidates": IdeaCandidateRecord,
    "selection_decisions": SelectionDecisionRecord,
    "selection_decision_items": SelectionDecisionItemRecord,
    "story_seeds": StorySeedRecord,
    "idempotency_records": IdempotencyRecord,
}


class MigrationModule(Protocol):
    def upgrade(self) -> None: ...

    def downgrade(self) -> None: ...


def _load_migration() -> MigrationModule:
    spec = importlib.util.spec_from_file_location("migration_0004", MIGRATION_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load the approved creative migration.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(MigrationModule, module)


def _create_existing_schema(connection: sa.Connection) -> set[str]:
    tables = [
        table
        for name, table in Base.metadata.tables.items()
        if name not in CREATIVE_TABLES
    ]
    Base.metadata.create_all(connection, tables=tables)
    return set(sa.inspect(connection).get_table_names())


def _normalize_sql(value: object) -> str:
    return " ".join(str(value).split())


def _schema_snapshot(connection: sa.Connection) -> dict[str, object]:
    inspector = sa.inspect(connection)
    snapshot: dict[str, object] = {}
    for table_name in sorted(CREATIVE_TABLES):
        snapshot[table_name] = {
            "columns": sorted(
                (
                    column["name"],
                    str(column["type"]),
                    column["nullable"],
                )
                for column in inspector.get_columns(table_name)
            ),
            "primary_key": tuple(
                inspector.get_pk_constraint(table_name)["constrained_columns"]
            ),
            "checks": sorted(
                (constraint["name"], _normalize_sql(constraint["sqltext"]))
                for constraint in inspector.get_check_constraints(table_name)
            ),
            "foreign_keys": sorted(
                (
                    tuple(foreign_key["constrained_columns"]),
                    foreign_key["referred_table"],
                    tuple(foreign_key["referred_columns"]),
                    foreign_key["options"].get("ondelete"),
                )
                for foreign_key in inspector.get_foreign_keys(table_name)
            ),
            "unique_constraints": sorted(
                (
                    constraint["name"],
                    tuple(constraint["column_names"]),
                )
                for constraint in inspector.get_unique_constraints(table_name)
            ),
            "indexes": sorted(
                (
                    index["name"],
                    tuple(index["column_names"]),
                    index["unique"],
                    _normalize_sql(
                        index.get("dialect_options", {}).get("sqlite_where", "")
                    ),
                )
                for index in inspector.get_indexes(table_name)
            ),
        }
    return snapshot


def test_creative_migration_matches_base_approved_digest() -> None:
    digest, relative_path = APPROVAL_PATH.read_text().split()

    assert relative_path == "alembic/versions/0004_creative_bundle_persistence.py"
    assert hashlib.sha256(MIGRATION_PATH.read_bytes()).hexdigest() == digest


def test_creative_models_are_registered_on_the_canonical_base() -> None:
    assert set(CREATIVE_MODELS) == CREATIVE_TABLES
    for table_name, model in CREATIVE_MODELS.items():
        assert model.__table__ is Base.metadata.tables[table_name]


def test_creative_orm_schema_matches_the_approved_migration(tmp_path: Path) -> None:
    orm_engine = sa.create_engine(f"sqlite:///{tmp_path / 'orm.sqlite3'}")
    migration_engine = sa.create_engine(f"sqlite:///{tmp_path / 'migration.sqlite3'}")
    migration = _load_migration()

    with orm_engine.begin() as orm_connection:
        orm_connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        Base.metadata.create_all(orm_connection)
        orm_snapshot = _schema_snapshot(orm_connection)

    with migration_engine.begin() as migration_connection:
        migration_connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        _create_existing_schema(migration_connection)
        context = MigrationContext.configure(migration_connection)
        with Operations.context(context):
            migration.upgrade()
        migration_snapshot = _schema_snapshot(migration_connection)

    assert orm_snapshot == migration_snapshot


def test_creative_migration_upgrades_and_downgrades_existing_schema(
    tmp_path: Path,
) -> None:
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'migration.sqlite3'}")
    migration = _load_migration()

    with engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        original_tables = _create_existing_schema(connection)
        context = MigrationContext.configure(connection)

        with Operations.context(context):
            migration.upgrade()
        assert set(sa.inspect(connection).get_table_names()) >= CREATIVE_TABLES

        with Operations.context(context):
            migration.downgrade()
        downgraded_tables = set(sa.inspect(connection).get_table_names())
        assert not CREATIVE_TABLES & downgraded_tables
        assert original_tables <= downgraded_tables

        with Operations.context(context):
            migration.upgrade()
        assert set(sa.inspect(connection).get_table_names()) >= CREATIVE_TABLES
        assert connection.exec_driver_sql("PRAGMA integrity_check").scalar_one() == "ok"
