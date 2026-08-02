from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.core.policies import AdminAccessPolicy, MatterAccessPolicy
from apps.api.core.ratelimit import limiter
from apps.api.core.utils import utc_now
from apps.api.dependencies.auth import require_recent_auth, setup_tenant_context
from apps.api.models.domain import Matter, User
from apps.api.schemas.api import MatterCreate, MatterResponse
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def _matter_response(
    matter: Matter, access_scope: str, responsible_attorney: str | None
) -> dict:
    return {
        "id": matter.id,
        "title": matter.title,
        "internal_reference": matter.internal_reference,
        "status": matter.status,
        "client_name": matter.client_name,
        "jurisdiction": matter.jurisdiction,
        "case_type": matter.case_type,
        "confidentiality_level": matter.confidentiality_level,
        "ai_processing_policy": matter.ai_processing_policy,
        "opened_at": matter.opened_at.isoformat() if matter.opened_at else None,
        "closed_at": matter.closed_at.isoformat() if matter.closed_at else None,
        "access_scope": access_scope,
        "responsible_attorney": responsible_attorney,
        "created_at": matter.created_at,
        "updated_at": matter.updated_at,
    }


@router.get("", response_model=list[MatterResponse], operation_id="listMatters")
@limiter.limit("100/minute")
async def list_matters(
    request: Request,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    MatterAccessPolicy.can_list(context)
    from apps.api.models.domain import MatterMember

    stmt = (
        select(Matter, MatterMember.access_scope, User.full_name)
        .join(
            MatterMember,
            (Matter.id == MatterMember.matter_id)
            & (MatterMember.user_id == context.principal_id),
        )
        .where(
            Matter.tenant_id == context.tenant_id,
            MatterMember.tenant_id == context.tenant_id,
        )
        .outerjoin(User, Matter.responsible_attorney_id == User.id)
        .order_by(Matter.created_at.desc())
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [_matter_response(m, scope, attorney) for m, scope, attorney in rows]


from apps.api.core.idempotency import check_idempotency, complete_idempotency
from fastapi import Header


@router.get("/{matter_id}", response_model=MatterResponse, operation_id="getMatter")
@limiter.limit("100/minute")
async def get_matter(
    request: Request,
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    await MatterAccessPolicy.can_read(context, db, matter_id)

    matter = await db.get(Matter, matter_id)
    if not matter or matter.tenant_id != context.tenant_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Matter not found")

    # Get user's scope
    from apps.api.models.domain import MatterMember

    stmt = select(MatterMember.access_scope).where(
        MatterMember.matter_id == matter_id,
        MatterMember.user_id == context.principal_id,
        MatterMember.tenant_id == context.tenant_id,
    )
    res = await db.execute(stmt)
    scope = res.scalar_one()
    responsible_attorney = None
    if matter.responsible_attorney_id:
        responsible_attorney = await db.scalar(
            select(User.full_name).where(User.id == matter.responsible_attorney_id)
        )

    return _matter_response(matter, scope, responsible_attorney)


@router.post(
    "", response_model=MatterResponse, operation_id="createMatter", status_code=201
)
@limiter.limit("30/minute")
async def create_matter(
    request: Request,
    matter_data: MatterCreate,
    idem_key: str | None = Header(None, alias="Idempotency-Key"),
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    if idem_key:
        cached = await check_idempotency(db, idem_key)
        if cached and cached.response_body:
            return cached.response_body

    await MatterAccessPolicy.can_create(context)
    now = utc_now()
    matter = Matter(
        title=matter_data.title,
        internal_reference=matter_data.internal_reference,
        client_name=matter_data.client_name,
        tenant_id=context.tenant_id,
        jurisdiction=matter_data.jurisdiction,
        case_type=matter_data.case_type,
        confidentiality_level=matter_data.confidentiality_level,
        ai_processing_policy=matter_data.ai_processing_policy,
        responsible_attorney_id=context.principal_id,
        opened_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(matter)
    await db.flush()

    from apps.api.models.domain import MatterMember

    member = MatterMember(
        matter_id=matter.id,
        user_id=context.principal_id,
        access_scope="admin",
        tenant_id=context.tenant_id,
    )
    db.add(member)

    await db.commit()
    await db.refresh(matter)

    responsible_attorney = await db.scalar(
        select(User.full_name).where(User.id == context.principal_id)
    )
    if not isinstance(responsible_attorney, str):
        responsible_attorney = None
    resp = _matter_response(matter, "admin", responsible_attorney)

    if idem_key:
        await complete_idempotency(db, idem_key, 201, resp)

    return resp


@router.post("/{matter_id}/rebuild-mesa", operation_id="rebuildMatterMesa")
@limiter.limit("5/minute")
async def rebuild_matter_mesa(
    request: Request,
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    AdminAccessPolicy.can_rebuild_mesa(context)
    await MatterAccessPolicy.can_manage_members(context, db, matter_id)
    from fastapi import HTTPException

    raise HTTPException(
        status_code=501, detail="MESA Core v4 rebuild is not implemented"
    )


from apps.api.core.qa import QAResponse, QuestionRequest, ask_matter_question


@router.post("/{matter_id}/qa", operation_id="matterQA", response_model=QAResponse)
@limiter.limit("20/minute")
async def matter_qa_endpoint(
    request: Request,
    matter_id: str,
    query: QuestionRequest,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    await MatterAccessPolicy.can_read(context, db, matter_id)
    return await ask_matter_question(
        db, context.tenant_id, matter_id, None, query.question
    )


class MatterPartyResponse(BaseModel):
    id: str
    name: str
    role: str
    type: str


@router.get(
    "/{matter_id}/parties",
    response_model=list[MatterPartyResponse],
    operation_id="listMatterParties",
)
async def list_matter_parties(
    matter_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    await MatterAccessPolicy.can_read(context, db, matter_id)
    from apps.api.models.domain import MatterParty

    result = await db.execute(
        select(MatterParty).where(MatterParty.matter_id == matter_id)
    )
    return result.scalars().all()


class ConflictCheckRequest(BaseModel):
    party_names: list[str]


class ConflictResult(BaseModel):
    searched_name: str
    matched_name: str
    role: str
    matter_id: str
    matter_title: str
    status: str


class ConflictCheckResponse(BaseModel):
    id: str
    has_conflicts: bool
    conflicts: list[ConflictResult]


@router.post(
    "/conflict-check",
    response_model=ConflictCheckResponse,
    operation_id="conflictCheck",
)
@limiter.limit("20/minute")
async def check_conflicts(
    request: Request,
    payload: ConflictCheckRequest,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    MatterAccessPolicy.can_list(context)

    from apps.api.models.domain import Matter, MatterParty
    from sqlalchemy import select

    results = []
    for party_name in payload.party_names:
        from apps.api.models.domain import MatterMember

        stmt = (
            select(MatterParty, Matter)
            .join(Matter, MatterParty.matter_id == Matter.id)
            .join(
                MatterMember,
                (MatterMember.matter_id == Matter.id)
                & (MatterMember.user_id == context.principal_id),
            )
            .where(
                MatterParty.tenant_id == context.tenant_id,
                MatterMember.tenant_id == context.tenant_id,
                MatterParty.name.ilike(f"%{party_name}%"),
            )
        )
        res = await db.execute(stmt)
        matches = res.all()
        for mp, m in matches:
            results.append(
                ConflictResult(
                    searched_name=party_name,
                    matched_name=mp.name,
                    role=mp.role,
                    matter_id=m.id,
                    matter_title=m.title,
                    status=m.status,
                )
            )

    from apps.api.models.domain import ConflictCheckResult

    check_record = ConflictCheckResult(
        tenant_id=context.tenant_id,
        requested_by=context.principal_id,
        party_names=payload.party_names,
        has_conflicts=len(results) > 0,
        results=[r.model_dump() for r in results],
    )
    db.add(check_record)
    await db.commit()
    await db.refresh(check_record)

    return ConflictCheckResponse(
        id=check_record.id, conflicts=results, has_conflicts=len(results) > 0
    )


class OverrideConflictRequest(BaseModel):
    reason: str


class OverrideConflictResponse(BaseModel):
    status: str
    message: str


@router.post(
    "/{matter_id}/override-conflict",
    operation_id="overrideConflict",
    response_model=OverrideConflictResponse,
)
@limiter.limit("5/minute")
async def override_conflict(
    request: Request,
    matter_id: str,
    payload: OverrideConflictRequest,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_recent_auth),
):
    await MatterAccessPolicy.can_manage_members(context, db, matter_id)

    matter = await db.get(Matter, matter_id)
    if not matter or matter.tenant_id != context.tenant_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Matter not found")

    from apps.api.models.audit import AuditEvent

    db.add(
        AuditEvent(
            tenant_id=context.tenant_id,
            user_id=context.principal_id,
            action="CONFLICT_OVERRIDE",
            entity_type="matter",
            entity_id=matter.id,
            changes={"reason": payload.reason},
        )
    )

    await db.commit()
    return OverrideConflictResponse(
        status="success", message="Conflict check override recorded in the audit log"
    )
