"""Forum-Tabellen: forum_category, forum_topic, forum_post

Leichtgewichtiges Benutzer-Forum (login-pflichtig zum Lesen). Kategorie → Topic
→ Post; der erste Post (is_op) ist der Thread-Body. Soft-Delete ueberall.

STRIKT ADDITIV: legt nur neue Tabellen an, ruehrt keine bestehende Tabelle an.
Sicher beim automatischen `flask db upgrade` im Prod-Container-Entrypoint.

Revision ID: forum_tables
Revises: lesson_category_image_url
Create Date: 2026-06-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'forum_tables'
down_revision = 'lesson_category_image_url'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'forum_category',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=80), nullable=False),
        sa.Column('description', sa.String(length=300), nullable=True),
        sa.Column('icon', sa.String(length=40), nullable=True),
        sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('admin_only_post', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )

    op.create_table(
        'forum_topic',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=True),
        sa.Column('is_pinned', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('is_locked', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('view_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('reply_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['forum_category.id']),
        sa.ForeignKeyConstraint(['author_id'], ['user.id']),
        sa.ForeignKeyConstraint(['deleted_by_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_forum_topic_category_id', 'forum_topic', ['category_id'])
    op.create_index('ix_forum_topic_author_id', 'forum_topic', ['author_id'])
    op.create_index('ix_forum_topic_slug', 'forum_topic', ['slug'])
    op.create_index('ix_forum_topic_created_at', 'forum_topic', ['created_at'])
    op.create_index('ix_forum_topic_last_activity_at', 'forum_topic', ['last_activity_at'])

    op.create_table(
        'forum_post',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('is_op', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('edited_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['topic_id'], ['forum_topic.id']),
        sa.ForeignKeyConstraint(['author_id'], ['user.id']),
        sa.ForeignKeyConstraint(['deleted_by_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_forum_post_topic_id', 'forum_post', ['topic_id'])
    op.create_index('ix_forum_post_author_id', 'forum_post', ['author_id'])
    op.create_index('ix_forum_post_created_at', 'forum_post', ['created_at'])


def downgrade():
    op.drop_index('ix_forum_post_created_at', table_name='forum_post')
    op.drop_index('ix_forum_post_author_id', table_name='forum_post')
    op.drop_index('ix_forum_post_topic_id', table_name='forum_post')
    op.drop_table('forum_post')
    op.drop_index('ix_forum_topic_last_activity_at', table_name='forum_topic')
    op.drop_index('ix_forum_topic_created_at', table_name='forum_topic')
    op.drop_index('ix_forum_topic_slug', table_name='forum_topic')
    op.drop_index('ix_forum_topic_author_id', table_name='forum_topic')
    op.drop_index('ix_forum_topic_category_id', table_name='forum_topic')
    op.drop_table('forum_topic')
    op.drop_table('forum_category')
