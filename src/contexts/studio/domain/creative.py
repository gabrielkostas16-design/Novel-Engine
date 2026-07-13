"""Author-controlled contracts for turning ideas into a story seed."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

StoryFormat = Literal["short", "medium", "long_serial"]
IdeaSource = Literal["author", "rule", "ai"]


def _require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} is required.")


@dataclass(frozen=True, slots=True)
class CreativeBrief:
    id: str
    story_format: StoryFormat
    genre: str
    theme: str
    target_reader: str
    platform: str
    style: str
    premise: str
    preferences: str

    def __post_init__(self) -> None:
        _require_text(self.id, "Creative brief id")
        _require_text(self.genre, "Genre")
        _require_text(self.premise, "Premise")


@dataclass(frozen=True, slots=True)
class IdeaCandidate:
    id: str
    brief_id: str
    title: str
    logline: str
    core_conflict: str
    emotional_promise: str
    audience_fit: str
    scalability: str
    difficulty: str
    risk: str
    source: IdeaSource
    source_job_id: str | None = None
    source_proposal_id: str | None = None

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.id, "Candidate id"),
            (self.brief_id, "Candidate brief id"),
            (self.title, "Candidate title"),
            (self.logline, "Candidate logline"),
            (self.core_conflict, "Core conflict"),
        ):
            _require_text(value, field_name)
        evidence = self.source_job_id and self.source_proposal_id
        if self.source == "ai" and not evidence:
            raise ValueError("AI candidates require job and proposal evidence.")
        if self.source != "ai" and (self.source_job_id or self.source_proposal_id):
            raise ValueError(
                "Only AI candidates may reference job or proposal evidence."
            )


@dataclass(frozen=True, slots=True)
class SelectionDecision:
    id: str
    brief_id: str
    selected_candidate_id: str
    merged_candidate_ids: tuple[str, ...]
    rejected_candidate_ids: tuple[str, ...]
    decided_by_session_id: str

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.id, "Decision id"),
            (self.brief_id, "Decision brief id"),
            (self.selected_candidate_id, "Selected candidate id"),
            (self.decided_by_session_id, "Deciding session id"),
        ):
            _require_text(value, field_name)
        merged = set(self.merged_candidate_ids)
        rejected = set(self.rejected_candidate_ids)
        if len(merged) != len(self.merged_candidate_ids):
            raise ValueError("Merged candidate ids must be unique.")
        if len(rejected) != len(self.rejected_candidate_ids):
            raise ValueError("Rejected candidate ids must be unique.")
        if self.selected_candidate_id in merged | rejected or merged & rejected:
            raise ValueError(
                "Selected, merged, and rejected candidates cannot overlap."
            )


@dataclass(frozen=True, slots=True)
class StorySeed:
    id: str
    brief_id: str
    decision_id: str
    source_candidate_ids: tuple[str, ...]
    title: str
    premise: str
    core_conflict: str
    emotional_promise: str

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.id, "Story seed id"),
            (self.brief_id, "Story seed brief id"),
            (self.decision_id, "Story seed decision id"),
            (self.title, "Story seed title"),
            (self.premise, "Story seed premise"),
            (self.core_conflict, "Story seed core conflict"),
        ):
            _require_text(value, field_name)
        if not self.source_candidate_ids:
            raise ValueError("Story seed requires at least one source candidate.")


@dataclass(frozen=True, slots=True)
class CreativeBundle:
    brief: CreativeBrief
    candidates: tuple[IdeaCandidate, ...]
    decision: SelectionDecision
    story_seed: StorySeed

    def __post_init__(self) -> None:
        if len(self.candidates) < 2:
            raise ValueError("A creative bundle requires multiple candidates.")
        candidate_ids = tuple(candidate.id for candidate in self.candidates)
        if len(set(candidate_ids)) != len(candidate_ids):
            raise ValueError("Candidate ids must be unique.")
        if any(candidate.brief_id != self.brief.id for candidate in self.candidates):
            raise ValueError("All candidates must belong to the creative brief.")
        if self.decision.brief_id != self.brief.id:
            raise ValueError("Selection decision must belong to the creative brief.")
        referenced = {
            self.decision.selected_candidate_id,
            *self.decision.merged_candidate_ids,
            *self.decision.rejected_candidate_ids,
        }
        if not referenced.issubset(candidate_ids):
            raise ValueError("Selection decision references an unknown candidate.")
        if self.story_seed.brief_id != self.brief.id:
            raise ValueError("Story seed must belong to the creative brief.")
        if self.story_seed.decision_id != self.decision.id:
            raise ValueError("Story seed must reference the selection decision.")
        expected_sources = (
            self.decision.selected_candidate_id,
            *self.decision.merged_candidate_ids,
        )
        if self.story_seed.source_candidate_ids != expected_sources:
            raise ValueError("Story seed sources must match the author decision.")
