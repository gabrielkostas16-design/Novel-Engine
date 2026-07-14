from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Header, status

from src.contexts.studio.interface.http.dependencies import StudioStoreDependency
from src.contexts.studio.interface.http.errors import _handle_domain_exceptions
from src.contexts.studio.interface.http.schemas import (
    CreativeAbandonRequest,
    CreativeBriefCreateRequest,
    CreativeBriefPatchRequest,
    CreativeDecisionCreateRequest,
    RuleCandidatesRequest,
)
from src.contexts.studio.interface.http.session_router import PrincipalDependency

creative_router = APIRouter(prefix="/creative-briefs", tags=["creative"])
IdempotencyKey = Annotated[
    str,
    Header(alias="Idempotency-Key", min_length=1, max_length=128),
]


@creative_router.post("", status_code=status.HTTP_201_CREATED)
@_handle_domain_exceptions
async def create_creative_brief(
    payload: CreativeBriefCreateRequest,
    idempotency_key: IdempotencyKey,
    principal: PrincipalDependency,
    store: StudioStoreDependency,
) -> dict[str, Any]:
    return store.create_creative_brief(
        principal,
        values=payload.model_dump(),
        idempotency_key=idempotency_key,
    )


@creative_router.get("/{brief_id}")
@_handle_domain_exceptions
async def get_creative_brief(
    brief_id: str,
    principal: PrincipalDependency,
    store: StudioStoreDependency,
) -> dict[str, Any]:
    return store.get_creative_bundle(principal, brief_id)


@creative_router.patch("/{brief_id}")
@_handle_domain_exceptions
async def update_creative_brief(
    brief_id: str,
    payload: CreativeBriefPatchRequest,
    principal: PrincipalDependency,
    store: StudioStoreDependency,
) -> dict[str, Any]:
    values = payload.model_dump(exclude={"base_version"}, exclude_unset=True)
    return store.update_creative_brief(
        principal,
        brief_id,
        base_version=payload.base_version,
        changes=values,
    )


@creative_router.post("/{brief_id}/rule-candidates")
@_handle_domain_exceptions
async def save_rule_candidates(
    brief_id: str,
    payload: RuleCandidatesRequest,
    principal: PrincipalDependency,
    store: StudioStoreDependency,
) -> dict[str, Any]:
    return store.save_rule_candidates(
        principal,
        brief_id,
        base_version=payload.base_version,
        candidates=[candidate.model_dump() for candidate in payload.candidates],
    )


@creative_router.post(
    "/{brief_id}/decisions",
    status_code=status.HTTP_201_CREATED,
)
@_handle_domain_exceptions
async def confirm_creative_brief(
    brief_id: str,
    payload: CreativeDecisionCreateRequest,
    idempotency_key: IdempotencyKey,
    principal: PrincipalDependency,
    store: StudioStoreDependency,
) -> dict[str, Any]:
    return store.confirm_creative_brief(
        principal,
        brief_id,
        base_version=payload.base_version,
        selected_candidate_id=payload.selected_candidate_id,
        merged_candidate_ids=payload.merged_candidate_ids,
        rejected_candidate_ids=payload.rejected_candidate_ids,
        idempotency_key=idempotency_key,
    )


@creative_router.post("/{brief_id}/abandon")
@_handle_domain_exceptions
async def abandon_creative_brief(
    brief_id: str,
    payload: CreativeAbandonRequest,
    principal: PrincipalDependency,
    store: StudioStoreDependency,
) -> dict[str, Any]:
    return store.abandon_creative_brief(
        principal,
        brief_id,
        base_version=payload.base_version,
    )


__all__ = ["creative_router"]
