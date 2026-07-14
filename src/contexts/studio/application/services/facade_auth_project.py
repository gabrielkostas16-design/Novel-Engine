from __future__ import annotations

from src.contexts.studio.application.service_common import Any, Principal
from src.contexts.studio.application.services.facade_base import StudioServiceRegistry


class AuthProjectFacade(StudioServiceRegistry):
    def owner_exists(self) -> bool:
        return self.auth.owner_exists()

    def owner_principal(self, username: str | None = None) -> Principal:
        return self.auth.owner_principal(username)

    def setup_owner(self, username: str, password: str) -> dict[str, Any]:
        return self.auth.setup_owner(username, password)

    def create_owner_session(
        self,
        username: str,
        password: str,
    ) -> tuple[str, str, Principal]:
        return self.auth.create_owner_session(username, password)

    def create_guest_session(self) -> tuple[str, str, Principal]:
        return self.auth.create_guest_session()

    def csrf_token_for_session(self, token_hash: str) -> str | None:
        return self.auth.csrf_token_for_session(token_hash)

    def principal_from_token(self, token: str | None) -> Principal | None:
        return self.auth.principal_from_token(token)

    def logout(self, token: str | None) -> None:
        return self.auth.logout(token)

    def cleanup_expired_guests(self) -> int:
        return self.auth.cleanup_expired_guests()

    def create_project(
        self,
        principal: Principal,
        *,
        title: str,
        description: str = "",
        create_seed: bool = True,
    ) -> dict[str, Any]:
        return self.project_service.create_project(
            principal,
            title=title,
            description=description,
            create_seed=create_seed,
        )

    def list_projects(self, principal: Principal) -> list[dict[str, Any]]:
        return self.project_service.list_projects(principal)

    def get_project(self, principal: Principal, project_id: str) -> dict[str, Any]:
        return self.project_service.get_project(principal, project_id)

    def update_project(
        self,
        principal: Principal,
        project_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        settings: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.project_service.update_project(
            principal,
            project_id,
            title=title,
            description=description,
            settings=settings,
        )

    def delete_project(self, principal: Principal, project_id: str) -> None:
        return self.project_service.delete_project(principal, project_id)

    def create_creative_brief(
        self,
        principal: Principal,
        *,
        values: dict[str, Any],
        idempotency_key: str,
    ) -> dict[str, Any]:
        return self.creative_service.create_brief(
            principal,
            values=values,
            idempotency_key=idempotency_key,
        )

    def get_creative_bundle(
        self, principal: Principal, brief_id: str
    ) -> dict[str, Any]:
        return self.creative_service.get_bundle(principal, brief_id)

    def update_creative_brief(
        self,
        principal: Principal,
        brief_id: str,
        *,
        base_version: int,
        changes: dict[str, Any],
    ) -> dict[str, Any]:
        return self.creative_service.update_brief(
            principal,
            brief_id,
            base_version=base_version,
            changes=changes,
        )

    def save_rule_candidates(
        self,
        principal: Principal,
        brief_id: str,
        *,
        base_version: int,
        candidates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return self.creative_service.save_rule_candidates(
            principal,
            brief_id,
            base_version=base_version,
            candidates=candidates,
        )

    def confirm_creative_brief(
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
        return self.creative_service.confirm_brief(
            principal,
            brief_id,
            base_version=base_version,
            selected_candidate_id=selected_candidate_id,
            merged_candidate_ids=merged_candidate_ids,
            rejected_candidate_ids=rejected_candidate_ids,
            idempotency_key=idempotency_key,
        )

    def abandon_creative_brief(
        self,
        principal: Principal,
        brief_id: str,
        *,
        base_version: int,
    ) -> dict[str, Any]:
        return self.creative_service.abandon_brief(
            principal,
            brief_id,
            base_version=base_version,
        )
