"""KanaConfusion-Tabelle: Per-User-Verwechslungssignal fuer den Kana-Drill

Revision ID: kana_confusion_table
Revises: c4e1a8b6f2d9
Create Date: 2026-05-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'kana_confusion_table'
down_revision = 'c4e1a8b6f2d9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'kana_confusion',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('target_kana_id', sa.Integer(), nullable=False),
        sa.Column('confused_kana_id', sa.Integer(), nullable=False),
        sa.Column('count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.ForeignKeyConstraint(['target_kana_id'], ['kana.id']),
        sa.ForeignKeyConstraint(['confused_kana_id'], ['kana.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'user_id', 'target_kana_id', 'confused_kana_id', name='uq_kana_confusion'
        ),
    )
    op.create_index('ix_kana_confusion_user_id', 'kana_confusion', ['user_id'])


def downgrade():
    op.drop_index('ix_kana_confusion_user_id', table_name='kana_confusion')
    op.drop_table('kana_confusion')
