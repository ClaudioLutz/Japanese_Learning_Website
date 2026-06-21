"""Kana-Schreibspiel: kana_spell_score

Drittes Kana-Spiel auf /practice/kana (Zuordnung + Storm + Schreiben). Speichert
eine beendete Runde des eingeloggten Spielers (eigenstaendige, leichte Wertung
nach dem KanaStormScore-Muster — KEIN FSRS-Eingriff). Gaeste bleiben rein
clientseitig (localStorage).

STRIKT ADDITIV: legt nur eine neue Tabelle an, ruehrt keine bestehende an.
Sicher beim automatischen `flask db upgrade` im Prod-Container-Entrypoint.

Revision ID: kana_spell_score
Revises: content_issue_tables
Create Date: 2026-06-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'kana_spell_score'
down_revision = 'content_issue_tables'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'kana_spell_score',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('schrift', sa.String(length=16), server_default='hiragana', nullable=False),
        sa.Column('source', sa.String(length=16), server_default='all', nullable=False),
        sa.Column('cue', sa.String(length=16), server_default='bedeutung', nullable=False),
        sa.Column('score', sa.Integer(), server_default='0', nullable=False),
        sa.Column('best_streak', sa.Integer(), server_default='0', nullable=False),
        sa.Column('correct_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('miss_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('xp_awarded', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_kana_spell_score_user_id', 'kana_spell_score', ['user_id'])
    op.create_index('ix_kana_spell_score_created_at', 'kana_spell_score', ['created_at'])


def downgrade():
    op.drop_index('ix_kana_spell_score_created_at', table_name='kana_spell_score')
    op.drop_index('ix_kana_spell_score_user_id', table_name='kana_spell_score')
    op.drop_table('kana_spell_score')
