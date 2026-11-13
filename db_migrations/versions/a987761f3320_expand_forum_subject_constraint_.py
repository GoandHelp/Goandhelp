"""expand_forum_subject_constraint_activities_money

Revision ID: a987761f3320
Revises: 06433dcc86e2
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'a987761f3320'
down_revision: Union[str, Sequence[str], None] = '06433dcc86e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE skillkind_community_topic DROP CONSTRAINT ck_community_topic_subject_category;\nALTER TABLE skillkind_community_topic ADD CONSTRAINT ck_community_topic_subject_category CHECK (subject_category IN ('First time Helper', 'First time Helpee', 'Communication', 'Privacy', 'Emergencies', 'Events', 'Activities', 'Job management', 'Health and Safety', 'Regulations', 'Work visas', 'Meeting people', 'Businesses', 'Money', 'Workshops', 'Tours', 'Dinner', 'Other'));")


def downgrade() -> None:
    pass
