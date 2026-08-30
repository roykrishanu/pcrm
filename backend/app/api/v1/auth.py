from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.core.errors import RateLimitedError
from app.core.rate_limit import check_rate_limit
from app.db.session import get_db
from app.models.auth_tokens import Session as AuthSession
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    EmailVerificationConfirm,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterOrganizationRequest,
    SessionOut,
    TokenResponse,
)
from app.schemas.user import UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register-organization", status_code=201)
async def register_organization(payload: RegisterOrganizationRequest, db: AsyncSession = Depends(get_db)):
    org, owner = await auth_service.register_organization(db, payload)
    return {"organization_id": str(org.id), "user_id": str(owner.id), "slug": org.slug}


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    settings = get_settings()
    if not check_rate_limit(f"login:{client_ip}", limit=settings.LOGIN_RATE_LIMIT_PER_MINUTE, window_seconds=60):
        raise RateLimitedError()
    if not check_rate_limit(f"login:{payload.email.lower()}", limit=settings.LOGIN_RATE_LIMIT_PER_MINUTE, window_seconds=60):
        raise RateLimitedError()

    _, access_token, refresh_token = await auth_service.authenticate(
        db, email=payload.email, password=payload.password, organization_slug=payload.organization_slug,
        ip_address=client_ip, user_agent=request.headers.get("user-agent"),
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    access_token, refresh_token = await auth_service.refresh_access_token(db, refresh_token=payload.refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=204)
async def logout(
    payload: RefreshRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    await auth_service.revoke_session(db, user_id=user.id, refresh_token=payload.refresh_token)


@router.post("/logout-all", status_code=204)
async def logout_all(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await auth_service.revoke_all_sessions(db, user_id=user.id)


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AuthSession)
        .where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
        .order_by(AuthSession.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/password-reset/request", status_code=202)
async def request_password_reset(payload: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.request_password_reset(db, email=payload.email, organization_slug=payload.organization_slug)
    return {"message": "If an account exists, a reset link has been sent."}


@router.post("/password-reset/confirm", status_code=204)
async def confirm_password_reset(payload: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    await auth_service.confirm_password_reset(db, token=payload.token, new_password=payload.new_password)


@router.post("/verify-email", status_code=204)
async def verify_email(payload: EmailVerificationConfirm, db: AsyncSession = Depends(get_db)):
    await auth_service.confirm_email_verification(db, token=payload.token)


@router.post("/change-password", status_code=204)
async def change_password(
    payload: ChangePasswordRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    await auth_service.change_password(
        db, user=user, current_password=payload.current_password, new_password=payload.new_password
    )


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    out = UserOut.model_validate(user)
    out.role_name = user.role.name if user.role else None
    return out
