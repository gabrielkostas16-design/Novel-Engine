from __future__ import annotations

from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _brief_payload(
    *, premise: str = "A witness must choose truth or family."
) -> dict[str, Any]:
    return {
        "story_format": "medium",
        "genre": "悬疑",
        "theme": "真相与救赎",
        "target_reader": "成年悬疑读者",
        "platform": "本地创作",
        "style": "现实感与强冲突",
        "premise": premise,
        "preferences": "逻辑严密，拒绝无因反转",
    }


def _candidate_payload(index: int) -> dict[str, str]:
    return {
        "title": f"候选 {index}",
        "logline": f"第 {index} 条故事钩子",
        "core_conflict": f"第 {index} 条核心冲突",
        "emotional_promise": "真相需要付出代价",
        "audience_fit": "悬疑读者",
        "scalability": "可扩展为三幕结构",
        "difficulty": "中等",
        "risk": "避免反转压过人物",
    }


def _create_brief(client: TestClient, *, key: str = "brief-key") -> dict[str, Any]:
    response = client.post(
        "/api/creative-briefs",
        headers={"Idempotency-Key": key},
        json=_brief_payload(),
    )
    assert response.status_code == 201
    return cast(dict[str, Any], response.json())


def _save_candidates(client: TestClient, bundle: dict[str, Any]) -> dict[str, Any]:
    response = client.post(
        f"/api/creative-briefs/{bundle['brief']['id']}/rule-candidates",
        json={
            "base_version": bundle["brief"]["version"],
            "candidates": [_candidate_payload(index) for index in range(1, 4)],
        },
    )
    assert response.status_code == 200
    return cast(dict[str, Any], response.json())


def test_creative_workflow_is_scoped_cas_safe_and_idempotent(
    canonical_client: TestClient,
) -> None:
    session_id = canonical_client.post("/api/session/guest").json()["session_id"]
    created = _create_brief(canonical_client)
    brief_id = created["brief"]["id"]

    replay = canonical_client.post(
        "/api/creative-briefs",
        headers={"Idempotency-Key": "brief-key"},
        json=_brief_payload(),
    )
    assert replay.status_code == 201
    assert replay.json()["brief"]["id"] == brief_id

    conflicting_key = canonical_client.post(
        "/api/creative-briefs",
        headers={"Idempotency-Key": "brief-key"},
        json=_brief_payload(premise="Different command content."),
    )
    assert conflicting_key.status_code == 409

    other = TestClient(canonical_client.app, raise_server_exceptions=False)
    with other:
        other.post("/api/session/guest")
        assert other.get(f"/api/creative-briefs/{brief_id}").status_code == 404

    comparing = _save_candidates(canonical_client, created)
    assert comparing["brief"]["status"] == "comparing"
    assert comparing["brief"]["version"] == 2
    assert len(comparing["candidates"]) == 3

    stale = canonical_client.patch(
        f"/api/creative-briefs/{brief_id}",
        json={"base_version": 1, "theme": "过期修改"},
    )
    assert stale.status_code == 409
    assert stale.json()["detail"]["current_version"] == 2

    candidate_ids = [item["id"] for item in comparing["candidates"]]
    decision_payload = {
        "base_version": 2,
        "selected_candidate_id": candidate_ids[1],
        "merged_candidate_ids": [candidate_ids[0]],
        "rejected_candidate_ids": [candidate_ids[2]],
    }
    confirmed = canonical_client.post(
        f"/api/creative-briefs/{brief_id}/decisions",
        headers={"Idempotency-Key": "decision-key"},
        json=decision_payload,
    )
    assert confirmed.status_code == 201
    result = confirmed.json()
    assert result["brief"]["status"] == "confirmed"
    assert result["story_seed"]["source_candidate_ids"] == candidate_ids[1::-1]
    project_id = result["story_seed"]["project_id"]
    assert canonical_client.get(f"/api/projects/{project_id}").status_code == 200

    replayed = canonical_client.post(
        f"/api/creative-briefs/{brief_id}/decisions",
        headers={"Idempotency-Key": "decision-key"},
        json=decision_payload,
    )
    assert replayed.status_code == 201
    assert replayed.json()["story_seed"]["project_id"] == project_id
    assert len(canonical_client.get("/api/projects").json()["projects"]) == 1

    from src.contexts.studio.infrastructure.database import StudioDatabase
    from src.contexts.studio.infrastructure.repository import SqlAlchemyStudioRepository

    app = cast(FastAPI, canonical_client.app)
    live_database = app.state.studio_runtime.database
    reopened_database = StudioDatabase(live_database.url)
    try:
        reopened = SqlAlchemyStudioRepository(reopened_database).get_creative_bundle(
            brief_id,
            owner_id=None,
            guest_session_id=session_id,
        )
        assert reopened.brief.status == "confirmed"
        assert reopened.story_seed is not None
        assert reopened.story_seed.project_id == project_id
    finally:
        reopened_database.dispose()


def test_confirmation_failure_rolls_back_all_records(
    canonical_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canonical_client.post("/api/session/guest")
    comparing = _save_candidates(canonical_client, _create_brief(canonical_client))
    brief_id = comparing["brief"]["id"]
    candidate_ids = [item["id"] for item in comparing["candidates"]]
    app = cast(FastAPI, canonical_client.app)
    repository = app.state.studio_store.repository

    def fail_project_creation(**_kwargs: Any) -> Any:
        raise RuntimeError("injected project failure")

    monkeypatch.setattr(repository, "create_project", fail_project_creation)
    failed = canonical_client.post(
        f"/api/creative-briefs/{brief_id}/decisions",
        headers={"Idempotency-Key": "rollback-key"},
        json={
            "base_version": 2,
            "selected_candidate_id": candidate_ids[0],
            "merged_candidate_ids": [],
            "rejected_candidate_ids": candidate_ids[1:],
        },
    )
    assert failed.status_code == 500

    persisted = canonical_client.get(f"/api/creative-briefs/{brief_id}").json()
    assert persisted["brief"]["status"] == "comparing"
    assert persisted["brief"]["version"] == 2
    assert persisted["decision"] is None
    assert persisted["story_seed"] is None
    assert canonical_client.get("/api/projects").json()["projects"] == []
