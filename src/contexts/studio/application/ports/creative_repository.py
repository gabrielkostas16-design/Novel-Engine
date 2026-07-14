from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from src.contexts.studio.domain.creative import (
    CreativeBrief,
    IdeaCandidate,
    SelectionDecision,
    StorySeed,
)


@dataclass(frozen=True, slots=True)
class CreativeBriefDto:
    brief: CreativeBrief
    status: str
    version: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class IdeaCandidateDto:
    candidate: IdeaCandidate
    revision_of_candidate_id: str | None
    revision_number: int
    lifecycle_status: str
    position: int
    created_at: datetime


@dataclass(frozen=True, slots=True)
class SelectionDecisionDto:
    decision: SelectionDecision
    base_brief_version: int
    created_at: datetime


@dataclass(frozen=True, slots=True)
class StorySeedDto:
    seed: StorySeed
    project_id: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class CreativeBundleDto:
    brief: CreativeBriefDto
    candidates: tuple[IdeaCandidateDto, ...] = field(default_factory=tuple)
    decision: SelectionDecisionDto | None = None
    story_seed: StorySeedDto | None = None


class CreativeRepository(Protocol):
    def create_creative_brief(
        self,
        *,
        owner_id: str | None,
        guest_session_id: str | None,
        brief: CreativeBrief,
        idempotency_key: str,
        request_hash: str,
        now: datetime,
    ) -> CreativeBundleDto: ...

    def get_creative_bundle(
        self,
        brief_id: str,
        *,
        owner_id: str | None,
        guest_session_id: str | None,
    ) -> CreativeBundleDto: ...

    def update_creative_brief(
        self,
        brief_id: str,
        *,
        owner_id: str | None,
        guest_session_id: str | None,
        brief: CreativeBrief,
        base_version: int,
        now: datetime,
    ) -> CreativeBundleDto: ...

    def replace_rule_candidates(
        self,
        brief_id: str,
        *,
        owner_id: str | None,
        guest_session_id: str | None,
        candidates: tuple[IdeaCandidate, ...],
        base_version: int,
        now: datetime,
    ) -> CreativeBundleDto: ...

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
    ) -> CreativeBundleDto: ...

    def abandon_creative_brief(
        self,
        brief_id: str,
        *,
        owner_id: str | None,
        guest_session_id: str | None,
        base_version: int,
        now: datetime,
    ) -> CreativeBundleDto: ...


__all__ = [
    "CreativeBriefDto",
    "CreativeBundleDto",
    "CreativeRepository",
    "IdeaCandidateDto",
    "SelectionDecisionDto",
    "StorySeedDto",
]
