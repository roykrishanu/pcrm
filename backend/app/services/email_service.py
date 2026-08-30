"""Email sending abstraction (section 27 — provider-agnostic). Dev default
logs to console; set EMAIL_BACKEND=smtp + SMTP_* env vars for real delivery.
Never blocks the request — call this from a background task in production."""
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger("app.email")
settings = get_settings()


def send_email(*, to: str, subject: str, body: str) -> None:
    if settings.EMAIL_BACKEND == "smtp" and settings.SMTP_HOST:
        msg = EmailMessage()
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD or "")
            server.send_message(msg)
        return

    logger.info("email.console", extra={"to": to, "subject": subject, "body": body})


def send_verification_email(*, to: str, token: str) -> None:
    link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    send_email(to=to, subject="Verify your email", body=f"Verify your account: {link}")


def send_password_reset_email(*, to: str, token: str) -> None:
    link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    send_email(to=to, subject="Reset your password", body=f"Reset your password: {link}")


def send_invite_email(*, to: str, token: str, org_name: str) -> None:
    link = f"{settings.FRONTEND_URL}/accept-invite?token={token}"
    send_email(to=to, subject=f"You've been invited to {org_name}", body=f"Accept your invite: {link}")
