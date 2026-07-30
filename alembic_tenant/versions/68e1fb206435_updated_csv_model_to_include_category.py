"""updated csv model to include category

Revision ID: 68e1fb206435
Revises: 8c176638e7f7
Create Date: 2026-07-28 21:38:13.519800

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '68e1fb206435'
down_revision: Union[str, Sequence[str], None] = '8c176638e7f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    csv_data_category = postgresql.ENUM(
        'sales', 'production', 'inventory', 'marketing', 'finance', 'customer', 'other',
        name='csv_data_category'
    )
    csv_data_category.create(op.get_bind())

    op.add_column(
        'csv_data_analyse_table',
        sa.Column('data_category', csv_data_category, nullable=False)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('csv_data_analyse_table', 'data_category')
    postgresql.ENUM(name='csv_data_category').drop(op.get_bind())
    # ### end Alembic commands ###
