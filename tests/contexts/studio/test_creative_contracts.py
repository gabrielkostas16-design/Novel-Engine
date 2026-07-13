from __future__ import annotations

from typing import Any, cast

import pytest
from pydantic import ValidationError

from src.contexts.studio.interface.http.schemas import CreativeBundleRequest


def _candidate(candidate_id: str, source: str = "rule") -> dict[str, Any]:
    candidate: dict[str, Any] = {
        "id": candidate_id,
        "brief_id": "brief-1",
        "title": f"Direction {candidate_id}",
        "logline": "A witness must choose between truth and the person they protect.",
        "core_conflict": "Truth versus loyalty.",
        "emotional_promise": "A costly but earned reconciliation.",
        "audience_fit": "Readers of suspense and relationship drama.",
        "scalability": "Supports a short story or a compact novel.",
        "difficulty": "Medium",
        "risk": "The mystery can overshadow the relationship.",
        "source": source,
    }
    if source == "ai":
        candidate.update(
            source_job_id="job-1",
            source_proposal_id="proposal-1",
        )
    return candidate


def _valid_payload() -> dict[str, Any]:
    return {
        "brief": {
            "id": "brief-1",
            "story_format": "short",
            "genre": "Suspense",
            "theme": "Truth and protection",
            "target_reader": "Adult genre readers",
            "platform": "Web",
            "style": "Controlled and cinematic",
            "premise": "A witness hides evidence to protect the suspect.",
            "preferences": "No unexplained supernatural solution.",
        },
        "candidates": [
            _candidate("candidate-a", source="ai"),
            _candidate("candidate-b"),
            _candidate("candidate-c"),
        ],
        "decision": {
            "id": "decision-1",
            "brief_id": "brief-1",
            "selected_candidate_id": "candidate-a",
            "merged_candidate_ids": ["candidate-c"],
            "rejected_candidate_ids": ["candidate-b"],
            "decided_by_session_id": "session-1",
        },
        "story_seed": {
            "id": "seed-1",
            "brief_id": "brief-1",
            "decision_id": "decision-1",
            "source_candidate_ids": ["candidate-a", "candidate-c"],
            "title": "The Missing Frame",
            "premise": "A witness edits one frame and becomes part of the crime.",
            "core_conflict": "Expose the truth or protect the accused.",
            "emotional_promise": "Protection becomes an honest choice, not a lie.",
        },
    }


def test_creative_bundle_maps_to_author_controlled_domain_contract() -> None:
    request = CreativeBundleRequest.model_validate(_valid_payload())

    bundle = request.to_domain()

    assert bundle.brief.story_format == "short"
    assert bundle.candidates[0].source_job_id == "job-1"
    assert bundle.decision.selected_candidate_id == "candidate-a"
    assert bundle.story_seed.source_candidate_ids == (
        "candidate-a",
        "candidate-c",
    )


def test_ai_candidate_requires_job_and_proposal_evidence() -> None:
    payload = _valid_payload()
    candidates = cast(list[dict[str, Any]], payload["candidates"])
    candidates[0].pop("source_proposal_id")

    with pytest.raises(ValidationError, match="job and proposal evidence"):
        CreativeBundleRequest.model_validate(payload)


def test_selection_cannot_reject_the_selected_candidate() -> None:
    payload = _valid_payload()
    decision = cast(dict[str, Any], payload["decision"])
    decision["rejected_candidate_ids"] = ["candidate-a"]

    with pytest.raises(ValidationError, match="cannot overlap"):
        CreativeBundleRequest.model_validate(payload)


def test_story_seed_must_match_the_author_decision() -> None:
    payload = _valid_payload()
    story_seed = cast(dict[str, Any], payload["story_seed"])
    story_seed["source_candidate_ids"] = ["candidate-b"]

    with pytest.raises(ValidationError, match="must match the author decision"):
        CreativeBundleRequest.model_validate(payload)
