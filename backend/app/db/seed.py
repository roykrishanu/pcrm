"""Reusable seed routines — called from the Alembic data-seed migration in
real deployments, and directly from the test fixtures / dev bootstrap
(app.main lifespan) for SQLite. Idempotent: safe to call repeatedly."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import DEFAULT_LEAD_STATUSES, DEFAULT_ROLE_LABELS, DEFAULT_ROLES, PERMISSION_CATALOG
from app.models.lead import LeadStatus
from app.models.rbac import Permission, Role


async def seed_permissions(db: AsyncSession) -> None:
    existing = {p.key for p in (await db.execute(select(Permission))).scalars()}
    for key, description, category in PERMISSION_CATALOG:
        if key not in existing:
            db.add(Permission(key=key, description=description, category=category))
    await db.flush()


async def seed_default_roles(db: AsyncSession, organization_id: uuid.UUID) -> dict[str, Role]:
    """Creates the six system roles for a brand-new organization. Returns a
    slug -> Role map."""
    all_permissions = {p.key: p for p in (await db.execute(select(Permission))).scalars()}
    roles: dict[str, Role] = {}
    for slug, permission_keys in DEFAULT_ROLES.items():
        role = Role(
            organization_id=organization_id,
            name=DEFAULT_ROLE_LABELS[slug],
            slug=slug,
            is_system=True,
            permissions=[all_permissions[k] for k in permission_keys if k in all_permissions],
        )
        db.add(role)
        roles[slug] = role
    await db.flush()
    return roles


async def seed_default_lead_statuses(db: AsyncSession, organization_id: uuid.UUID) -> dict[str, LeadStatus]:
    statuses: dict[str, LeadStatus] = {}
    for order, (key, label, is_won, is_lost) in enumerate(DEFAULT_LEAD_STATUSES):
        status = LeadStatus(
            organization_id=organization_id, key=key, label=label,
            sort_order=order, is_won=is_won, is_lost=is_lost,
        )
        db.add(status)
        statuses[key] = status
    await db.flush()
    return statuses
