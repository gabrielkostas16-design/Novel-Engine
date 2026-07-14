from __future__ import annotations

from dataclasses import asdict
from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from src.contexts.studio.application.ports.creative_repository import CreativeBundleDto
from src.contexts.studio.domain.creative import (
    CreativeBrief,
    IdeaCandidate,
)
from src.contexts.studio.domain.exceptions import (
    InvalidOperation,
    NotFound,
    StateConflict,
)
from src.contexts.studio.infrastructure.creative_models import (
    CreativeBriefRecord,
    IdeaCandidateRecord,
    IdempotencyRecord,
)
from src.contexts.studio.infrastructure.repository.common import (
    StudioDatabase,
    new_id,
)
from src.contexts.studio.infrastructure.repository.creative_mapping import _bundle_dto


def _scoped_brief_statement(
    brief_id: str,
    owner_id: str | None,
    guest_session_id: str | None,
) -> Select[tuple[CreativeBriefRecord]]:
    statement = select(CreativeBriefRecord).where(CreativeBriefRecord.id == brief_id)
    if owner_id:
        return statement.where(CreativeBriefRecord.owner_id == owner_id)
    return statement.where(CreativeBriefRecord.guest_session_id == guest_session_id)


def _brief_record(
    session: Session,
    brief_id: str,
    owner_id: str | None,
    guest_session_id: str | None,
    *,
    lock: bool = False,
) -> CreativeBriefRecord:
    statement = _scoped_brief_statement(brief_id, owner_id, guest_session_id)
    record = session.scalar(statement.with_for_update() if lock else statement)
    if record is None:
        raise NotFound("Creative brief not found.")
    return record


def _check_version(record: CreativeBriefRecord, base_version: int) -> None:
    if record.version != base_version:
        raise StateConflict(
            "Creative brief changed since the requested base version.",
            current_version=record.version,
        )


def _idempotency_record(
    session: Session,
    *,
    owner_id: str | None,
    guest_session_id: str | None,
    operation: str,
    key: str,
) -> IdempotencyRecord | None:
    statement = select(IdempotencyRecord).where(
        IdempotencyRecord.operation == operation,
        IdempotencyRecord.idempotency_key == key,
    )
    if owner_id:
        statement = statement.where(IdempotencyRecord.owner_id == owner_id)
    else:
        statement = statement.where(
            IdempotencyRecord.guest_session_id == guest_session_id
        )
    return session.scalar(statement)


class CreativeDraftRepositoryMixin:
    database: StudioDatabase

    def get_creative_bundle(
        self,
        brief_id: str,
        *,
        owner_id: str | None,
        guest_session_id: str | None,
    ) -> CreativeBundleDto:
        with self.database.session() as session:
            brief = _brief_record(session, brief_id, owner_id, guest_session_id)
            return _bundle_dto(session, brief)

    def create_creative_brief(
        self,
        *,
        owner_id: str | None,
        guest_session_id: str | None,
        brief: CreativeBrief,
        idempotency_key: str,
        request_hash: str,
        now: datetime,
    ) -> CreativeBundleDto:
        with self.database.session() as session:
            replay = _idempotency_record(
                session,
                owner_id=owner_id,
                guest_session_id=guest_session_id,
                operation="create_creative_brief",
                key=idempotency_key,
            )
            if replay:
                return self._replay_bundle(session, replay, request_hash)
            record = CreativeBriefRecord(
                **asdict(brief),
                owner_id=owner_id,
                guest_session_id=guest_session_id,
                status="draft",
                version=1,
                created_at=now,
                updated_at=now,
            )
            session.add(record)
            session.flush()
            session.add(
                IdempotencyRecord(
                    id=new_id(),
                    owner_id=owner_id,
                    guest_session_id=guest_session_id,
                    operation="create_creative_brief",
                    idempotency_key=idempotency_key,
                    request_hash=request_hash,
                    status="completed",
                    resource_type="creative_brief",
                    resource_id=record.id,
                    created_at=now,
                    completed_at=now,
                )
            )
            return _bundle_dto(session, record)

    def update_creative_brief(
        self,
        brief_id: str,
        *,
        owner_id: str | None,
        guest_session_id: str | None,
        brief: CreativeBrief,
        base_version: int,
        now: datetime,
    ) -> CreativeBundleDto:
        with self.database.session() as session:
            record = _brief_record(
                session, brief_id, owner_id, guest_session_id, lock=True
            )
            _check_version(record, base_version)
            self._require_editable(record)
            for field_name in (
                "story_format",
                "genre",
                "theme",
                "target_reader",
                "platform",
                "style",
                "premise",
                "preferences",
            ):
                setattr(record, field_name, getattr(brief, field_name))
            record.version += 1
            record.updated_at = now
            return _bundle_dto(session, record)

    def replace_rule_candidates(
        self,
        brief_id: str,
        *,
        owner_id: str | None,
        guest_session_id: str | None,
        candidates: tuple[IdeaCandidate, ...],
        base_version: int,
        now: datetime,
    ) -> CreativeBundleDto:
        with self.database.session() as session:
            brief = _brief_record(
                session, brief_id, owner_id, guest_session_id, lock=True
            )
            _check_version(brief, base_version)
            self._require_editable(brief)
            active = session.scalars(
                select(IdeaCandidateRecord).where(
                    IdeaCandidateRecord.brief_id == brief.id,
                    IdeaCandidateRecord.lifecycle_status == "active",
                )
            ).all()
            for old in active:
                old.lifecycle_status = "superseded"
            for position, candidate in enumerate(candidates):
                session.add(
                    IdeaCandidateRecord(
                        **asdict(candidate),
                        revision_of_candidate_id=None,
                        revision_number=1,
                        lifecycle_status="active",
                        position=position,
                        created_at=now,
                    )
                )
            brief.status = "comparing"
            brief.version += 1
            brief.updated_at = now
            session.flush()
            return _bundle_dto(session, brief)

    @staticmethod
    def _require_editable(record: CreativeBriefRecord) -> None:
        if record.status in {"confirmed", "abandoned"}:
            raise InvalidOperation("Creative brief is no longer editable.")

    @staticmethod
    def _replay_bundle(
        session: Session,
        record: IdempotencyRecord,
        request_hash: str,
    ) -> CreativeBundleDto:
        if record.request_hash != request_hash:
            raise StateConflict("Idempotency key was reused with different content.")
        if record.status != "completed" or not record.resource_id:
            raise StateConflict("The idempotent command is not complete.")
        brief = session.get(CreativeBriefRecord, record.resource_id)
        if brief is None:
            raise InvalidOperation("Idempotency record points to a missing brief.")
        return _bundle_dto(session, brief)


__all__ = [
    "CreativeDraftRepositoryMixin",
    "_brief_record",
    "_check_version",
    "_idempotency_record",
]
