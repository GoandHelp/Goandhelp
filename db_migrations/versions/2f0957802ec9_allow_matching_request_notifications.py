"""allow_matching_request_notifications

Revision ID: 2f0957802ec9
Revises: 4605dad19900
"""
from typing import Sequence, Union

from alembic import op

revision: str = '2f0957802ec9'
down_revision: Union[str, Sequence[str], None] = '4605dad19900'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE skillkind_member_notification DROP CONSTRAINT IF EXISTS ck_member_notification_kind;\nALTER TABLE skillkind_member_notification ADD CONSTRAINT ck_member_notification_kind CHECK (kind IN ('community_like','community_reply','inbox_message','help_offer','help_confirmed','schedule_proposed','schedule_confirmed','schedule_declined','direct_help_request','request_accepted','request_declined','job_expired','job_renewed','cancellation_proposed','cancellation_accepted','cancellation_declined','no_show_reported','requests_in_my_field'))")


def downgrade() -> None:
    pass
