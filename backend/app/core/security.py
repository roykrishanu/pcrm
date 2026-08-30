"""Password hashing, JWT issuance, and opaque-token hashing.

Design: access tokens are short-lived stateless JWTs (org_id/user_id/role
baked in at issue time, never trusted from the client afterward — every
protected route re-derives identity from THIS token, not from request
params). Refresh tokens are long-lived random opaque strings; only their
SHA-256 hash is stored (in `sessions`), so a stolen DB dump doesn't yield
usable refresh tokens. Same hash-only pattern for email-verify / password-
reset tokens.
"""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def generate_opaque_token() -> str:
    """Raw, high-entropy token to hand to the client (refresh token, email
    verification link, password reset link). Never stored raw."""
    return secrets.token_urlsafe(48)


def hash_opaque_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(*, user_id: uuid.UUID, organization_id: uuid.UUID | None,
                         role_slug: str | None, is_super_admin: bool) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "org_id": str(organization_id) if organization_id else None,
        "role": role_slug,
        "super_admin": is_super_admin,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Raises jwt.PyJWTError on invalid/expired token — callers must catch it."""
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("not an access token")
    return payload
