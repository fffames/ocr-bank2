"""add_template_and_ocr_engine_fields

Revision ID: 3b81f6ea7015
Revises: a0dfc67fc08c
Create Date: 2026-05-04 02:06:29.135841

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b81f6ea7015'
down_revision: Union[str, None] = 'a0dfc67fc08c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add detected_template column
    op.add_column('receipts',
                  sa.Column('detected_template', sa.String(100), nullable=True)
                  )
    # Add ocr_engine column
    op.add_column('receipts',
                  sa.Column('ocr_engine', sa.String(50), server_default='template', nullable=True)
                  )


def downgrade() -> None:
    # Remove ocr_engine column
    op.drop_column('receipts', 'ocr_engine')
    # Remove detected_template column
    op.drop_column('receipts', 'detected_template')
