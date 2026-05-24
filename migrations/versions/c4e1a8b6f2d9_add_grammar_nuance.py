"""Grammar: nuance-Feld (kuratierte Nuance-/Verwechslungs-/Formalitätsnotiz)

Revision ID: c4e1a8b6f2d9
Revises: 0a95e22ba15a
Create Date: 2026-05-24 21:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4e1a8b6f2d9'
down_revision = '0a95e22ba15a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('grammar', schema=None) as batch_op:
        batch_op.add_column(sa.Column('nuance', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('grammar', schema=None) as batch_op:
        batch_op.drop_column('nuance')
