from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.contexts.studio.application.ports.creative_repository import CreativeBundleDto
from src.contexts.studio.application.ports.studio_repository import ProjectDto
from src.contexts.studio.domain.creative import SelectionDecision, StorySeed
from src.contexts.studio.domain.exceptions import InvalidOperation
from src.contexts.studio.infrastructure.creative_models import (
    IdeaCandidateRecord,
    IdempotencyRecord,
    SelectionDecisionItemRecord,
    SelectionDecisionRecord,
    StorySeedRecord,
)
from src.contexts.studio.infrastructure.repository.common import (
    StudioDatabase,
    dump_json,
    new_id,
)
from src.contexts.studio.infrastructure.repository.creative import (
    CreativeDraftRepositoryMixin,
    _brief_record,
    _check_version,
    _idempotency_record,
)
from src.contexts.studio.infrastructure.repository.creative_mapping import _bundle_dto


class CreativeRepositoryMixin(CreativeDraftRepositoryMixin):
    database: StudioDatabase

    if TYPE_CHECKING:

        def create_project(
            self,
            *,
            owner_id: str | None,
            guest_session_id: str | None,
            title: str,
            description: str,
            settings_json: str,
            now: datetime,
            create_seed: bool = True,
            session: Session | None = None,
        ) -> ProjectDto: ...

    def confirm_creative_brief(
        self,
        brief_id: str,
        *,
        owner_id: str | None,
        guest_session_id: str | None,
        decision: SelectionDecision,
        story_seed: StorySeed,
        base_version: int,
        idempotency_key: str,
        request_hash: str,
        now: datetime,
    ) -> CreativeBundleDto:
        with self.database.session() as session:
            replay = _idempotency_record(
                session,
                owner_id=owner_id,
                guest_session_id=guest_session_id,
                operation="confirm_creative_brief",
                key=idempotency_key,
            )
            if replay:
                return self._replay_bundle(session, replay, request_hash)
            brief = _brief_record(
                session, brief_id, owner_id, guest_session_id, lock=True
            )
            _check_version(brief, base_version)
            if brief.status != "comparing":
                raise InvalidOperation("Creative brief is not ready for confirmation.")
            candidates = self._active_candidates(session, brief.id)
            referenced = {
                decision.selected_candidate_id,
                *decision.merged_candidate_ids,
                *decision.rejected_candidate_ids,
            }
            if referenced != set(candidates):
                raise InvalidOperation(
                    "Every active candidate must receive one decision role."
                )
            self._write_decision(session, decision, base_version, now)
            project = self.create_project(
                owner_id=owner_id,
                guest_session_id=guest_session_id,
                title=story_seed.title,
                description=(
                    f"{brief.story_format} · {brief.genre} · {brief.theme}｜"
                    f"{story_seed.premise}｜核心冲突：{story_seed.core_conflict}"
                ),
                settings_json=dump_json(
                    {"provider": "mock", "creative_brief_id": brief.id}
                ),
                now=now,
                create_seed=True,
                session=session,
            )
            session.add(
                StorySeedRecord(
                    id=story_seed.id,
                    brief_id=brief.id,
                    decision_id=decision.id,
                    project_id=project.id,
                    title=story_seed.title,
                    premise=story_seed.premise,
                    core_conflict=story_seed.core_conflict,
                    emotional_promise=story_seed.emotional_promise,
                    created_at=now,
                )
            )
            brief.status = "confirmed"
            brief.version += 1
            brief.updated_at = now
            session.add(
                IdempotencyRecord(
                    id=new_id(),
                    owner_id=owner_id,
                    guest_session_id=guest_session_id,
                    operation="confirm_creative_brief",
                    idempotency_key=idempotency_key,
                    request_hash=request_hash,
                    status="completed",
                    resource_type="creative_brief",
                    resource_id=brief.id,
                    created_at=now,
                    completed_at=now,
                )
            )
            session.flush()
            return _bundle_dto(session, brief)

    def abandon_creative_brief(
        self,
        brief_id: str,
        *,
        owner_id: str | None,
        guest_session_id: str | None,
        base_version: int,
        now: datetime,
    ) -> CreativeBundleDto:
        with self.database.session() as session:
            brief = _brief_record(
                session, brief_id, owner_id, guest_session_id, lock=True
            )
            _check_version(brief, base_version)
            if brief.status == "confirmed":
                raise InvalidOperation("Confirmed creative briefs cannot be abandoned.")
            if brief.status != "abandoned":
                brief.status = "abandoned"
                brief.version += 1
                brief.updated_at = now
            return _bundle_dto(session, brief)

    @staticmethod
    def _active_candidates(
        session: Session,
        brief_id: str,
    ) -> dict[str, IdeaCandidateRecord]:
        items = session.scalars(
            select(IdeaCandidateRecord).where(
                IdeaCandidateRecord.brief_id == brief_id,
                IdeaCandidateRecord.lifecycle_status == "active",
            )
        ).all()
        if len(items) < 2:
            raise InvalidOperation("Multiple active candidates are required.")
        return {item.id: item for item in items}

    @staticmethod
    def _write_decision(
        session: Session,
        decision: SelectionDecision,
        base_version: int,
        now: datetime,
    ) -> None:
        session.add(
            SelectionDecisionRecord(
                id=decision.id,
                brief_id=decision.brief_id,
                decided_by_session_id=decision.decided_by_session_id,
                base_brief_version=base_version,
                created_at=now,
            )
        )
        session.flush()
        roles = (
            [(decision.selected_candidate_id, "selected")]
            + [(item, "merged") for item in decision.merged_candidate_ids]
            + [(item, "rejected") for item in decision.rejected_candidate_ids]
        )
        for position, (candidate_id, role) in enumerate(roles):
            session.add(
                SelectionDecisionItemRecord(
                    id=new_id(),
                    decision_id=decision.id,
                    candidate_id=candidate_id,
                    role=role,
                    position=position,
                )
            )


__all__ = ["CreativeRepositoryMixin"]
