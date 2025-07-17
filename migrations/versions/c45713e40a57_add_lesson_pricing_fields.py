"""add_lesson_pricing_fields

Revision ID: c45713e40a57
Revises: a462f46557fe
Create Date: 2025-07-17 16:46:35.859374

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c45713e40a57'
down_revision = 'a462f46557fe'
branch_labels = None
depends_on = None


def upgrade():
    # Add pricing fields to lesson table
    with op.batch_alter_table('lesson', schema=None) as batch_op:
        batch_op.add_column(sa.Column('price', sa.Float(), nullable=False, server_default='0.0'))
        batch_op.add_column(sa.Column('is_purchasable', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    # Remove pricing fields from lesson table
    with op.batch_alter_table('lesson', schema=None) as batch_op:
        batch_op.drop_column('is_purchasable')
        batch_op.drop_column('price')
