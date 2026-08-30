"""RBAC: roles are per-organization (so orgs can customize), permissions are
a fixed platform-defined catalog of granular capability strings
(e.g. "leads.create"). A role holds a set of permissions; a user holds one
role. See app/core/permissions.py for the capability catalog and the
`require_permission` dependency that enforces this server-side."""
import uuid

from sqlalchemy import Boolean, ForeignKey, String, Table, Column, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, TimestampMixin, UUIDPKMixin

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", GUID(), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_key", String(64), ForeignKey("permissions.key", ondelete="CASCADE"), primary_key=True),
)


class Permission(Base):
    """Fixed catalog row, e.g. key='leads.create'. Seeded by migration, not
    user-editable — the catalog itself is not multi-tenant."""

    __tablename__ = "permissions"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)


class Role(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("organization_id", "slug", name="uq_role_org_slug"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    """System roles (owner/admin/manager/agent/sales_executive/viewer) are
    seeded per-organization at creation and cannot be deleted."""

    permissions: Mapped[list[Permission]] = relationship(
        secondary=role_permissions, lazy="selectin"
    )


class Team(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "teams"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
