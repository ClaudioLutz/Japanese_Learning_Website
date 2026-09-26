"""Rollenspiel-Tutor-Tabellen: roleplay_session, roleplay_turn, tutor_question

Rollenspiel am Lektionsdialog (dialog_slideshow) + Tutor „Frag zur Seite".
Laufzeit-Interaktion eines Nutzers, KEIN Lektionsinhalt. Tokens/Kosten pro
Zeile fuer Tageslimits und die globale Kostenkappe.

STRIKT ADDITIV: legt nur neue Tabellen an, ruehrt keine bestehende Tabelle an.
Sicher beim automatischen `flask db upgrade` im Prod-Container-Entrypoint.

Revision ID: roleplay_tutor_tables
Revises: review_log_undo_snapshot
Create Date: 2026-09-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'roleplay_tutor_tables'
down_revision = 'review_log_undo_snapshot'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'roleplay_session',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('lesson_content_id', sa.Integer(), nullable=False),
        sa.Column('role_user', sa.String(length=100), nullable=False),
        sa.Column('role_bot', sa.String(length=100), nullable=False),
        sa.Column('goal_de', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('turn_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('xp_awarded', sa.Integer(), server_default='0', nullable=False),
        sa.Column('model_name', sa.String(length=64), nullable=True),
        sa.Column('tokens_in', sa.Integer(), server_default='0', nullable=False),
        sa.Column('tokens_out', sa.Integer(), server_default='0', nullable=False),
        sa.Column('cost_usd', sa.Float(), server_default='0', nullable=False),
        sa.Column('correction_json', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.ForeignKeyConstraint(['lesson_content_id'], ['lesson_content.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_roleplay_session_lesson_content_id', 'roleplay_session', ['lesson_content_id'])
    op.create_index('ix_roleplay_session_user_started', 'roleplay_session', ['user_id', 'started_at'])
    op.create_index('ix_roleplay_session_started', 'roleplay_session', ['started_at'])

    op.create_table(
        'roleplay_turn',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('turn_index', sa.Integer(), nullable=False),
        sa.Column('speaker', sa.String(length=10), nullable=False),
        sa.Column('text_jp', sa.Text(), nullable=True),
        sa.Column('reading_kana', sa.Text(), nullable=True),
        sa.Column('text_de', sa.Text(), nullable=True),
        sa.Column('suggestions_json', sa.Text(), nullable=True),
        sa.Column('hint_de', sa.Text(), nullable=True),
        sa.Column('raw_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['roleplay_session.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'turn_index', name='uq_roleplay_turn_session_index'),
    )
    op.create_index('ix_roleplay_turn_session_id', 'roleplay_turn', ['session_id'])
    op.create_index('ix_roleplay_turn_speaker_created', 'roleplay_turn', ['speaker', 'created_at'])

    op.create_table(
        'tutor_question',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=True),
        sa.Column('model_name', sa.String(length=64), nullable=True),
        sa.Column('tokens_in', sa.Integer(), server_default='0', nullable=False),
        sa.Column('tokens_out', sa.Integer(), server_default='0', nullable=False),
        sa.Column('cost_usd', sa.Float(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.ForeignKeyConstraint(['lesson_id'], ['lesson.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tutor_question_lesson_id', 'tutor_question', ['lesson_id'])
    op.create_index('ix_tutor_question_user_created', 'tutor_question', ['user_id', 'created_at'])
    op.create_index('ix_tutor_question_created', 'tutor_question', ['created_at'])


def downgrade():
    op.drop_index('ix_tutor_question_created', table_name='tutor_question')
    op.drop_index('ix_tutor_question_user_created', table_name='tutor_question')
    op.drop_index('ix_tutor_question_lesson_id', table_name='tutor_question')
    op.drop_table('tutor_question')
    op.drop_index('ix_roleplay_turn_speaker_created', table_name='roleplay_turn')
    op.drop_index('ix_roleplay_turn_session_id', table_name='roleplay_turn')
    op.drop_table('roleplay_turn')
    op.drop_index('ix_roleplay_session_started', table_name='roleplay_session')
    op.drop_index('ix_roleplay_session_user_started', table_name='roleplay_session')
    op.drop_index('ix_roleplay_session_lesson_content_id', table_name='roleplay_session')
    op.drop_table('roleplay_session')
