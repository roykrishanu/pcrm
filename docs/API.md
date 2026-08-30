# API

Base path: `/api/v1`. Interactive docs at `/docs` (disabled when `ENV=production`).
All responses are JSON. Errors follow:

```json
{"error": {"code": "LEAD_NOT_FOUND", "message": "Lead could not be found.", "request_id": "..."}}
```

Auth: `Authorization: Bearer <access_token>` header on every protected route.

## Auth (`/auth`)

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/register-organization` | none | Creates org + owner user + default roles/statuses. Sends verification email. |
| POST | `/login` | none | Body: `email`, `password`, optional `organization_slug` (needed if the same email exists in >1 org). Rate-limited, lockout after 5 failures. |
| POST | `/refresh` | none (refresh token) | Rotates the refresh token. |
| POST | `/logout` | bearer | Revokes one session (pass its refresh token). |
| POST | `/logout-all` | bearer | Revokes every session for the user. |
| GET | `/sessions` | bearer | List active devices/sessions. |
| POST | `/password-reset/request` | none | Always 202, never reveals whether the email exists. |
| POST | `/password-reset/confirm` | none | Consumes token, revokes all sessions. |
| POST | `/verify-email` | none | Consumes token. |
| POST | `/change-password` | bearer | Requires current password, revokes all sessions. |
| GET | `/me` | bearer | Current user + role name. |

## Leads (`/leads`)

All require bearer auth + the listed permission.

| Method | Path | Permission | Notes |
|---|---|---|---|
| POST | `` | `leads.create` | |
| GET | `` | `leads.read` | Query: `page`, `page_size`, `status_key`, `assigned_user_id`, `search`. Returns `Page[LeadOut]`. |
| GET | `/{lead_id}` | `leads.read` | 404 if not found OR belongs to another org. |
| PATCH | `/{lead_id}` | `leads.update` | Partial update. |
| POST | `/{lead_id}/status` | `leads.update` | Moves the lead to a different pipeline stage; logs a `status_change` activity. |
| DELETE | `/{lead_id}` | `leads.delete` | Soft delete. |
| GET | `/{lead_id}/activities` | `leads.read` | Timeline, newest first. |
| POST | `/{lead_id}/activities` | `leads.update` | Logs an activity; applies the scoring delta for its `type` if one is configured. |

## Ops

`GET /health` — liveness, no dependencies checked. `GET /ready` — checks DB
connectivity, returns 503 if the DB is unreachable.

## Not yet implemented

Users/teams/roles management endpoints, properties, visits, deals,
customers, owners, developers, documents, reports, webhooks, automation,
search, import/export. See `PROJECT_STATUS.md` for the ordered backlog.
