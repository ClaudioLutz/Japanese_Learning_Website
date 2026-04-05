"""Rename postfinance_transaction_id to provider_transaction_id

Generisch umbenennen, da Payrexx nun als Payment-Provider verwendet wird.

Revision ID: rename_postfinance_to_provider
Revises: 2cf5935d183f
Create Date: 2026-04-05
"""
from alembic import op
import sqlalchemy as sa

revision = 'rename_postfinance_to_provider'
down_revision = '2cf5935d183f'
branch_labels = None
depends_on = None


def upgrade():
    # Lesson Purchase: Spalte umbenennen
    with op.batch_alter_table('lesson_purchase', schema=None) as batch_op:
        batch_op.alter_column(
            'postfinance_transaction_id',
            new_column_name='provider_transaction_id',
            existing_type=sa.BigInteger(),
            existing_nullable=True,
        )

    # Course Purchase: Spalte umbenennen
    with op.batch_alter_table('course_purchase', schema=None) as batch_op:
        batch_op.alter_column(
            'postfinance_transaction_id',
            new_column_name='provider_transaction_id',
            existing_type=sa.BigInteger(),
            existing_nullable=True,
        )


def downgrade():
    with op.batch_alter_table('lesson_purchase', schema=None) as batch_op:
        batch_op.alter_column(
            'provider_transaction_id',
            new_column_name='postfinance_transaction_id',
            existing_type=sa.BigInteger(),
            existing_nullable=True,
        )

    with op.batch_alter_table('course_purchase', schema=None) as batch_op:
        batch_op.alter_column(
            'provider_transaction_id',
            new_column_name='postfinance_transaction_id',
            existing_type=sa.BigInteger(),
            existing_nullable=True,
        )
