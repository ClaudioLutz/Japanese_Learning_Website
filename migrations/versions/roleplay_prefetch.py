"""Rollenspiel: Tabelle roleplay_prefetch (vorausberechnete Antworten auf Vorschlaege)

Pro Bot-Zug rechnet der Server die Antwort auf jeden der drei Antwortvorschlaege
vor. Eingeloggt ueber session_id, Gast-Demo ueber demo_key (Token-Hash).

STRIKT ADDITIV: legt nur eine neue Tabelle an.

Revision ID: roleplay_prefetch
Revises: guest_demo_counter
Create Date: 2026-09-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'roleplay_prefetch'
down_revision = 'guest_demo_counter'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'roleplay_prefetch',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('demo_key', sa.String(length=64), nullable=True),
        sa.Column('turn_index', sa.Integer(), nullable=False),
        sa.Column('user_text', sa.Text(), nullable=False),
        sa.Column('norm_text', sa.String(length=400), nullable=False),
        sa.Column('response_json', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=10), nullable=False, server_default='pending'),
        sa.Column('tokens_in', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tokens_out', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cost_usd', sa.Float(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_roleplay_prefetch_session_turn', 'roleplay_prefetch', ['session_id', 'turn_index'])
    op.create_index('ix_roleplay_prefetch_demo_turn', 'roleplay_prefetch', ['demo_key', 'turn_index'])
    op.create_index('ix_roleplay_prefetch_created', 'roleplay_prefetch', ['created_at'])


def downgrade():
    op.drop_index('ix_roleplay_prefetch_created', table_name='roleplay_prefetch')
    op.drop_index('ix_roleplay_prefetch_demo_turn', table_name='roleplay_prefetch')
    op.drop_index('ix_roleplay_prefetch_session_turn', table_name='roleplay_prefetch')
    op.drop_table('roleplay_prefetch')
