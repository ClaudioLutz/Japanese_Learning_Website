"""grammar.tts_example_jp Spalte fuer einen JP-Satz pro Karte

Revision ID: e7f010257f79
Revises: e9a2b4c8d3f1
Create Date: 2026-04-30 21:24:46.094822

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e7f010257f79'
down_revision = 'e9a2b4c8d3f1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('grammar', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tts_example_jp', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('grammar', schema=None) as batch_op:
        batch_op.drop_column('tts_example_jp')
