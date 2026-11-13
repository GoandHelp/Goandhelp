"""allow_schedule_notification_kinds

Revision ID: 55d7ddcce6d4
Revises: 7f86187048c7
"""
from typing import Sequence, Union

from alembic import op

revision: str = '55d7ddcce6d4'
down_revision: Union[str, Sequence[str], None] = '7f86187048c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE skillkind_member_notification DROP CONSTRAINT IF EXISTS ck_member_notification_kind;\nALTER TABLE skillkind_member_notification ADD CONSTRAINT ck_member_notification_kind CHECK (kind IN ('community_like', 'community_reply', 'inbox_message', 'help_offer', 'help_confirmed', 'schedule_proposed', 'schedule_confirmed', 'schedule_declined'));")


def downgrade() -> None:
    pass
