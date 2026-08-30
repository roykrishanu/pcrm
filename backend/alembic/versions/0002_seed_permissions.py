"""seed permission catalog

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-30
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.core.permissions import PERMISSION_CATALOG

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

permissions_table = sa.table(
    "permissions",
    sa.column("key", sa.String),
    sa.column("description", sa.String),
    sa.column("category", sa.String),
)


def upgrade() -> None:
    op.bulk_insert(
        permissions_table,
        [{"key": key, "description": description, "category": category}
         for key, description, category in PERMISSION_CATALOG],
    )


def downgrade() -> None:
    op.execute(permissions_table.delete())
