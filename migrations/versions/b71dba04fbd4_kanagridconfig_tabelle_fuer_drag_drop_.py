"""KanaGridConfig-Tabelle fuer Drag-Drop-Spiel

Revision ID: b71dba04fbd4
Revises: add_kana_mnemonic_column
Create Date: 2026-05-12 21:31:23.904542

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b71dba04fbd4'
down_revision = 'add_kana_mnemonic_column'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'kana_grid_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lesson_content_id', sa.Integer(), nullable=False),
        sa.Column('kana_ids', sa.JSON(), nullable=False),
        sa.Column('default_mode', sa.String(length=20), server_default='schreiben', nullable=False),
        sa.Column('allow_mode_switch', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('grid_layout', sa.String(length=20), server_default='rows', nullable=False),
        sa.Column('shuffle_pool', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('timer_enabled', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['lesson_content_id'], ['lesson_content.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lesson_content_id'),
    )
    # Hinweis: Alembic hat faelschlich "drop_index ix_lesson_category_jlpt_order"
    # vorgeschlagen — false positive (Index existiert produktiv, Model definiert
    # ihn nur nicht explizit). Wurde entfernt.


def downgrade():
    op.drop_table('kana_grid_config')
