"""Add user authentication and multi-user support

Revision ID: 002_add_user_auth
Revises: 3b81f6ea7015
Create Date: 2026-05-05

This migration:
- Creates users table with authentication fields
- Adds user_id foreign key to receipts (with cascade delete)
- Adds user_id foreign key to user_settings (with cascade delete, unique)
- Adds user_id foreign key to chat_history (with cascade delete, nullable)
- Deletes existing receipt data (starting fresh as requested)
- Creates 3 initial user accounts with secure passwords
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from passlib.context import CryptContext

# revision identifiers, used by Alembic.
revision = '002_add_user_auth'
down_revision = '3b81f6ea7015'
branch_labels = None
depends_on = None

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def upgrade() -> None:
    """Create users table and add user_id to existing tables."""

    # 1. Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. Add user_id to receipts table (first, make it nullable to avoid issues with existing data)
    op.add_column('receipts', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_receipts_user_id', 'receipts', 'users', ['user_id'], ['id'], ondelete='CASCADE')

    # 3. Delete all existing receipt data (as requested by user)
    op.execute("DELETE FROM receipts")

    # 4. Now make user_id NOT NULL (since table is empty)
    op.alter_column('receipts', 'user_id', nullable=False)
    op.create_index('ix_receipts_user_id', 'receipts', ['user_id'])

    # 5. Create user_settings table first
    op.create_table(
        'user_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('user_name', sa.String(length=255), nullable=True),
        sa.Column('user_name_variations', sa.Text(), nullable=True),
        sa.Column('auto_classify', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('default_salary_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('salary_day_of_month', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('salary_category', sa.String(length=100), nullable=False, server_default='Salary'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_settings_id', 'user_settings', ['id'])
    op.create_foreign_key('fk_user_settings_user_id', 'user_settings', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_user_settings_user_id', 'user_settings', ['user_id'], unique=True)

    # 8. Add user_id to chat_history table (nullable for backward compatibility)
    op.add_column('chat_history', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_chat_history_user_id', 'chat_history', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_chat_history_user_id', 'chat_history', ['user_id'])

    # 9. Create initial user accounts
    users_table = table(
        'users',
        column('id', sa.Integer),
        column('email', sa.String),
        column('password_hash', sa.String),
        column('name', sa.String),
        column('is_admin', sa.Boolean),
        column('is_active', sa.Boolean)
    )

    # Generate secure passwords
    admin_password_hash = pwd_context.hash("OCR-Bank-Admin-2026!")  # You'll change this
    dad_password_hash = pwd_context.hash("Dad-Budget-2026!")  # You'll change this

    # Insert initial users
    op.bulk_insert(users_table, [
        {
            'id': 1,
            'email': 'admin@ocrbank.local',
            'password_hash': admin_password_hash,
            'name': 'Admin User',
            'is_admin': True,
            'is_active': True
        },
        {
            'id': 2,
            'email': 'dad@ocrbank.local',
            'password_hash': dad_password_hash,
            'name': 'Dad',
            'is_admin': False,
            'is_active': True
        }
    ])

    # 10. Create default user_settings for each user
    user_settings_table = table(
        'user_settings',
        column('id', sa.Integer),
        column('user_id', sa.Integer),
        column('user_name', sa.String),
        column('user_name_variations', sa.String),
        column('auto_classify', sa.Boolean),
        column('default_salary_amount', sa.Numeric),
        column('salary_day_of_month', sa.Integer),
        column('salary_category', sa.String)
    )

    op.bulk_insert(user_settings_table, [
        {
            'id': 1,
            'user_id': 1,
            'user_name': 'Admin User',
            'user_name_variations': '["Admin", "admin"]',
            'auto_classify': True,
            'default_salary_amount': None,
            'salary_day_of_month': 1,
            'salary_category': 'Salary'
        },
        {
            'id': 2,
            'user_id': 2,
            'user_name': 'Dad',
            'user_name_variations': '["Dad", "dad"]',
            'auto_classify': True,
            'default_salary_amount': None,
            'salary_day_of_month': 1,
            'salary_category': 'Salary'
        }
    ])

    print("\n" + "="*80)
    print("✅ USER AUTHENTICATION SUCCESSFULLY INSTALLED")
    print("="*80)
    print("\n👤 INITIAL USER ACCOUNTS CREATED:")
    print("-" * 80)
    print("1. ADMIN ACCOUNT (You):")
    print("   Email: admin@ocrbank.local")
    print("   Password: OCR-Bank-Admin-2026!")
    print("   Role: Admin")
    print("-" * 80)
    print("2. DAD ACCOUNT (Your Dad):")
    print("   Email: dad@ocrbank.local")
    print("   Password: Dad-Budget-2026!")
    print("   Role: User")
    print("-" * 80)
    print("\n⚠️  IMPORTANT: Change these passwords after first login!")
    print("⚠️  These emails are local and won't receive real emails.")
    print("="*80 + "\n")


def downgrade() -> None:
    """Remove user authentication and revert changes."""

    # 1. Drop foreign keys and indexes
    op.drop_index('ix_chat_history_user_id', table_name='chat_history')
    op.drop_constraint('fk_chat_history_user_id', 'chat_history', type_='foreignkey')

    op.drop_index('ix_user_settings_user_id', table_name='user_settings')
    op.drop_constraint('fk_user_settings_user_id', 'user_settings', type_='foreignkey')

    op.drop_index('ix_receipts_user_id', table_name='receipts')
    op.drop_constraint('fk_receipts_user_id', 'receipts', type_='foreignkey')

    # 2. Remove user_id columns
    op.drop_column('chat_history', 'user_id')
    op.drop_column('user_settings', 'user_id')
    op.drop_column('receipts', 'user_id')

    # 3. Drop users table
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_table('users')