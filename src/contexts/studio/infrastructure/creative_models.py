from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.contexts.studio.infrastructure.model_base import Base

__all__ = [
    "CreativeBriefRecord",
    "IdeaCandidateRecord",
    "IdempotencyRecord",
    "SelectionDecisionItemRecord",
    "SelectionDecisionRecord",
    "StorySeedRecord",
]


class CreativeBriefRecord(Base):
    __tablename__ = "creative_briefs"
    __table_args__ = (
        CheckConstraint(
            "((owner_id IS NOT NULL AND guest_session_id IS NULL) OR "
            "(owner_id IS NULL AND guest_session_id IS NOT NULL))",
            name="ck_creative_brief_single_owner",
        ),
        CheckConstraint(
            "story_format IN ('short', 'medium', 'long_serial')",
            name="ck_creative_brief_story_format",
        ),
        CheckConstraint(
            "status IN ('draft', 'generating', 'comparing', 'confirmed', 'abandoned')",
            name="ck_creative_brief_status",
        ),
        CheckConstraint("version >= 1", name="ck_creative_brief_version"),
        Index("ix_creative_brief_owner_status", "owner_id", "status"),
        Index("ix_creative_brief_guest_status", "guest_session_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str | None] = mapped_column(
        ForeignKey("owners.id", ondelete="CASCADE"), nullable=True
    )
    guest_session_id: Mapped[str | None] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=True
    )
    story_format: Mapped[str] = mapped_column(String(24), nullable=False)
    genre: Mapped[str] = mapped_column(String(120), nullable=False)
    theme: Mapped[str] = mapped_column(String(240), nullable=False)
    target_reader: Mapped[str] = mapped_column(String(240), nullable=False)
    platform: Mapped[str] = mapped_column(String(120), nullable=False)
    style: Mapped[str] = mapped_column(String(240), nullable=False)
    premise: Mapped[str] = mapped_column(Text, nullable=False)
    preferences: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class IdeaCandidateRecord(Base):
    __tablename__ = "idea_candidates"
    __table_args__ = (
        CheckConstraint(
            "source IN ('author', 'rule', 'ai')",
            name="ck_idea_candidate_source",
        ),
        CheckConstraint(
            "((source = 'ai' AND source_job_id IS NOT NULL AND "
            "source_proposal_id IS NOT NULL) OR "
            "(source <> 'ai' AND source_job_id IS NULL AND "
            "source_proposal_id IS NULL))",
            name="ck_idea_candidate_ai_evidence",
        ),
        CheckConstraint("revision_number >= 1", name="ck_idea_candidate_revision"),
        CheckConstraint(
            "lifecycle_status IN ('active', 'superseded')",
            name="ck_idea_candidate_lifecycle",
        ),
        CheckConstraint("position >= 0", name="ck_idea_candidate_position"),
        Index("ix_idea_candidate_brief_position", "brief_id", "position"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    brief_id: Mapped[str] = mapped_column(
        ForeignKey("creative_briefs.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    logline: Mapped[str] = mapped_column(Text, nullable=False)
    core_conflict: Mapped[str] = mapped_column(Text, nullable=False)
    emotional_promise: Mapped[str] = mapped_column(Text, nullable=False)
    audience_fit: Mapped[str] = mapped_column(Text, nullable=False)
    scalability: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(Text, nullable=False)
    risk: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    source_job_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_proposal_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    revision_of_candidate_id: Mapped[str | None] = mapped_column(
        ForeignKey("idea_candidates.id", ondelete="SET NULL"), nullable=True
    )
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    lifecycle_status: Mapped[str] = mapped_column(String(24), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class SelectionDecisionRecord(Base):
    __tablename__ = "selection_decisions"
    __table_args__ = (
        CheckConstraint(
            "base_brief_version >= 1",
            name="ck_selection_decision_base_version",
        ),
        UniqueConstraint("brief_id", name="uq_selection_decision_brief"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    brief_id: Mapped[str] = mapped_column(
        ForeignKey("creative_briefs.id", ondelete="CASCADE"), nullable=False
    )
    decided_by_session_id: Mapped[str | None] = mapped_column(
        ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True
    )
    base_brief_version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class SelectionDecisionItemRecord(Base):
    __tablename__ = "selection_decision_items"
    __table_args__ = (
        CheckConstraint(
            "role IN ('selected', 'merged', 'rejected')",
            name="ck_selection_decision_item_role",
        ),
        CheckConstraint("position >= 0", name="ck_selection_decision_item_position"),
        UniqueConstraint(
            "decision_id",
            "candidate_id",
            name="uq_selection_decision_candidate",
        ),
        Index(
            "uq_selection_decision_single_selected",
            "decision_id",
            unique=True,
            sqlite_where=text("role = 'selected'"),
            postgresql_where=text("role = 'selected'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    decision_id: Mapped[str] = mapped_column(
        ForeignKey("selection_decisions.id", ondelete="CASCADE"), nullable=False
    )
    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("idea_candidates.id", ondelete="RESTRICT"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)


class StorySeedRecord(Base):
    __tablename__ = "story_seeds"
    __table_args__ = (
        UniqueConstraint("brief_id", name="uq_story_seed_brief"),
        UniqueConstraint("decision_id", name="uq_story_seed_decision"),
        UniqueConstraint("project_id", name="uq_story_seed_project"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    brief_id: Mapped[str] = mapped_column(
        ForeignKey("creative_briefs.id", ondelete="CASCADE"), nullable=False
    )
    decision_id: Mapped[str] = mapped_column(
        ForeignKey("selection_decisions.id", ondelete="RESTRICT"), nullable=False
    )
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    premise: Mapped[str] = mapped_column(Text, nullable=False)
    core_conflict: Mapped[str] = mapped_column(Text, nullable=False)
    emotional_promise: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        CheckConstraint(
            "((owner_id IS NOT NULL AND guest_session_id IS NULL) OR "
            "(owner_id IS NULL AND guest_session_id IS NOT NULL))",
            name="ck_idempotency_record_single_owner",
        ),
        CheckConstraint(
            "status IN ('in_progress', 'completed', 'failed')",
            name="ck_idempotency_record_status",
        ),
        Index(
            "uq_idempotency_owner_operation_key",
            "owner_id",
            "operation",
            "idempotency_key",
            unique=True,
            sqlite_where=text("owner_id IS NOT NULL"),
            postgresql_where=text("owner_id IS NOT NULL"),
        ),
        Index(
            "uq_idempotency_guest_operation_key",
            "guest_session_id",
            "operation",
            "idempotency_key",
            unique=True,
            sqlite_where=text("guest_session_id IS NOT NULL"),
            postgresql_where=text("guest_session_id IS NOT NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str | None] = mapped_column(
        ForeignKey("owners.id", ondelete="CASCADE"), nullable=True
    )
    guest_session_id: Mapped[str | None] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=True
    )
    operation: Mapped[str] = mapped_column(String(80), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
