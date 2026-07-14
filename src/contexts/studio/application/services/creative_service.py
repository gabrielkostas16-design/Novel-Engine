from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any

from src.contexts.studio.application.ports.creative_repository import (
    CreativeBundleDto,
    CreativeRepository,
)
from src.contexts.studio.application.service_common import (
    InvalidOperation,
    Principal,
    _owner_scopes,
    new_id,
    utcnow,
)
from src.contexts.studio.domain.creative import (
    CreativeBrief,
    IdeaCandidate,
    SelectionDecision,
    StorySeed,
)


def _request_hash(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _bundle_payload(bundle: CreativeBundleDto) -> dict[str, Any]:
    brief = bundle.brief
    decision = bundle.decision
    seed = bundle.story_seed
    return {
        "brief": {
            **asdict(brief.brief),
            "status": brief.status,
            "version": brief.version,
            "created_at": brief.created_at.isoformat(),
            "updated_at": brief.updated_at.isoformat(),
        },
        "candidates": [
            {
                **asdict(item.candidate),
                "revision_of_candidate_id": item.revision_of_candidate_id,
                "revision_number": item.revision_number,
                "lifecycle_status": item.lifecycle_status,
                "position": item.position,
                "created_at": item.created_at.isoformat(),
            }
            for item in bundle.candidates
        ],
        "decision": (
            {
                **asdict(decision.decision),
                "base_brief_version": decision.base_brief_version,
                "created_at": decision.created_at.isoformat(),
            }
            if decision
            else None
        ),
        "story_seed": (
            {
                **asdict(seed.seed),
                "project_id": seed.project_id,
                "created_at": seed.created_at.isoformat(),
            }
            if seed
            else None
        ),
    }


class CreativeService:
    def __init__(self, repository: CreativeRepository) -> None:
        self._repository = repository

    def create_brief(
        self,
        principal: Principal,
        *,
        values: dict[str, Any],
        idempotency_key: str,
    ) -> dict[str, Any]:
        self._require_idempotency_key(idempotency_key)
        owner_id, guest_session_id = _owner_scopes(principal)
        brief = CreativeBrief(id=new_id(), **values)
        bundle = self._repository.create_creative_brief(
            owner_id=owner_id,
            guest_session_id=guest_session_id,
            brief=brief,
            idempotency_key=idempotency_key,
            request_hash=_request_hash(values),
            now=utcnow(),
        )
        return _bundle_payload(bundle)

    def get_bundle(self, principal: Principal, brief_id: str) -> dict[str, Any]:
        owner_id, guest_session_id = _owner_scopes(principal)
        return _bundle_payload(
            self._repository.get_creative_bundle(
                brief_id,
                owner_id=owner_id,
                guest_session_id=guest_session_id,
            )
        )

    def update_brief(
        self,
        principal: Principal,
        brief_id: str,
        *,
        base_version: int,
        changes: dict[str, Any],
    ) -> dict[str, Any]:
        owner_id, guest_session_id = _owner_scopes(principal)
        current = self._repository.get_creative_bundle(
            brief_id,
            owner_id=owner_id,
            guest_session_id=guest_session_id,
        ).brief.brief
        values = asdict(current)
        values.update(
            {key: value for key, value in changes.items() if value is not None}
        )
        values["id"] = brief_id
        bundle = self._repository.update_creative_brief(
            brief_id,
            owner_id=owner_id,
            guest_session_id=guest_session_id,
            brief=CreativeBrief(**values),
            base_version=base_version,
            now=utcnow(),
        )
        return _bundle_payload(bundle)

    def save_rule_candidates(
        self,
        principal: Principal,
        brief_id: str,
        *,
        base_version: int,
        candidates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if len(candidates) < 2:
            raise InvalidOperation("At least two rule candidates are required.")
        owner_id, guest_session_id = _owner_scopes(principal)
        domain_candidates = tuple(
            IdeaCandidate(
                id=new_id(),
                brief_id=brief_id,
                source="rule",
                **candidate,
            )
            for candidate in candidates
        )
        bundle = self._repository.replace_rule_candidates(
            brief_id,
            owner_id=owner_id,
            guest_session_id=guest_session_id,
            candidates=domain_candidates,
            base_version=base_version,
            now=utcnow(),
        )
        return _bundle_payload(bundle)

    def confirm_brief(
        self,
        principal: Principal,
        brief_id: str,
        *,
        base_version: int,
        selected_candidate_id: str,
        merged_candidate_ids: list[str],
        rejected_candidate_ids: list[str],
        idempotency_key: str,
    ) -> dict[str, Any]:
        self._require_idempotency_key(idempotency_key)
        owner_id, guest_session_id = _owner_scopes(principal)
        bundle = self._repository.get_creative_bundle(
            brief_id,
            owner_id=owner_id,
            guest_session_id=guest_session_id,
        )
        selected = next(
            (
                item.candidate
                for item in bundle.candidates
                if item.candidate.id == selected_candidate_id
            ),
            None,
        )
        if selected is None:
            raise InvalidOperation("Selected candidate is not active.")
        command = {
            "brief_id": brief_id,
            "base_version": base_version,
            "selected_candidate_id": selected_candidate_id,
            "merged_candidate_ids": merged_candidate_ids,
            "rejected_candidate_ids": rejected_candidate_ids,
        }
        decision = SelectionDecision(
            id=new_id(),
            brief_id=brief_id,
            selected_candidate_id=selected_candidate_id,
            merged_candidate_ids=tuple(merged_candidate_ids),
            rejected_candidate_ids=tuple(rejected_candidate_ids),
            decided_by_session_id=principal.session_id,
        )
        seed = StorySeed(
            id=new_id(),
            brief_id=brief_id,
            decision_id=decision.id,
            source_candidate_ids=(selected_candidate_id, *merged_candidate_ids),
            title=selected.title,
            premise=selected.logline,
            core_conflict=selected.core_conflict,
            emotional_promise=selected.emotional_promise,
        )
        confirmed = self._repository.confirm_creative_brief(
            brief_id,
            owner_id=owner_id,
            guest_session_id=guest_session_id,
            decision=decision,
            story_seed=seed,
            base_version=base_version,
            idempotency_key=idempotency_key,
            request_hash=_request_hash(command),
            now=utcnow(),
        )
        return _bundle_payload(confirmed)

    def abandon_brief(
        self,
        principal: Principal,
        brief_id: str,
        *,
        base_version: int,
    ) -> dict[str, Any]:
        owner_id, guest_session_id = _owner_scopes(principal)
        return _bundle_payload(
            self._repository.abandon_creative_brief(
                brief_id,
                owner_id=owner_id,
                guest_session_id=guest_session_id,
                base_version=base_version,
                now=utcnow(),
            )
        )

    @staticmethod
    def _require_idempotency_key(value: str) -> None:
        if not value.strip():
            raise InvalidOperation("Idempotency-Key is required.")


__all__ = ["CreativeService"]
