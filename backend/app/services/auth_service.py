"""Auth business logic. Routes stay thin; all rules (lockout, token
lifetimes, tenant creation) live here so they're covered by one set of tests."""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    verify_password,
)
from app.core.timeutils import aware
from app.db.seed import seed_default_lead_statuses, seed_default_roles, seed_permissions
from app.models.auth_tokens import OneTimeToken, Session as AuthSession
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import RegisterOrganizationRequest
from app.services import audit_service, email_service

settings = get_settings()

MAX_FAILED_LOGINS = settings.LOGIN_LOCKOUT_THRESHOLD
LOCKOUT_DURATION = timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)


async def register_organization(db: AsyncSession, payload: RegisterOrganizationRequest) -> tuple[Organization, User]:
    existing = (await db.execute(select(Organization).where(Organization.slug == payload.slug))).scalar_one_or_none()
    if existing is not None:
        raise ConflictError("An organization with this slug already exists.")

    await seed_permissions(db)

    org = Organization(name=payload.organization_name, slug=payload.slug)
    db.add(org)
    await db.flush()

    roles = await seed_default_roles(db, org.id)
    await seed_default_lead_statuses(db, org.id)

    owner = User(
        organization_id=org.id,
        role_id=roles["owner"].id,
        name=payload.owner_name,
        email=payload.owner_email.lower(),
        password_hash=hash_password(payload.owner_password),
        is_active=True,
        is_email_verified=False,
    )
    db.add(owner)
    try:
        await db.flush()
    except IntegrityError:
        raise ConflictError("An organization with this slug already exists.")

    await audit_service.record(
        db, organization_id=org.id, actor_user_id=owner.id,
        action="organization.created", entity_type="organization", entity_id=str(org.id),
    )

    token = generate_opaque_token()
    db.add(OneTimeToken(
        user_id=owner.id, token_hash=hash_opaque_token(token), purpose="email_verify",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS),
    ))
    await db.commit()
    email_service.send_verification_email(to=owner.email, token=token)
    return org, owner


async def authenticate(
    db: AsyncSession, *, email: str, password: str, organization_slug: str | None,
    ip_address: str | None, user_agent: str | None,
) -> tuple[User, str, str]:
    """Returns (user, access_token, refresh_token). Raises UnauthorizedError
    on any failure — deliberately the SAME error for 'no such user' and
    'wrong password' so login can't be used to enumerate accounts."""
    query = select(User).where(User.email == email.lower())
    if organization_slug:
        org = (await db.execute(select(Organization).where(Organization.slug == organization_slug))).scalar_one_or_none()
        if org is None:
            raise UnauthorizedError("Invalid email or password.")
        query = query.where(User.organization_id == org.id)
    user = (await db.execute(query)).scalars().first()

    generic_error = UnauthorizedError("Invalid email or password.")
    if user is None or user.is_deleted:
        raise generic_error

    now = datetime.now(timezone.utc)
    if aware(user.locked_until) and aware(user.locked_until) > now:
        raise UnauthorizedError("Account temporarily locked due to failed login attempts. Try again later.")

    if not user.is_active:
        raise UnauthorizedError("Account is deactivated.")

    if not verify_password(password, user.password_hash):
        user.failed_login_count += 1
        if user.failed_login_count >= MAX_FAILED_LOGINS:
            user.locked_until = now + LOCKOUT_DURATION
            user.failed_login_count = 0
        await db.commit()
        raise generic_error

    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = now
    await db.flush()

    access_token = create_access_token(
        user_id=user.id, organization_id=user.organization_id,
        role_slug=user.role.slug if user.role else None, is_super_admin=user.is_super_admin,
    )
    refresh_token = generate_opaque_token()
    db.add(AuthSession(
        user_id=user.id,
        refresh_token_hash=hash_opaque_token(refresh_token),
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        last_used_at=now,
    ))
    await audit_service.record(
        db, organization_id=user.organization_id, actor_user_id=user.id,
        action="auth.login", entity_type="user", entity_id=str(user.id), ip_address=ip_address,
    )
    await db.commit()
    return user, access_token, refresh_token


async def refresh_access_token(db: AsyncSession, *, refresh_token: str) -> tuple[str, str]:
    """Rotates the refresh token on every use (reduces replay window) and
    returns (new_access_token, new_refresh_token)."""
    token_hash = hash_opaque_token(refresh_token)
    session = (await db.execute(
        select(AuthSession).where(AuthSession.refresh_token_hash == token_hash)
    )).scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if session is None or session.revoked_at is not None or aware(session.expires_at) < now:
        raise UnauthorizedError("Invalid or expired refresh token.")

    user = (await db.execute(select(User).where(User.id == session.user_id))).scalar_one_or_none()
    if user is None or not user.is_active or user.is_deleted:
        raise UnauthorizedError("Account is not active.")

    session.revoked_at = now
    new_refresh_token = generate_opaque_token()
    db.add(AuthSession(
        user_id=user.id,
        refresh_token_hash=hash_opaque_token(new_refresh_token),
        ip_address=session.ip_address,
        user_agent=session.user_agent,
        device_label=session.device_label,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        last_used_at=now,
    ))
    access_token = create_access_token(
        user_id=user.id, organization_id=user.organization_id,
        role_slug=user.role.slug if user.role else None, is_super_admin=user.is_super_admin,
    )
    await db.commit()
    return access_token, new_refresh_token


async def revoke_session(db: AsyncSession, *, user_id: uuid.UUID, refresh_token: str) -> None:
    token_hash = hash_opaque_token(refresh_token)
    session = (await db.execute(
        select(AuthSession).where(AuthSession.refresh_token_hash == token_hash, AuthSession.user_id == user_id)
    )).scalar_one_or_none()
    if session is not None:
        session.revoked_at = datetime.now(timezone.utc)
        await db.commit()


async def revoke_all_sessions(db: AsyncSession, *, user_id: uuid.UUID) -> None:
    sessions = (await db.execute(
        select(AuthSession).where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
    )).scalars().all()
    now = datetime.now(timezone.utc)
    for s in sessions:
        s.revoked_at = now
    await db.commit()


async def request_password_reset(db: AsyncSession, *, email: str, organization_slug: str | None) -> None:
    """Always succeeds silently from the caller's perspective (route returns
    a generic message) to avoid leaking whether an email exists."""
    query = select(User).where(User.email == email.lower())
    if organization_slug:
        org = (await db.execute(select(Organization).where(Organization.slug == organization_slug))).scalar_one_or_none()
        if org is None:
            return
        query = query.where(User.organization_id == org.id)
    user = (await db.execute(query)).scalars().first()
    if user is None:
        return

    token = generate_opaque_token()
    db.add(OneTimeToken(
        user_id=user.id, token_hash=hash_opaque_token(token), purpose="password_reset",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
    ))
    await db.commit()
    email_service.send_password_reset_email(to=user.email, token=token)


async def _consume_token(db: AsyncSession, *, token: str, purpose: str) -> OneTimeToken:
    token_hash = hash_opaque_token(token)
    record = (await db.execute(
        select(OneTimeToken).where(OneTimeToken.token_hash == token_hash, OneTimeToken.purpose == purpose)
    )).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if record is None or record.used_at is not None or aware(record.expires_at) < now:
        raise UnauthorizedError("Invalid or expired token.")
    record.used_at = now
    return record


async def confirm_password_reset(db: AsyncSession, *, token: str, new_password: str) -> None:
    record = await _consume_token(db, token=token, purpose="password_reset")
    user = (await db.execute(select(User).where(User.id == record.user_id))).scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("Invalid or expired token.")
    user.password_hash = hash_password(new_password)
    await revoke_all_sessions(db, user_id=user.id)
    await audit_service.record(
        db, organization_id=user.organization_id, actor_user_id=user.id,
        action="auth.password_reset", entity_type="user", entity_id=str(user.id),
    )
    await db.commit()


async def confirm_email_verification(db: AsyncSession, *, token: str) -> None:
    record = await _consume_token(db, token=token, purpose="email_verify")
    user = (await db.execute(select(User).where(User.id == record.user_id))).scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("Invalid or expired token.")
    user.is_email_verified = True
    await db.commit()


async def change_password(db: AsyncSession, *, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise UnauthorizedError("Current password is incorrect.")
    user.password_hash = hash_password(new_password)
    await revoke_all_sessions(db, user_id=user.id)
    await db.commit()
