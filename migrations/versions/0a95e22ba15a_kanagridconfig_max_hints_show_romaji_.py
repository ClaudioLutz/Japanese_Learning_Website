"""KanaGridConfig: max_hints + show_romaji_hint_on_pool

Revision ID: 0a95e22ba15a
Revises: 7454b30b080e
Create Date: 2026-05-12 22:30:52.149062

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0a95e22ba15a'
down_revision = '7454b30b080e'
branch_labels = None
depends_on = None


def upgrade():
    # Hinweis: drop_index ix_lesson_category_jlpt_order ist alembic false positive
    # (Index existiert produktiv, Model definiert ihn nicht explizit). Entfernt.
    with op.batch_alter_table('kana_grid_config', schema=None) as batch_op:
        batch_op.add_column(sa.Column('max_hints', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('show_romaji_hint_on_pool', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade():
    with op.batch_alter_table('kana_grid_config', schema=None) as batch_op:
        batch_op.drop_column('show_romaji_hint_on_pool')
        batch_op.drop_column('max_hints')
