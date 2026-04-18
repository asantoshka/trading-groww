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
    op.add_column(
        "positions",
        sa.Column("action", sa.String(length=10), nullable=True, server_default="BUY"),
    )


def downgrade() -> None:
    op.drop_column("positions", "action")
