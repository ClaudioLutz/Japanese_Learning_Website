"""Vocabulary: romaji Feld hinzugefuegt

Revision ID: a3f5c2d1b8e9
Revises: c866cbc1bf97
Create Date: 2026-04-24 20:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a3f5c2d1b8e9'
down_revision = '6730297e0374'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('vocabulary', schema=None) as batch_op:
        batch_op.add_column(sa.Column('romaji', sa.String(length=200), nullable=True))


def downgrade():
    with op.batch_alter_table('vocabulary', schema=None) as batch_op:
        batch_op.drop_column('romaji')
