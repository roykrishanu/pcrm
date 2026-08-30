"""Single source of truth for the permission catalog and default roles.
Add a capability here, then reference it with `Depends(require_permission(...))`
on a route — never hand-roll a role-name check in route code."""

# (key, description, category)
PERMISSION_CATALOG: list[tuple[str, str, str]] = [
    ("leads.create", "Create leads", "leads"),
    ("leads.read", "View leads", "leads"),
    ("leads.update", "Edit leads", "leads"),
    ("leads.delete", "Delete leads", "leads"),
    ("leads.assign", "Assign leads to agents", "leads"),
    ("leads.export", "Export leads", "leads"),
    ("properties.create", "Create properties", "properties"),
    ("properties.read", "View properties", "properties"),
    ("properties.update", "Edit properties", "properties"),
    ("properties.delete", "Delete properties", "properties"),
    ("visits.create", "Schedule visits", "visits"),
    ("visits.update", "Update visits", "visits"),
    ("deals.create", "Create deals", "deals"),
    ("deals.update", "Update deals", "deals"),
    ("reports.read", "View reports", "reports"),
    ("users.create", "Invite/create users", "users"),
    ("users.update", "Edit users", "users"),
    ("users.delete", "Deactivate/delete users", "users"),
    ("settings.manage", "Manage organization settings", "settings"),
    ("audit.read", "View audit logs", "audit"),
]

ALL_PERMISSION_KEYS = [p[0] for p in PERMISSION_CATALOG]

# role_slug -> permission keys. "owner" implicitly gets everything (checked
# in code, not listed here, so new permissions are automatically included).
DEFAULT_ROLES: dict[str, list[str]] = {
    "owner": ALL_PERMISSION_KEYS,
    "admin": ALL_PERMISSION_KEYS,
    "manager": [
        "leads.create", "leads.read", "leads.update", "leads.assign", "leads.export",
        "properties.create", "properties.read", "properties.update",
        "visits.create", "visits.update",
        "deals.create", "deals.update",
        "reports.read", "audit.read",
    ],
    "agent": [
        "leads.create", "leads.read", "leads.update",
        "properties.read",
        "visits.create", "visits.update",
        "deals.create", "deals.update",
    ],
    "sales_executive": [
        "leads.create", "leads.read", "leads.update",
        "properties.read",
        "visits.create", "visits.update",
    ],
    "viewer": [
        "leads.read", "properties.read", "reports.read",
    ],
}

DEFAULT_ROLE_LABELS: dict[str, str] = {
    "owner": "Organization Owner",
    "admin": "Admin",
    "manager": "Manager",
    "agent": "Agent",
    "sales_executive": "Sales Executive",
    "viewer": "Viewer",
}

DEFAULT_LEAD_STATUSES: list[tuple[str, str, bool, bool]] = [
    # (key, label, is_won, is_lost)
    ("new", "New", False, False),
    ("contacted", "Contacted", False, False),
    ("qualified", "Qualified", False, False),
    ("property_suggested", "Property Suggested", False, False),
    ("interested", "Interested", False, False),
    ("site_visit_scheduled", "Site Visit Scheduled", False, False),
    ("site_visit_completed", "Site Visit Completed", False, False),
    ("negotiation", "Negotiation", False, False),
    ("booking", "Booking", False, False),
    ("won", "Won", True, False),
    ("lost", "Lost", False, True),
    ("nurture", "Nurture", False, False),
]
