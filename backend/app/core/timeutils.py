"""SQLite (used for tests / lightweight dev) silently drops tzinfo on
round-trip even for DateTime(timezone=True) columns — Postgres doesn't have
this problem. `aware()` re-attaches UTC so comparisons against
datetime.now(timezone.utc) never raise "can't compare offset-naive and
offset-aware datetimes"."""
from datetime import datetime, timezone


def aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
