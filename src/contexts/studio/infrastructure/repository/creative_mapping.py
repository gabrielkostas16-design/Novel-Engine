from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.contexts.studio.application.ports.creative_repository import (
    CreativeBriefDto,
    CreativeBundleDto,
    IdeaCandidateDto,
    SelectionDecisionDto,
    StorySeedDto,
)
from src.contexts.studio.domain.creative import (
    CreativeBrief,
    IdeaCandidate,
    SelectionDecision,
    StorySeed,
)
from src.contexts.studio.domain.exceptions import InvalidOperation
from src.contexts.studio.infrastructure.creative_models import (
    CreativeBriefRecord,
    IdeaCandidateRecord,
    SelectionDecisionItemRecord,
    SelectionDecisionRecord,
    StorySeedRecord,
)


def _brief_dto(record: CreativeBriefRecord) -> CreativeBriefDto:
    return CreativeBriefDto(
        brief=CreativeBrief(
            id=record.id,
            story_format=record.story_format,  # type: ignore[arg-type]
            genre=record.genre,
            theme=record.theme,
            target_reader=record.target_reader,
            platform=record.platform,
            style=record.style,
            premise=record.premise,
            preferences=record.preferences,
        ),
        status=record.status,
        version=record.version,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _candidate_dto(record: IdeaCandidateRecord) -> IdeaCandidateDto:
    return IdeaCandidateDto(
        candidate=IdeaCandidate(
            id=record.id,
            brief_id=record.brief_id,
            title=record.title,
            logline=record.logline,
            core_conflict=record.core_conflict,
            emotional_promise=record.emotional_promise,
            audience_fit=record.audience_fit,
            scalability=record.scalability,
            difficulty=record.difficulty,
            risk=record.risk,
            source=record.source,  # type: ignore[arg-type]
            source_job_id=record.source_job_id,
            source_proposal_id=record.source_proposal_id,
        ),
        revision_of_candidate_id=record.revision_of_candidate_id,
        revision_number=record.revision_number,
        lifecycle_status=record.lifecycle_status,
        position=record.position,
        created_at=record.created_at,
    )


def _decision_dto(
    session: Session,
    record: SelectionDecisionRecord,
) -> SelectionDecisionDto:
    items = session.scalars(
        select(SelectionDecisionItemRecord)
        .where(SelectionDecisionItemRecord.decision_id == record.id)
        .order_by(SelectionDecisionItemRecord.position)
    ).all()
    selected = next(item.candidate_id for item in items if item.role == "selected")
    return SelectionDecisionDto(
        decision=SelectionDecision(
            id=record.id,
            brief_id=record.brief_id,
            selected_candidate_id=selected,
            merged_candidate_ids=tuple(
                item.candidate_id for item in items if item.role == "merged"
            ),
            rejected_candidate_ids=tuple(
                item.candidate_id for item in items if item.role == "rejected"
            ),
            decided_by_session_id=record.decided_by_session_id or "expired-session",
        ),
        base_brief_version=record.base_brief_version,
        created_at=record.created_at,
    )


def _seed_dto(
    record: StorySeedRecord,
    decision: SelectionDecisionDto | None,
) -> StorySeedDto:
    if decision is None:
        raise InvalidOperation("Story seed has no selection decision.")
    source_ids = (
        decision.decision.selected_candidate_id,
        *decision.decision.merged_candidate_ids,
    )
    return StorySeedDto(
        seed=StorySeed(
            id=record.id,
            brief_id=record.brief_id,
            decision_id=record.decision_id,
            source_candidate_ids=source_ids,
            title=record.title,
            premise=record.premise,
            core_conflict=record.core_conflict,
            emotional_promise=record.emotional_promise,
        ),
        project_id=record.project_id,
        created_at=record.created_at,
    )


def _bundle_dto(session: Session, brief: CreativeBriefRecord) -> CreativeBundleDto:
    candidates = session.scalars(
        select(IdeaCandidateRecord)
        .where(
            IdeaCandidateRecord.brief_id == brief.id,
            IdeaCandidateRecord.lifecycle_status == "active",
        )
        .order_by(IdeaCandidateRecord.position, IdeaCandidateRecord.created_at)
    ).all()
    decision_record = session.scalar(
        select(SelectionDecisionRecord).where(
            SelectionDecisionRecord.brief_id == brief.id
        )
    )
    decision_dto = _decision_dto(session, decision_record) if decision_record else None
    seed_record = session.scalar(
        select(StorySeedRecord).where(StorySeedRecord.brief_id == brief.id)
    )
    return CreativeBundleDto(
        brief=_brief_dto(brief),
        candidates=tuple(_candidate_dto(item) for item in candidates),
        decision=decision_dto,
        story_seed=_seed_dto(seed_record, decision_dto) if seed_record else None,
    )


__all__ = ["_bundle_dto"]
