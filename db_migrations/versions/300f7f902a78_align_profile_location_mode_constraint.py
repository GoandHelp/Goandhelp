"""align_profile_location_mode_constraint

Revision ID: 300f7f902a78
Revises: 26b16d5e2b0b
"""
from typing import Sequence, Union

from alembic import op

revision: str = '300f7f902a78'
down_revision: Union[str, Sequence[str], None] = '26b16d5e2b0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE skillkind_profile SET location_mode = 'approximate' WHERE location_mode = 'fixed';")


def downgrade() -> None:
    pass
