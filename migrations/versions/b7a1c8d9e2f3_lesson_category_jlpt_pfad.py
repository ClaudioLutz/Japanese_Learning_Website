"""LessonCategory: JLPT-Pfad-Felder (slug, jlpt_level, display_order, icon, prereq)

Revision ID: b7a1c8d9e2f3
Revises: rename_postfinance_to_provider
Create Date: 2026-04-25

Mayuko-Direktive 2026-04-25: Lektionen werden in JLPT-strukturierte Module
gruppiert. LessonCategory wird als Modul-Container erweitert.
"""
from alembic import op
import sqlalchemy as sa


revision = 'b7a1c8d9e2f3'
down_revision = 'a3f5c2d1b8e9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('lesson_category') as batch:
        batch.add_column(sa.Column('slug', sa.String(length=80), nullable=True))
        batch.add_column(sa.Column('jlpt_level', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('display_order', sa.Integer(),
                                   nullable=False, server_default='0'))
        batch.add_column(sa.Column('icon_emoji', sa.String(length=8), nullable=True))
        batch.add_column(sa.Column('prerequisite_category_id', sa.Integer(),
                                   nullable=True))
        batch.create_unique_constraint('uq_lesson_category_slug', ['slug'])
        batch.create_foreign_key(
            'fk_lesson_category_prereq',
            'lesson_category',
            ['prerequisite_category_id'], ['id'],
        )
        batch.create_index('ix_lesson_category_jlpt_order',
                           ['jlpt_level', 'display_order'])


def downgrade():
    with op.batch_alter_table('lesson_category') as batch:
        batch.drop_index('ix_lesson_category_jlpt_order')
        batch.drop_constraint('fk_lesson_category_prereq', type_='foreignkey')
        batch.drop_constraint('uq_lesson_category_slug', type_='unique')
        batch.drop_column('prerequisite_category_id')
        batch.drop_column('icon_emoji')
        batch.drop_column('display_order')
        batch.drop_column('jlpt_level')
        batch.drop_column('slug')
