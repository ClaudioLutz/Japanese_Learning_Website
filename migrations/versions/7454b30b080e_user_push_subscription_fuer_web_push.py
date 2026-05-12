"""User.push_subscription fuer Web Push

Revision ID: 7454b30b080e
Revises: b71dba04fbd4
Create Date: 2026-05-12 21:52:38.240033

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7454b30b080e'
down_revision = 'b71dba04fbd4'
branch_labels = None
depends_on = None


def upgrade():
    # Hinweis: Auto-Detect "drop_index ix_lesson_category_jlpt_order" wurde
    # bewusst entfernt (false positive, siehe vorherige Migration).
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('push_subscription', sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('push_subscription')
