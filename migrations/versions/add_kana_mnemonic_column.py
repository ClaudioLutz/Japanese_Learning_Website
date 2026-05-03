"""Kana: mnemonic-Spalte fuer Merkhilfen (Tofugu-Stil, deutsche Lautanker)

Revision ID: add_kana_mnemonic_column
Revises: e7f010257f79
Create Date: 2026-05-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_kana_mnemonic_column'
down_revision = 'e7f010257f79'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('kana', sa.Column('mnemonic', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('kana', 'mnemonic')
