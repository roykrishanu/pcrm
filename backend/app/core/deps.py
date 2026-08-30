"""Auth/authorization dependencies. Every protected route depends on
`get_current_user` (never trusts organization_id/user_id/role from the
request) and, where a specific capability is required, on
`require_permission(...)`.
"""
import uuid

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import PermissionDeniedError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.organization import Organization
from app.models.user import User

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise UnauthorizedError()
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise UnauthorizedError("Invalid or expired token.")

    user_id = uuid.UUID(payload["sub"])
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None or not user.is_active or user.is_deleted:
        raise UnauthorizedError("Account is not active.")

    if user.organization_id is not None:
        org = (await db.execute(
            select(Organization).where(Organization.id == user.organization_id)
        )).scalar_one_or_none()
        if org is None or not org.is_active:
            raise UnauthorizedError("Organization is not active.")

    return user


def get_current_org_id(user: User = Depends(get_current_user)) -> uuid.UUID:
    """The ONLY legitimate source of organization_id for a scoped query.
    Never accept organization_id as a path/query/body param on tenant routes."""
    if user.organization_id is None:
        raise UnauthorizedError("This action requires an organization context.")
    return user.organization_id


def require_super_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_super_admin:
        raise PermissionDeniedError("Super admin access required.")
    return user


def require_permission(permission_key: str):
    async def _checker(user: User = Depends(get_current_user)) -> User:
        if user.is_super_admin:
            return user
        role = user.role
        if role is None:
            raise PermissionDeniedError()
        if role.slug == "owner":
            return user
        granted = {p.key for p in role.permissions}
        if permission_key not in granted:
            raise PermissionDeniedError(f"Missing permission: {permission_key}")
        return user

    return _checker
