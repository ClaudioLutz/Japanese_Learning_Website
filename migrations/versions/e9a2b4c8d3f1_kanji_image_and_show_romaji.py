"""Add kanji.image_url and lesson.show_romaji_on_front

Revision ID: e9a2b4c8d3f1
Revises: d8e2c1a4f6b3
Create Date: 2026-04-28
"""
from alembic import op
import sqlalchemy as sa


revision = 'e9a2b4c8d3f1'
down_revision = 'd8e2c1a4f6b3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('kanji') as batch_op:
        batch_op.add_column(sa.Column('image_url', sa.String(length=500), nullable=True))

    with op.batch_alter_table('lesson') as batch_op:
        batch_op.add_column(
            sa.Column(
                'show_romaji_on_front',
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )


def downgrade():
    with op.batch_alter_table('lesson') as batch_op:
        batch_op.drop_column('show_romaji_on_front')

    with op.batch_alter_table('kanji') as batch_op:
        batch_op.drop_column('image_url')
