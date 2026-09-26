"""Gast-Demo des Rollenspiels: Tageszaehler guest_demo_counter

Pro CH-Kalendertag und gehashter Client-IP ein Zaehler der Gast-Zuege
(ip_hash '*' = globale Tageskappe). Ueber alle Gunicorn-Worker konsistent.

STRIKT ADDITIV: legt nur eine neue Tabelle an.

Revision ID: guest_demo_counter
Revises: roleplay_tutor_tables
Create Date: 2026-09-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'guest_demo_counter'
down_revision = 'roleplay_tutor_tables'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'guest_demo_counter',
        sa.Column('day', sa.Date(), nullable=False),
        sa.Column('ip_hash', sa.String(length=64), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('day', 'ip_hash'),
    )


def downgrade():
    op.drop_table('guest_demo_counter')
