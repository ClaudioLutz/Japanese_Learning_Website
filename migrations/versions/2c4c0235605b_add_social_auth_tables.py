"""add_social_auth_tables

Revision ID: 2c4c0235605b
Revises: f518706fd7a4
Create Date: 2025-07-18 20:58:57.591475

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2c4c0235605b'
down_revision = 'f518706fd7a4'
branch_labels = None
depends_on = None


def upgrade():
    # Create social_auth_association table
    op.create_table('social_auth_association',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('server_url', sa.String(255), nullable=False),
        sa.Column('handle', sa.String(255), nullable=False),
        sa.Column('secret', sa.String(255), nullable=False),
        sa.Column('issued', sa.Integer(), nullable=False),
        sa.Column('lifetime', sa.Integer(), nullable=False),
        sa.Column('assoc_type', sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('server_url', 'handle')
    )

    # Create social_auth_code table
    op.create_table('social_auth_code',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(254), nullable=False),
        sa.Column('code', sa.String(32), nullable=False),
        sa.Column('verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', 'code')
    )

    # Create social_auth_nonce table
    op.create_table('social_auth_nonce',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('server_url', sa.String(255), nullable=False),
        sa.Column('timestamp', sa.Integer(), nullable=False),
        sa.Column('salt', sa.String(65), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('server_url', 'timestamp', 'salt')
    )

    # Create social_auth_usersocialauth table
    op.create_table('social_auth_usersocialauth',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(32), nullable=False),
        sa.Column('uid', sa.String(255), nullable=False),
        sa.Column('extra_data', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'uid')
    )

    # Create indexes
    op.create_index('social_auth_usersocialauth_user_id', 'social_auth_usersocialauth', ['user_id'])


def downgrade():
    # Drop indexes
    op.drop_index('social_auth_usersocialauth_user_id', table_name='social_auth_usersocialauth')
    
    # Drop tables
    op.drop_table('social_auth_usersocialauth')
    op.drop_table('social_auth_nonce')
    op.drop_table('social_auth_code')
    op.drop_table('social_auth_association')
