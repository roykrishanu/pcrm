import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from app.schemas.auth import validate_password_strength


class UserOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    phone: str | None
    job_title: str | None
    role_id: uuid.UUID | None
    role_name: str | None = None
    team_id: uuid.UUID | None
    is_active: bool
    is_email_verified: bool
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class InviteUserRequest(BaseModel):
    name: str
    email: EmailStr
    role_id: uuid.UUID
    team_id: uuid.UUID | None = None
    job_title: str | None = None


class AcceptInviteRequest(BaseModel):
    token: str
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_strength(v)


class UpdateUserRequest(BaseModel):
    name: str | None = None
    phone: str | None = None
    job_title: str | None = None
    role_id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None
    is_active: bool | None = None
