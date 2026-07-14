from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from typing import Protocol, cast

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

from src.contexts.studio.infrastructure.models import Base

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


def test_creative_migration_matches_base_approved_digest() -> None:
    digest, relative_path = APPROVAL_PATH.read_text().split()

    assert relative_path == "alembic/versions/0004_creative_bundle_persistence.py"
    assert hashlib.sha256(MIGRATION_PATH.read_bytes()).hexdigest() == digest


def test_creative_migration_upgrades_and_downgrades_existing_schema(
    tmp_path: Path,
) -> None:
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'migration.sqlite3'}")
    migration = _load_migration()

    with engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        Base.metadata.create_all(connection)
        original_tables = set(sa.inspect(connection).get_table_names())
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
