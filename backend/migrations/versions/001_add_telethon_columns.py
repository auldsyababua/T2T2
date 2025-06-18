"""Add Telethon session columns to users table

Revision ID: 001_add_telethon_columns
Revises: 
Create Date: 2024-01-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_telethon_columns'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add columns for Telethon phone authentication"""
    # Add new columns
    op.add_column('users', sa.Column('phone_number', sa.String(20), unique=True))
    op.add_column('users', sa.Column('session_string', sa.Text()))  # Encrypted
    op.add_column('users', sa.Column('session_created_at', sa.DateTime()))
    op.add_column('users', sa.Column('last_auth_at', sa.DateTime()))
    
    # Create index on phone_number for faster lookups
    op.create_index('ix_users_phone_number', 'users', ['phone_number'])
    
    # Note: session_file column will be removed in a later migration after data migration


def downgrade():
    """Remove Telethon session columns"""
    op.drop_index('ix_users_phone_number', 'users')
    op.drop_column('users', 'last_auth_at')
    op.drop_column('users', 'session_created_at')
    op.drop_column('users', 'session_string')
    op.drop_column('users', 'phone_number')