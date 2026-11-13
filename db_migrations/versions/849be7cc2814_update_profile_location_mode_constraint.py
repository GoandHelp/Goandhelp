"""update_profile_location_mode_constraint

Revision ID: 849be7cc2814
Revises: 300f7f902a78
"""
from typing import Sequence, Union

from alembic import op

revision: str = '849be7cc2814'
down_revision: Union[str, Sequence[str], None] = '300f7f902a78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE skillkind_profile DROP CONSTRAINT IF EXISTS ck_profile_location_mode; ALTER TABLE skillkind_profile ADD CONSTRAINT ck_profile_location_mode CHECK (location_mode IN ('hidden', 'approximate', 'live'));")


def downgrade() -> None:
    pass
