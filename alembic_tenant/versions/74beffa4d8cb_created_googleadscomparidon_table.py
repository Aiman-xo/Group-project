"""created Googleadscomparidon table

Revision ID: 74beffa4d8cb
Revises: 0569c27bd5e4
Create Date: 2026-08-04 10:37:27.711711

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '74beffa4d8cb'
down_revision: Union[str, Sequence[str], None] = '0569c27bd5e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'google_ads_comparison_reports',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('competitor_id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=True),
        sa.Column('competitor_name', sa.String(), nullable=True),
        sa.Column('active_ads_count', sa.Integer(), nullable=False),
        sa.Column('ad_copy_strategy_gap', sa.Text(), nullable=True),
        sa.Column('media_format_gap', sa.Text(), nullable=True),
        sa.Column('positioning_summary', sa.Text(), nullable=True),
        sa.Column('raw_ads_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('is_latest', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['competitor_id'], ['competitors.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id'),
    )
    op.create_index(op.f('ix_google_ads_comparison_reports_company_id'), 'google_ads_comparison_reports', ['company_id'], unique=False)
    op.create_index(op.f('ix_google_ads_comparison_reports_competitor_id'), 'google_ads_comparison_reports', ['competitor_id'], unique=False)
    op.create_index(op.f('ix_google_ads_comparison_reports_competitor_name'), 'google_ads_comparison_reports', ['competitor_name'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_google_ads_comparison_reports_competitor_name'), table_name='google_ads_comparison_reports')
    op.drop_index(op.f('ix_google_ads_comparison_reports_competitor_id'), table_name='google_ads_comparison_reports')
    op.drop_index(op.f('ix_google_ads_comparison_reports_company_id'), table_name='google_ads_comparison_reports')
    op.drop_table('google_ads_comparison_reports')
    # ### end Alembic commands ###
