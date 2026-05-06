"""Initial migration for Supabase

Revision ID: 001_initial
Revises:
Create Date: 2026-05-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)

    # Create user_settings table
    op.create_table(
        'user_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('user_name', sa.String(), nullable=True),
        sa.Column('user_bank_account', sa.String(), nullable=True),
        sa.Column('preferred_currency', sa.String(), nullable=True),
        sa.Column('timezone', sa.String(), nullable=True),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('theme', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )

    # Create income_categories table
    op.create_table(
        'income_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('icon', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_income_categories_name', 'income_categories', ['name'], unique=True)

    # Create receipts table
    op.create_table(
        'receipts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('image_path', sa.String(), nullable=True),
        sa.Column('ocr_raw_text', sa.Text(), nullable=True),
        sa.Column('extracted_date', sa.Date(), nullable=True),
        sa.Column('extracted_time', sa.String(), nullable=True),
        sa.Column('sender', sa.String(), nullable=True),
        sa.Column('receiver', sa.String(), nullable=True),
        sa.Column('amount', sa.Numeric(), nullable=True),
        sa.Column('note', sa.String(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('transaction_type', sa.String(), nullable=True),
        sa.Column('transaction_confidence', sa.String(), nullable=True),
        sa.Column('classification_reason', sa.String(), nullable=True),
        sa.Column('is_salary', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_manual_income', sa.Boolean(), nullable=True, default=False),
        sa.Column('income_category', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )
    op.create_index('ix_receipts_id', 'receipts', ['id'], unique=False)
    op.create_index('ix_receipts_user_id', 'receipts', ['user_id'], unique=False)


def downgrade():
    op.drop_index('ix_receipts_user_id', table_name='receipts')
    op.drop_index('ix_receipts_id', table_name='receipts')
    op.drop_table('receipts')

    op.drop_index('ix_income_categories_name', table_name='income_categories')
    op.drop_table('income_categories')

    op.drop_table('user_settings')

    op.drop_index('ix_users_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')