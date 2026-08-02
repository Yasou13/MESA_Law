from datetime import datetime

from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.core.policies import MatterAccessPolicy
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.mesa import MesaScopeBinding
from apps.api.models.queue import Job
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/matters", tags=["MESA bindings"])


class MesaBindingCreate(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    mesa_tenant_id: str = Field(min_length=1, max_length=128)
    workspace_id: str = Field(min_length=1, max_length=128)
    dataset_id: str = Field(min_length=1, max_length=128)
    agent_id: str = Field(min_length=1, max_length=128)


class MesaBindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    matter_id: str
    mesa_tenant_id: str
    workspace_id: str
    dataset_id: str
    agent_id: str
    provisioning_status: str
    last_verified_at: datetime | None
    last_error: str | None
    version_id: int


@router.get(
    "/{matter_id}/mesa-binding",
    response_model=MesaBindingResponse,
    operation_id="getMesaBinding",
)
async def get_mesa_binding(
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    await MatterAccessPolicy.can_read(context, db, matter_id)
    binding = await db.scalar(
        select(MesaScopeBinding).where(
            MesaScopeBinding.tenant_id == context.tenant_id,
            MesaScopeBinding.matter_id == matter_id,
        )
    )
    if binding is None:
        raise HTTPException(status_code=404, detail="MESA binding not found")
    return binding


@router.put(
    "/{matter_id}/mesa-binding",
    response_model=MesaBindingResponse,
    operation_id="createMesaBinding",
    status_code=status.HTTP_201_CREATED,
)
async def create_mesa_binding(
    matter_id: str,
    payload: MesaBindingCreate,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    await MatterAccessPolicy.can_write(context, db, matter_id)
    existing = await db.scalar(
        select(MesaScopeBinding.id).where(
            MesaScopeBinding.tenant_id == context.tenant_id,
            MesaScopeBinding.matter_id == matter_id,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="MESA binding already exists and is immutable; inspect its status",
        )

    binding = MesaScopeBinding(
        tenant_id=context.tenant_id,
        matter_id=matter_id,
        mesa_tenant_id=payload.mesa_tenant_id,
        workspace_id=payload.workspace_id,
        dataset_id=payload.dataset_id,
        agent_id=payload.agent_id,
        provisioning_status="PENDING_PREFLIGHT",
    )
    db.add(binding)
    await db.flush()
    db.add(
        Job(
            type="PROVISION_MESA_SCOPE",
            tenant_id=context.tenant_id,
            matter_id=matter_id,
            requested_by=context.principal_id,
            idempotency_key=f"mesa-preflight:{binding.id}:{binding.version_id}",
            payload={"binding_id": binding.id, "matter_id": matter_id},
        )
    )
    await db.commit()
    return binding
