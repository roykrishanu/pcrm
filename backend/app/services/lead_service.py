"""Lead CRUD + pipeline transitions + activity timeline.

Every function takes organization_id explicitly and filters by it — this is
the tenant-isolation boundary (section 7). Never build a Lead query without
this filter.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.lead import Lead, LeadActivity, LeadStatus
from app.schemas.lead import LeadCreate, LeadUpdate
from app.services import audit_service, scoring_service


async def _get_status(db: AsyncSession, *, organization_id: uuid.UUID, key: str) -> LeadStatus:
    status = (await db.execute(
        select(LeadStatus).where(LeadStatus.organization_id == organization_id, LeadStatus.key == key)
    )).scalar_one_or_none()
    if status is None:
        raise NotFoundError("LeadStatus")
    return status


async def create_lead(
    db: AsyncSession, *, organization_id: uuid.UUID, actor_user_id: uuid.UUID, payload: LeadCreate,
) -> Lead:
    status = await _get_status(db, organization_id=organization_id, key=payload.status_key or "new")
    lead = Lead(
        organization_id=organization_id,
        status_id=status.id,
        last_activity_at=datetime.now(timezone.utc),
        **payload.model_dump(exclude={"status_key"}),
    )
    db.add(lead)
    await db.flush()

    db.add(LeadActivity(
        organization_id=organization_id, lead_id=lead.id, actor_user_id=actor_user_id,
        type="lead_created", payload={"source": lead.source},
    ))
    await audit_service.record(
        db, organization_id=organization_id, actor_user_id=actor_user_id,
        action="lead.created", entity_type="lead", entity_id=str(lead.id),
    )
    await db.commit()
    await db.refresh(lead)
    return lead


async def get_lead(db: AsyncSession, *, organization_id: uuid.UUID, lead_id: uuid.UUID) -> Lead:
    lead = (await db.execute(
        select(Lead).where(
            Lead.id == lead_id, Lead.organization_id == organization_id, Lead.deleted_at.is_(None)
        )
    )).scalar_one_or_none()
    if lead is None:
        raise NotFoundError("Lead")
    return lead


async def list_leads(
    db: AsyncSession, *, organization_id: uuid.UUID, page: int, page_size: int,
    status_key: str | None = None, assigned_user_id: uuid.UUID | None = None, search: str | None = None,
) -> tuple[list[Lead], int]:
    query = select(Lead).where(Lead.organization_id == organization_id, Lead.deleted_at.is_(None))
    count_query = select(func.count()).select_from(Lead).where(
        Lead.organization_id == organization_id, Lead.deleted_at.is_(None)
    )

    if status_key:
        status = await _get_status(db, organization_id=organization_id, key=status_key)
        query = query.where(Lead.status_id == status.id)
        count_query = count_query.where(Lead.status_id == status.id)
    if assigned_user_id:
        query = query.where(Lead.assigned_user_id == assigned_user_id)
        count_query = count_query.where(Lead.assigned_user_id == assigned_user_id)
    if search:
        like = f"%{search}%"
        cond = (Lead.name.ilike(like) | Lead.phone.ilike(like) | Lead.email.ilike(like))
        query = query.where(cond)
        count_query = count_query.where(cond)

    total = (await db.execute(count_query)).scalar_one()
    query = query.order_by(Lead.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    leads = (await db.execute(query)).scalars().all()
    return list(leads), total


async def update_lead(
    db: AsyncSession, *, organization_id: uuid.UUID, actor_user_id: uuid.UUID,
    lead_id: uuid.UUID, payload: LeadUpdate,
) -> Lead:
    lead = await get_lead(db, organization_id=organization_id, lead_id=lead_id)
    changes = payload.model_dump(exclude_unset=True)
    before = {k: str(getattr(lead, k)) for k in changes}
    for key, value in changes.items():
        setattr(lead, key, value)
    lead.last_activity_at = datetime.now(timezone.utc)
    await audit_service.record(
        db, organization_id=organization_id, actor_user_id=actor_user_id,
        action="lead.updated", entity_type="lead", entity_id=str(lead.id),
        before=before, after={k: str(v) for k, v in changes.items()},
    )
    await db.commit()
    await db.refresh(lead)
    return lead


async def change_lead_status(
    db: AsyncSession, *, organization_id: uuid.UUID, actor_user_id: uuid.UUID,
    lead_id: uuid.UUID, new_status_key: str,
) -> Lead:
    lead = await get_lead(db, organization_id=organization_id, lead_id=lead_id)
    old_status = lead.status.key
    new_status = await _get_status(db, organization_id=organization_id, key=new_status_key)

    lead.status_id = new_status.id
    lead.last_activity_at = datetime.now(timezone.utc)
    db.add(LeadActivity(
        organization_id=organization_id, lead_id=lead.id, actor_user_id=actor_user_id,
        type="status_change", payload={"from": old_status, "to": new_status_key},
    ))
    await audit_service.record(
        db, organization_id=organization_id, actor_user_id=actor_user_id,
        action="lead.status_changed", entity_type="lead", entity_id=str(lead.id),
        before={"status": old_status}, after={"status": new_status_key},
    )
    await db.commit()
    await db.refresh(lead)
    return lead


async def add_activity(
    db: AsyncSession, *, organization_id: uuid.UUID, actor_user_id: uuid.UUID,
    lead_id: uuid.UUID, type_: str, payload: dict | None,
) -> LeadActivity:
    lead = await get_lead(db, organization_id=organization_id, lead_id=lead_id)
    activity = LeadActivity(
        organization_id=organization_id, lead_id=lead.id, actor_user_id=actor_user_id,
        type=type_, payload=payload,
    )
    db.add(activity)
    lead.last_activity_at = datetime.now(timezone.utc)
    lead.score = scoring_service.apply_score_delta(lead.score, type_)
    await db.commit()
    await db.refresh(activity)
    return activity


async def list_activities(
    db: AsyncSession, *, organization_id: uuid.UUID, lead_id: uuid.UUID,
) -> list[LeadActivity]:
    await get_lead(db, organization_id=organization_id, lead_id=lead_id)  # 404s + tenant check
    result = await db.execute(
        select(LeadActivity)
        .where(LeadActivity.organization_id == organization_id, LeadActivity.lead_id == lead_id)
        .order_by(LeadActivity.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_lead(db: AsyncSession, *, organization_id: uuid.UUID, actor_user_id: uuid.UUID, lead_id: uuid.UUID) -> None:
    """Soft delete (section 78) — the row stays for audit/recovery purposes."""
    lead = await get_lead(db, organization_id=organization_id, lead_id=lead_id)
    lead.deleted_at = datetime.now(timezone.utc)
    await audit_service.record(
        db, organization_id=organization_id, actor_user_id=actor_user_id,
        action="lead.deleted", entity_type="lead", entity_id=str(lead_id),
    )
    await db.commit()
