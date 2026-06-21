"""Content-Issue-Tabellen: content_issue, content_issue_comment

Oeffentlich lesbares, content-verankertes Hinweis-/Feedback-Board ("Issues").
Lesen ist oeffentlich, Schreiben braucht ein Konto. Status open/resolved,
Maintainer beantwortet + setzt erledigt. Soft-Delete ueberall.

STRIKT ADDITIV: legt nur neue Tabellen an, ruehrt keine bestehende Tabelle an.
Sicher beim automatischen `flask db upgrade` im Prod-Container-Entrypoint.

Revision ID: content_issue_tables
Revises: vocab_direction_srs
Create Date: 2026-06-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'content_issue_tables'
down_revision = 'vocab_direction_srs'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'content_issue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.String(length=20), nullable=True),
        sa.Column('content_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='open', nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by_id', sa.Integer(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['user.id']),
        sa.ForeignKeyConstraint(['resolved_by_id'], ['user.id']),
        sa.ForeignKeyConstraint(['deleted_by_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_content_issue_author_id', 'content_issue', ['author_id'])
    op.create_index('ix_content_issue_status_created', 'content_issue', ['status', 'created_at'])
    op.create_index('ix_content_issue_content', 'content_issue', ['content_type', 'content_id'])

    op.create_table(
        'content_issue_comment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('issue_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('is_maintainer_reply', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('edited_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['issue_id'], ['content_issue.id']),
        sa.ForeignKeyConstraint(['author_id'], ['user.id']),
        sa.ForeignKeyConstraint(['deleted_by_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_content_issue_comment_author_id', 'content_issue_comment', ['author_id'])
    op.create_index(
        'ix_content_issue_comment_issue_created',
        'content_issue_comment', ['issue_id', 'created_at'],
    )


def downgrade():
    op.drop_index('ix_content_issue_comment_issue_created', table_name='content_issue_comment')
    op.drop_index('ix_content_issue_comment_author_id', table_name='content_issue_comment')
    op.drop_table('content_issue_comment')
    op.drop_index('ix_content_issue_content', table_name='content_issue')
    op.drop_index('ix_content_issue_status_created', table_name='content_issue')
    op.drop_index('ix_content_issue_author_id', table_name='content_issue')
    op.drop_table('content_issue')
