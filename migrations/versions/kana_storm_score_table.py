"""KanaStormScore-Tabelle: persoenliche Highscores/Statistik des Kana-Storm-Arcade-Modus

Revision ID: kana_storm_score_table
Revises: kana_confusion_table
Create Date: 2026-06-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'kana_storm_score_table'
down_revision = 'kana_confusion_table'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'kana_storm_score',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('mode', sa.String(length=16), server_default='storm', nullable=False),
        sa.Column('schrift', sa.String(length=16), server_default='hiragana', nullable=False),
        sa.Column('duration', sa.Integer(), server_default='0', nullable=False),
        sa.Column('score', sa.Integer(), server_default='0', nullable=False),
        sa.Column('best_combo', sa.Integer(), server_default='1', nullable=False),
        sa.Column('correct_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('miss_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('xp_awarded', sa.Integer(), server_default='0', nullable=False),
        sa.Column('daily_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_kana_storm_score_user_id', 'kana_storm_score', ['user_id'])
    op.create_index('ix_kana_storm_score_created_at', 'kana_storm_score', ['created_at'])


def downgrade():
    op.drop_index('ix_kana_storm_score_created_at', table_name='kana_storm_score')
    op.drop_index('ix_kana_storm_score_user_id', table_name='kana_storm_score')
    op.drop_table('kana_storm_score')
