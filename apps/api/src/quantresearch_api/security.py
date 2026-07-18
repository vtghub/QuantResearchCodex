from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Header

from quantresearch_api.schemas import TenantContext


async def get_tenant_context(
    x_tenant_id: Annotated[UUID | None, Header(alias="x-tenant-id")] = None,
    x_workspace_id: Annotated[UUID | None, Header(alias="x-workspace-id")] = None,
    x_role: Annotated[str, Header(alias="x-role")] = "platform_admin",
) -> TenantContext:
    return TenantContext(
        tenant_id=x_tenant_id or uuid4(),
        workspace_id=x_workspace_id or uuid4(),
        role=x_role,
    )
