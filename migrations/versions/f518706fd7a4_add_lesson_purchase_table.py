"""add_lesson_purchase_table

Revision ID: f518706fd7a4
Revises: c45713e40a57
Create Date: 2025-07-17 16:50:06.109455

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f518706fd7a4'
down_revision = 'c45713e40a57'
branch_labels = None
depends_on = None


def upgrade():
    # Create lesson_purchase table
    op.create_table('lesson_purchase',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('price_paid', sa.Float(), nullable=False),
        sa.Column('purchased_at', sa.DateTime(), nullable=False),
        sa.Column('stripe_payment_intent_id', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['lesson_id'], ['lesson.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'lesson_id')
    )


def downgrade():
    # Drop lesson_purchase table
    op.drop_table('lesson_purchase')
