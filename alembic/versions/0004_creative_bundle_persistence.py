"""Create the author-controlled creative bundle persistence tables."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_creative_bundle_persistence"
down_revision = "0003_add_csrf_token_to_sessions"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    return table_name in sa.inspect(op.get_bind()).get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    indexes = sa.inspect(op.get_bind()).get_indexes(table_name)
    return index_name in {str(index["name"]) for index in indexes}


def _create_creative_briefs() -> None:
    if not _table_exists("creative_briefs"):
        op.create_table(
            "creative_briefs",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("owner_id", sa.String(length=36), nullable=True),
            sa.Column("guest_session_id", sa.String(length=36), nullable=True),
            sa.Column("story_format", sa.String(length=24), nullable=False),
            sa.Column("genre", sa.String(length=120), nullable=False),
            sa.Column("theme", sa.String(length=240), nullable=False),
            sa.Column("target_reader", sa.String(length=240), nullable=False),
            sa.Column("platform", sa.String(length=120), nullable=False),
            sa.Column("style", sa.String(length=240), nullable=False),
            sa.Column("premise", sa.Text(), nullable=False),
            sa.Column("preferences", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=24), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint(
                "((owner_id IS NOT NULL AND guest_session_id IS NULL) OR "
                "(owner_id IS NULL AND guest_session_id IS NOT NULL))",
                name="ck_creative_brief_single_owner",
            ),
            sa.CheckConstraint(
                "story_format IN ('short', 'medium', 'long_serial')",
                name="ck_creative_brief_story_format",
            ),
            sa.CheckConstraint(
                "status IN ('draft', 'generating', 'comparing', "
                "'confirmed', 'abandoned')",
                name="ck_creative_brief_status",
            ),
            sa.CheckConstraint("version >= 1", name="ck_creative_brief_version"),
            sa.ForeignKeyConstraint(
                ["guest_session_id"],
                ["sessions.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["owner_id"],
                ["owners.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("creative_briefs", "ix_creative_brief_owner_status"):
        op.create_index(
            "ix_creative_brief_owner_status",
            "creative_briefs",
            ["owner_id", "status"],
        )
    if not _index_exists("creative_briefs", "ix_creative_brief_guest_status"):
        op.create_index(
            "ix_creative_brief_guest_status",
            "creative_briefs",
            ["guest_session_id", "status"],
        )


def _create_idea_candidates() -> None:
    if not _table_exists("idea_candidates"):
        op.create_table(
            "idea_candidates",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("brief_id", sa.String(length=36), nullable=False),
            sa.Column("title", sa.String(length=240), nullable=False),
            sa.Column("logline", sa.Text(), nullable=False),
            sa.Column("core_conflict", sa.Text(), nullable=False),
            sa.Column("emotional_promise", sa.Text(), nullable=False),
            sa.Column("audience_fit", sa.Text(), nullable=False),
            sa.Column("scalability", sa.Text(), nullable=False),
            sa.Column("difficulty", sa.Text(), nullable=False),
            sa.Column("risk", sa.Text(), nullable=False),
            sa.Column("source", sa.String(length=16), nullable=False),
            sa.Column("source_job_id", sa.String(length=36), nullable=True),
            sa.Column("source_proposal_id", sa.String(length=36), nullable=True),
            sa.Column(
                "revision_of_candidate_id",
                sa.String(length=36),
                nullable=True,
            ),
            sa.Column("revision_number", sa.Integer(), nullable=False),
            sa.Column("lifecycle_status", sa.String(length=24), nullable=False),
            sa.Column("position", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint(
                "source IN ('author', 'rule', 'ai')",
                name="ck_idea_candidate_source",
            ),
            sa.CheckConstraint(
                "((source = 'ai' AND source_job_id IS NOT NULL AND "
                "source_proposal_id IS NOT NULL) OR "
                "(source <> 'ai' AND source_job_id IS NULL AND "
                "source_proposal_id IS NULL))",
                name="ck_idea_candidate_ai_evidence",
            ),
            sa.CheckConstraint(
                "revision_number >= 1",
                name="ck_idea_candidate_revision",
            ),
            sa.CheckConstraint(
                "lifecycle_status IN ('active', 'superseded')",
                name="ck_idea_candidate_lifecycle",
            ),
            sa.CheckConstraint("position >= 0", name="ck_idea_candidate_position"),
            sa.ForeignKeyConstraint(
                ["brief_id"],
                ["creative_briefs.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["revision_of_candidate_id"],
                ["idea_candidates.id"],
                ondelete="SET NULL",
            ),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("idea_candidates", "ix_idea_candidate_brief_position"):
        op.create_index(
            "ix_idea_candidate_brief_position",
            "idea_candidates",
            ["brief_id", "position"],
        )


def _create_selection_decisions() -> None:
    if not _table_exists("selection_decisions"):
        op.create_table(
            "selection_decisions",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("brief_id", sa.String(length=36), nullable=False),
            sa.Column(
                "decided_by_session_id",
                sa.String(length=36),
                nullable=True,
            ),
            sa.Column("base_brief_version", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint(
                "base_brief_version >= 1",
                name="ck_selection_decision_base_version",
            ),
            sa.ForeignKeyConstraint(
                ["brief_id"],
                ["creative_briefs.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["decided_by_session_id"],
                ["sessions.id"],
                ondelete="SET NULL",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("brief_id", name="uq_selection_decision_brief"),
        )


def _create_selection_decision_items() -> None:
    if not _table_exists("selection_decision_items"):
        op.create_table(
            "selection_decision_items",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("decision_id", sa.String(length=36), nullable=False),
            sa.Column("candidate_id", sa.String(length=36), nullable=False),
            sa.Column("role", sa.String(length=16), nullable=False),
            sa.Column("position", sa.Integer(), nullable=False),
            sa.CheckConstraint(
                "role IN ('selected', 'merged', 'rejected')",
                name="ck_selection_decision_item_role",
            ),
            sa.CheckConstraint(
                "position >= 0",
                name="ck_selection_decision_item_position",
            ),
            sa.ForeignKeyConstraint(
                ["candidate_id"],
                ["idea_candidates.id"],
                ondelete="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["decision_id"],
                ["selection_decisions.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "decision_id",
                "candidate_id",
                name="uq_selection_decision_candidate",
            ),
        )
    index_name = "uq_selection_decision_single_selected"
    if not _index_exists("selection_decision_items", index_name):
        selected = sa.text("role = 'selected'")
        op.create_index(
            index_name,
            "selection_decision_items",
            ["decision_id"],
            unique=True,
            sqlite_where=selected,
            postgresql_where=selected,
        )


def _create_story_seeds() -> None:
    if not _table_exists("story_seeds"):
        op.create_table(
            "story_seeds",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("brief_id", sa.String(length=36), nullable=False),
            sa.Column("decision_id", sa.String(length=36), nullable=False),
            sa.Column("project_id", sa.String(length=36), nullable=True),
            sa.Column("title", sa.String(length=240), nullable=False),
            sa.Column("premise", sa.Text(), nullable=False),
            sa.Column("core_conflict", sa.Text(), nullable=False),
            sa.Column("emotional_promise", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["brief_id"],
                ["creative_briefs.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["decision_id"],
                ["selection_decisions.id"],
                ondelete="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["project_id"],
                ["projects.id"],
                ondelete="SET NULL",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("brief_id", name="uq_story_seed_brief"),
            sa.UniqueConstraint("decision_id", name="uq_story_seed_decision"),
            sa.UniqueConstraint("project_id", name="uq_story_seed_project"),
        )


def _create_idempotency_records() -> None:
    if not _table_exists("idempotency_records"):
        op.create_table(
            "idempotency_records",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("owner_id", sa.String(length=36), nullable=True),
            sa.Column("guest_session_id", sa.String(length=36), nullable=True),
            sa.Column("operation", sa.String(length=80), nullable=False),
            sa.Column("idempotency_key", sa.String(length=128), nullable=False),
            sa.Column("request_hash", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=24), nullable=False),
            sa.Column("resource_type", sa.String(length=80), nullable=True),
            sa.Column("resource_id", sa.String(length=36), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.CheckConstraint(
                "((owner_id IS NOT NULL AND guest_session_id IS NULL) OR "
                "(owner_id IS NULL AND guest_session_id IS NOT NULL))",
                name="ck_idempotency_record_single_owner",
            ),
            sa.CheckConstraint(
                "status IN ('in_progress', 'completed', 'failed')",
                name="ck_idempotency_record_status",
            ),
            sa.ForeignKeyConstraint(
                ["guest_session_id"],
                ["sessions.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["owner_id"],
                ["owners.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
        )
    owner_index = "uq_idempotency_owner_operation_key"
    if not _index_exists("idempotency_records", owner_index):
        owner_present = sa.text("owner_id IS NOT NULL")
        op.create_index(
            owner_index,
            "idempotency_records",
            ["owner_id", "operation", "idempotency_key"],
            unique=True,
            sqlite_where=owner_present,
            postgresql_where=owner_present,
        )
    guest_index = "uq_idempotency_guest_operation_key"
    if not _index_exists("idempotency_records", guest_index):
        guest_present = sa.text("guest_session_id IS NOT NULL")
        op.create_index(
            guest_index,
            "idempotency_records",
            ["guest_session_id", "operation", "idempotency_key"],
            unique=True,
            sqlite_where=guest_present,
            postgresql_where=guest_present,
        )


def upgrade() -> None:
    _create_creative_briefs()
    _create_idea_candidates()
    _create_selection_decisions()
    _create_selection_decision_items()
    _create_story_seeds()
    _create_idempotency_records()


def downgrade() -> None:
    for table_name in (
        "idempotency_records",
        "story_seeds",
        "selection_decision_items",
        "selection_decisions",
        "idea_candidates",
        "creative_briefs",
    ):
        if _table_exists(table_name):
            op.drop_table(table_name)
