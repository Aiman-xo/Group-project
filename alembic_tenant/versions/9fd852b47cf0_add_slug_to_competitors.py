"""add slug to competitors

Revision ID: 9fd852b47cf0
Revises: 6cd950b2b692
Create Date: 2026-07-07 13:15:43.871005

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9fd852b47cf0'
down_revision: Union[str, Sequence[str], None] = '6cd950b2b692'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add slug column to the already-existing competitors table in each tenant schema
    op.add_column('competitors', sa.Column('slug', sa.String(), nullable=True))
    op.create_unique_constraint('uq_competitors_slug', 'competitors', ['slug'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_competitors_slug', 'competitors', type_='unique')
    op.drop_column('competitors', 'slug')
