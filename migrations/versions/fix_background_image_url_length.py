"""Fix background_image_url length

Revision ID: fix_background_image_url_length
Revises: 2c4c0235605b
Create Date: 2025-07-18 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_background_image_url_length'
down_revision = '2c4c0235605b'
branch_labels = None
depends_on = None


def upgrade():
    # Increase the length of background_image_url from VARCHAR(255) to VARCHAR(1000)
    op.alter_column('lesson', 'background_image_url',
                    existing_type=sa.VARCHAR(length=255),
                    type_=sa.VARCHAR(length=1000),
                    existing_nullable=True)


def downgrade():
    # Revert back to VARCHAR(255)
    op.alter_column('lesson', 'background_image_url',
                    existing_type=sa.VARCHAR(length=1000),
                    type_=sa.VARCHAR(length=255),
                    existing_nullable=True)
