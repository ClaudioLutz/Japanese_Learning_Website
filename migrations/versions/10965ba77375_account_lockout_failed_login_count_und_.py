"""Account Lockout: failed_login_count und locked_until

Revision ID: 10965ba77375
Revises: rename_postfinance_to_provider
Create Date: 2026-04-10 18:31:09.620219

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '10965ba77375'
down_revision = 'rename_postfinance_to_provider'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('failed_login_count', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('locked_until', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('locked_until')
        batch_op.drop_column('failed_login_count')
