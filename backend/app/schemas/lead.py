import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class LeadCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    phone: str | None = None
    email: EmailStr | None = None
    whatsapp_number: str | None = None
    alternate_phone: str | None = None
    source: str | None = None
    campaign: str | None = None
    assigned_user_id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None
    status_key: str | None = None  # defaults to org's "new" status
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    preferred_location: str | None = None
    property_type: str | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    purpose: str | None = None
    timeline: str | None = None
    financing_status: str | None = None
    notes: str | None = None
    tags: list[str] | None = None


class LeadUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    whatsapp_number: str | None = None
    alternate_phone: str | None = None
    source: str | None = None
    campaign: str | None = None
    assigned_user_id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    preferred_location: str | None = None
    property_type: str | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    purpose: str | None = None
    timeline: str | None = None
    financing_status: str | None = None
    notes: str | None = None
    tags: list[str] | None = None
    next_follow_up_at: datetime | None = None


class LeadStatusChange(BaseModel):
    status_key: str


class LeadOut(BaseModel):
    id: uuid.UUID
    name: str
    phone: str | None
    email: str | None
    whatsapp_number: str | None
    source: str | None
    campaign: str | None
    assigned_user_id: uuid.UUID | None
    team_id: uuid.UUID | None
    status_key: str
    budget_min: Decimal | None
    budget_max: Decimal | None
    preferred_location: str | None
    property_type: str | None
    bedrooms: int | None
    bathrooms: int | None
    purpose: str | None
    timeline: str | None
    financing_status: str | None
    notes: str | None
    tags: list[str] | None
    score: int
    temperature: str
    next_follow_up_at: datetime | None
    last_activity_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class LeadActivityCreate(BaseModel):
    type: str
    payload: dict | None = None


class LeadActivityOut(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID
    actor_user_id: uuid.UUID | None
    type: str
    payload: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
