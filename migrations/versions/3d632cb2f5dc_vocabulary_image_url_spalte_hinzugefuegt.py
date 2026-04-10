"""Vocabulary: image_url Spalte hinzugefuegt

Revision ID: 3d632cb2f5dc
Revises: 10965ba77375
Create Date: 2026-04-10 20:16:00.418370

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3d632cb2f5dc'
down_revision = '10965ba77375'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('vocabulary', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_url', sa.String(length=500), nullable=True))


def downgrade():
    with op.batch_alter_table('vocabulary', schema=None) as batch_op:
        batch_op.drop_column('image_url')
