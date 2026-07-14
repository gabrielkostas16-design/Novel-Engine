from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.contexts.studio.domain.creative import (
    CreativeBrief,
    CreativeBundle,
    IdeaCandidate,
    IdeaSource,
    SelectionDecision,
    StoryFormat,
    StorySeed,
)
from src.contexts.studio.domain.types import DocumentKind, ExportFormat


class _CreativeContract(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CreativeBriefRequest(_CreativeContract):
    id: str = Field(min_length=1, max_length=120)
    story_format: StoryFormat
    genre: str = Field(min_length=1, max_length=120)
    theme: str = Field(default="", max_length=240)
    target_reader: str = Field(default="", max_length=240)
    platform: str = Field(default="", max_length=120)
    style: str = Field(default="", max_length=240)
    premise: str = Field(min_length=1, max_length=2_000)
    preferences: str = Field(default="", max_length=2_000)

    def to_domain(self) -> CreativeBrief:
        return CreativeBrief(**self.model_dump())


class IdeaCandidateRequest(_CreativeContract):
    id: str = Field(min_length=1, max_length=120)
    brief_id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=240)
    logline: str = Field(min_length=1, max_length=2_000)
    core_conflict: str = Field(min_length=1, max_length=2_000)
    emotional_promise: str = Field(default="", max_length=1_000)
    audience_fit: str = Field(default="", max_length=1_000)
    scalability: str = Field(default="", max_length=1_000)
    difficulty: str = Field(default="", max_length=1_000)
    risk: str = Field(default="", max_length=1_000)
    source: IdeaSource
    source_job_id: str | None = Field(default=None, max_length=120)
    source_proposal_id: str | None = Field(default=None, max_length=120)

    def to_domain(self) -> IdeaCandidate:
        return IdeaCandidate(**self.model_dump())


class SelectionDecisionRequest(_CreativeContract):
    id: str = Field(min_length=1, max_length=120)
    brief_id: str = Field(min_length=1, max_length=120)
    selected_candidate_id: str = Field(min_length=1, max_length=120)
    merged_candidate_ids: list[str] = Field(default_factory=list, max_length=4)
    rejected_candidate_ids: list[str] = Field(default_factory=list, max_length=4)
    decided_by_session_id: str = Field(min_length=1, max_length=120)

    def to_domain(self) -> SelectionDecision:
        return SelectionDecision(
            id=self.id,
            brief_id=self.brief_id,
            selected_candidate_id=self.selected_candidate_id,
            merged_candidate_ids=tuple(self.merged_candidate_ids),
            rejected_candidate_ids=tuple(self.rejected_candidate_ids),
            decided_by_session_id=self.decided_by_session_id,
        )


class StorySeedRequest(_CreativeContract):
    id: str = Field(min_length=1, max_length=120)
    brief_id: str = Field(min_length=1, max_length=120)
    decision_id: str = Field(min_length=1, max_length=120)
    source_candidate_ids: list[str] = Field(min_length=1, max_length=5)
    title: str = Field(min_length=1, max_length=240)
    premise: str = Field(min_length=1, max_length=4_000)
    core_conflict: str = Field(min_length=1, max_length=2_000)
    emotional_promise: str = Field(default="", max_length=1_000)

    def to_domain(self) -> StorySeed:
        return StorySeed(
            id=self.id,
            brief_id=self.brief_id,
            decision_id=self.decision_id,
            source_candidate_ids=tuple(self.source_candidate_ids),
            title=self.title,
            premise=self.premise,
            core_conflict=self.core_conflict,
            emotional_promise=self.emotional_promise,
        )


class CreativeBundleRequest(_CreativeContract):
    brief: CreativeBriefRequest
    candidates: list[IdeaCandidateRequest] = Field(min_length=2, max_length=5)
    decision: SelectionDecisionRequest
    story_seed: StorySeedRequest

    def to_domain(self) -> CreativeBundle:
        return CreativeBundle(
            brief=self.brief.to_domain(),
            candidates=tuple(candidate.to_domain() for candidate in self.candidates),
            decision=self.decision.to_domain(),
            story_seed=self.story_seed.to_domain(),
        )

    @model_validator(mode="after")
    def validate_creative_contract(self) -> CreativeBundleRequest:
        self.to_domain()
        return self


class CreativeBriefCreateRequest(_CreativeContract):
    story_format: StoryFormat
    genre: str = Field(min_length=1, max_length=120)
    theme: str = Field(default="", max_length=240)
    target_reader: str = Field(default="", max_length=240)
    platform: str = Field(default="", max_length=120)
    style: str = Field(default="", max_length=240)
    premise: str = Field(min_length=1, max_length=2_000)
    preferences: str = Field(default="", max_length=2_000)


class CreativeBriefPatchRequest(_CreativeContract):
    base_version: int = Field(ge=1)
    story_format: StoryFormat | None = None
    genre: str | None = Field(default=None, min_length=1, max_length=120)
    theme: str | None = Field(default=None, max_length=240)
    target_reader: str | None = Field(default=None, max_length=240)
    platform: str | None = Field(default=None, max_length=120)
    style: str | None = Field(default=None, max_length=240)
    premise: str | None = Field(default=None, min_length=1, max_length=2_000)
    preferences: str | None = Field(default=None, max_length=2_000)


class RuleCandidateInput(_CreativeContract):
    title: str = Field(min_length=1, max_length=240)
    logline: str = Field(min_length=1, max_length=2_000)
    core_conflict: str = Field(min_length=1, max_length=2_000)
    emotional_promise: str = Field(default="", max_length=1_000)
    audience_fit: str = Field(default="", max_length=1_000)
    scalability: str = Field(default="", max_length=1_000)
    difficulty: str = Field(default="", max_length=1_000)
    risk: str = Field(default="", max_length=1_000)


class RuleCandidatesRequest(_CreativeContract):
    base_version: int = Field(ge=1)
    candidates: list[RuleCandidateInput] = Field(min_length=2, max_length=5)


class CreativeDecisionCreateRequest(_CreativeContract):
    base_version: int = Field(ge=1)
    selected_candidate_id: str = Field(min_length=1, max_length=120)
    merged_candidate_ids: list[str] = Field(default_factory=list, max_length=4)
    rejected_candidate_ids: list[str] = Field(default_factory=list, max_length=4)


class CreativeAbandonRequest(_CreativeContract):
    base_version: int = Field(ge=1)


class OwnerSetupRequest(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=10, max_length=200)


class LoginRequest(BaseModel):
    username: str
    password: str


class ProjectRequest(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    description: str = Field(default="", max_length=10_000)


class ProjectUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=240)
    description: str | None = Field(default=None, max_length=10_000)
    settings: dict[str, Any] | None = None


class DocumentCreateRequest(BaseModel):
    kind: DocumentKind
    title: str = Field(min_length=1, max_length=240)
    content_markdown: str = ""
    position: int | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentSaveRequest(BaseModel):
    content_markdown: str
    base_revision_id: str | None
    title: str | None = Field(default=None, max_length=240)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentRestoreRequest(BaseModel):
    base_revision_id: str | None


class ReorderRequest(BaseModel):
    document_ids: list[str] = Field(min_length=1)


class AIProposalRequest(BaseModel):
    operation: Literal["continue", "rewrite", "generate"]
    instruction: str = Field(default="", max_length=10_000)
    provider: Literal["mock", "dashscope", "openai_compatible"] = "mock"


class ExportRequest(BaseModel):
    format: ExportFormat


class LegacyPathRequest(BaseModel):
    source: str = Field(
        min_length=1,
        max_length=240,
        description="Workspace directory name under data/imports.",
    )


class SnapshotRequest(BaseModel):
    reason: str = Field(default="manual", min_length=1, max_length=48)
