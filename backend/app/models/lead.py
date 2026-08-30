import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, SoftDeleteMixin, TenantMixin, TimestampMixin, UUIDPKMixin
from app.models.audit_log import JSONType


class LeadStatus(UUIDPKMixin, TenantMixin, TimestampMixin, Base):
    """Per-organization customizable pipeline stage (section 11: 'Allow
    organizations to customize statuses'). Seeded with the default 12-stage
    pipeline when an organization is created."""

    __tablename__ = "lead_statuses"
    __table_args__ = (UniqueConstraint("organization_id", "key", name="uq_lead_status_org_key"),)

    key: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_won: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_lost: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Lead(UUIDPKMixin, TenantMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "leads"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    whatsapp_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    alternate_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    source: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    campaign: Mapped[str | None] = mapped_column(String(150), nullable=True)

    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
    )
    status_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("lead_statuses.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    budget_min: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    budget_max: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    preferred_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    property_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bedrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bathrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    purpose: Mapped[str | None] = mapped_column(String(32), nullable=True)  # buy | rent | invest
    timeline: Mapped[str | None] = mapped_column(String(64), nullable=True)
    financing_status: Mapped[str | None] = mapped_column(String(64), nullable=True)

    notes: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    tags: Mapped[list | None] = mapped_column(JSONType, nullable=True)

    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_follow_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    status: Mapped[LeadStatus] = relationship(lazy="selectin")

    @property
    def status_key(self) -> str:
        return self.status.key

    @property
    def temperature(self) -> str:
        if self.score >= 81:
            return "very_hot"
        if self.score >= 61:
            return "hot"
        if self.score >= 31:
            return "warm"
        return "cold"


class LeadActivity(UUIDPKMixin, TenantMixin, Base):
    """Append-only activity timeline entry (section 14). Never updated or
    deleted through the API."""

    __tablename__ = "lead_activities"

    lead_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(64), nullable=False)  # call|whatsapp|email|note|status_change|...
    payload: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
