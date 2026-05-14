"""Make image_path nullable

Revision ID: 002
Revises: 001
Create Date: 2025-05-14

This migration allows image_path to be NULL since images are deleted
after receipt confirmation to save storage space.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    """Make image_path column nullable."""
    # Using ALTER TABLE with ALTER COLUMN for PostgreSQL
    op.execute("ALTER TABLE receipts ALTER COLUMN image_path DROP NOT NULL")


def downgrade():
    """Revert: make image_path not nullable again."""
    op.execute("ALTER TABLE receipts ALTER COLUMN image_path SET NOT NULL")
