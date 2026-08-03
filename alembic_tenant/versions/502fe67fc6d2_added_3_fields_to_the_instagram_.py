"""added 3 fields to the instagram comparison model

Revision ID: 502fe67fc6d2
Revises: 68e1fb206435
Create Date: 2026-07-31 20:28:55.256222

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '502fe67fc6d2'
down_revision: Union[str, Sequence[str], None] = '68e1fb206435'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('instagram_comparison_reports', sa.Column('summary', sa.Text(), nullable=True))
    op.add_column('instagram_comparison_reports', sa.Column('posting_cadence_gap', sa.Text(), nullable=True))
    op.add_column('instagram_comparison_reports', sa.Column('content_recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('instagram_comparison_reports', 'content_recommendations')
    op.drop_column('instagram_comparison_reports', 'posting_cadence_gap')
    op.drop_column('instagram_comparison_reports', 'summary')
    # ### end Alembic commands ###
