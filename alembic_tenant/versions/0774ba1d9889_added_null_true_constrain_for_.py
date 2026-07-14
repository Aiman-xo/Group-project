"""added null=true constrain for competitor analyser source_file field

Revision ID: 0774ba1d9889
Revises: a5439679ce74
Create Date: 2026-07-11 15:11:26.511737

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0774ba1d9889'
down_revision: Union[str, Sequence[str], None] = 'a5439679ce74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('competitor_analyses', 'source_file',
                     existing_type=sa.String(),
                     nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('competitor_analyses', 'source_file',
                     existing_type=sa.String(),
                     nullable=False)
   