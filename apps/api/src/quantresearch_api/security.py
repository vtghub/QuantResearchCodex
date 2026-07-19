from typing import Annotated
from uuid import UUID

from fastapi import Header

from quantresearch_api.schemas import TenantContext

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
DEFAULT_WORKSPACE_ID = UUID("00000000-0000-0000-0000-000000000002")


async def get_tenant_context(
    x_tenant_id: Annotated[UUID | None, Header(alias="x-tenant-id")] = None,
    x_workspace_id: Annotated[UUID | None, Header(alias="x-workspace-id")] = None,
    x_role: Annotated[str, Header(alias="x-role")] = "platform_admin",
) -> TenantContext:
    return TenantContext(
        tenant_id=x_tenant_id or DEFAULT_TENANT_ID,
        workspace_id=x_workspace_id or DEFAULT_WORKSPACE_ID,
        role=x_role,
    )
