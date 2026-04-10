"""Streak und XP Felder zum User-Model hinzugefuegt

Revision ID: 98255162a434
Revises: 3d632cb2f5dc
Create Date: 2026-04-10 20:54:47.070679

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '98255162a434'
down_revision = '3d632cb2f5dc'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('current_streak', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('longest_streak', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('last_activity_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('total_xp', sa.Integer(), server_default='0', nullable=False))


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('total_xp')
        batch_op.drop_column('last_activity_date')
        batch_op.drop_column('longest_streak')
        batch_op.drop_column('current_streak')
