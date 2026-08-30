import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_org_id, require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import Page
from app.schemas.lead import (
    LeadActivityCreate,
    LeadActivityOut,
    LeadCreate,
    LeadOut,
    LeadStatusChange,
    LeadUpdate,
)
from app.services import lead_service

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadOut, status_code=201)
async def create_lead(
    payload: LeadCreate,
    org_id: uuid.UUID = Depends(get_current_org_id),
    user: User = Depends(require_permission("leads.create")),
    db: AsyncSession = Depends(get_db),
):
    lead = await lead_service.create_lead(db, organization_id=org_id, actor_user_id=user.id, payload=payload)
    return LeadOut.model_validate(lead)


@router.get("", response_model=Page[LeadOut])
async def list_leads(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_key: str | None = None,
    assigned_user_id: uuid.UUID | None = None,
    search: str | None = None,
    org_id: uuid.UUID = Depends(get_current_org_id),
    _: User = Depends(require_permission("leads.read")),
    db: AsyncSession = Depends(get_db),
):
    leads, total = await lead_service.list_leads(
        db, organization_id=org_id, page=page, page_size=page_size,
        status_key=status_key, assigned_user_id=assigned_user_id, search=search,
    )
    return Page(items=[LeadOut.model_validate(lead) for lead in leads], total=total, page=page, page_size=page_size)


@router.get("/{lead_id}", response_model=LeadOut)
async def get_lead(
    lead_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_current_org_id),
    _: User = Depends(require_permission("leads.read")),
    db: AsyncSession = Depends(get_db),
):
    lead = await lead_service.get_lead(db, organization_id=org_id, lead_id=lead_id)
    return LeadOut.model_validate(lead)


@router.patch("/{lead_id}", response_model=LeadOut)
async def update_lead(
    lead_id: uuid.UUID,
    payload: LeadUpdate,
    org_id: uuid.UUID = Depends(get_current_org_id),
    user: User = Depends(require_permission("leads.update")),
    db: AsyncSession = Depends(get_db),
):
    lead = await lead_service.update_lead(
        db, organization_id=org_id, actor_user_id=user.id, lead_id=lead_id, payload=payload
    )
    return LeadOut.model_validate(lead)


@router.post("/{lead_id}/status", response_model=LeadOut)
async def change_status(
    lead_id: uuid.UUID,
    payload: LeadStatusChange,
    org_id: uuid.UUID = Depends(get_current_org_id),
    user: User = Depends(require_permission("leads.update")),
    db: AsyncSession = Depends(get_db),
):
    lead = await lead_service.change_lead_status(
        db, organization_id=org_id, actor_user_id=user.id, lead_id=lead_id, new_status_key=payload.status_key
    )
    return LeadOut.model_validate(lead)


@router.delete("/{lead_id}", status_code=204)
async def delete_lead(
    lead_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_current_org_id),
    user: User = Depends(require_permission("leads.delete")),
    db: AsyncSession = Depends(get_db),
):
    await lead_service.delete_lead(db, organization_id=org_id, actor_user_id=user.id, lead_id=lead_id)


@router.get("/{lead_id}/activities", response_model=list[LeadActivityOut])
async def list_activities(
    lead_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_current_org_id),
    _: User = Depends(require_permission("leads.read")),
    db: AsyncSession = Depends(get_db),
):
    activities = await lead_service.list_activities(db, organization_id=org_id, lead_id=lead_id)
    return [LeadActivityOut.model_validate(a) for a in activities]


@router.post("/{lead_id}/activities", response_model=LeadActivityOut, status_code=201)
async def add_activity(
    lead_id: uuid.UUID,
    payload: LeadActivityCreate,
    org_id: uuid.UUID = Depends(get_current_org_id),
    user: User = Depends(require_permission("leads.update")),
    db: AsyncSession = Depends(get_db),
):
    activity = await lead_service.add_activity(
        db, organization_id=org_id, actor_user_id=user.id, lead_id=lead_id,
        type_=payload.type, payload=payload.payload,
    )
    return LeadActivityOut.model_validate(activity)
