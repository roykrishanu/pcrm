"""Import every model module here so `Base.metadata` is complete for Alembic
autogenerate and for `create_all` in tests."""
from app.models.organization import Organization  # noqa: F401
from app.models.rbac import Permission, Role, Team, role_permissions  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.auth_tokens import OneTimeToken, Session  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.lead import Lead, LeadActivity, LeadStatus  # noqa: F401
