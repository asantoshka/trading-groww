"""add action to positions

Revision ID: b1c2d3e4f5a6
Revises: a3fe543fdb6f
Create Date: 2026-04-18 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "a3fe543fdb6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use raw connection to inspect existing columns — safe on both fresh
    # installs (where initial migration already created positions with action)
    # and existing EC2 databases (where positions was created via create_all
    # without the action column).
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    tables = inspector.get_table_names()
    if "positions" not in tables:
        # Should not happen (initial migration creates it), but guard anyway.
        return

    existing_columns = [col["name"] for col in inspector.get_columns("positions")]
    if "action" not in existing_columns:
        op.add_column(
            "positions",
            sa.Column("action", sa.String(length=10), nullable=True, server_default="BUY"),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col["name"] for col in inspector.get_columns("positions")]
    if "action" in existing_columns:
        op.drop_column("positions", "action")
