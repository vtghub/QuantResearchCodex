from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from quantresearch_api.schemas import TenantContext

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
DEFAULT_WORKSPACE_ID = UUID("00000000-0000-0000-0000-000000000002")

ROLE_PLATFORM_ADMIN = "platform_admin"
ROLE_ORG_ADMIN = "organization_admin"
ROLE_RESEARCHER = "researcher"
ROLE_TRADER = "trader"
ROLE_VIEWER = "viewer"
bearer_scheme = HTTPBearer(auto_error=False)


async def get_tenant_context(
    x_tenant_id: Annotated[UUID | None, Header(alias="x-tenant-id")] = None,
    x_workspace_id: Annotated[UUID | None, Header(alias="x-workspace-id")] = None,
    x_role: Annotated[str, Header(alias="x-role")] = "platform_admin",
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> TenantContext:
    if credentials is not None:
        from quantresearch_api.auth import decode_token

        try:
            payload = decode_token(credentials.credentials)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token",
            ) from exc
        return TenantContext(
            tenant_id=UUID(payload["tenant_id"]),
            workspace_id=UUID(payload["workspace_id"]),
            role=payload["role"],
        )

    return TenantContext(
        tenant_id=x_tenant_id or DEFAULT_TENANT_ID,
        workspace_id=x_workspace_id or DEFAULT_WORKSPACE_ID,
        role=x_role,
    )


def require_roles(*allowed_roles: str):
    async def dependency(
        context: Annotated[TenantContext, Depends(get_tenant_context)],
    ) -> TenantContext:
        if context.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role for this operation",
            )
        return context

    return dependency
