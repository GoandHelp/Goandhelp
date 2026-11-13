"""Add_secure_location_modes

Revision ID: 4fb3214bb218
Revises: eb90329d233e
"""
from typing import Sequence, Union

from alembic import op

revision: str = '4fb3214bb218'
down_revision: Union[str, Sequence[str], None] = 'eb90329d233e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE skillkind_profile SET location_mode = 'approximate' WHERE location_mode = 'fixed';")


def downgrade() -> None:
    pass
