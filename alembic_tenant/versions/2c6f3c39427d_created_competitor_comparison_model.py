"""created competitor comparison model

Revision ID: 2c6f3c39427d
Revises: 0774ba1d9889
Create Date: 2026-07-13 16:36:31.280637

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2c6f3c39427d'
down_revision: Union[str, Sequence[str], None] = '0774ba1d9889'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('competitor_comparison_reports',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('competitor_id', sa.UUID(), nullable=False),
    sa.Column('competitor_name', sa.String(), nullable=False),
    sa.Column('data_freshness_note', sa.String(), nullable=True),
    sa.Column('positioning_gap', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('narrative_gap_analysis', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('reputation', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('social_presence_gap', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('trajectory', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('is_latest', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['competitor_id'], ['competitor_analyses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_competitor_comparison_reports_competitor_id'), 'competitor_comparison_reports', ['competitor_id'], unique=False)
    op.create_index(op.f('ix_competitor_comparison_reports_competitor_name'), 'competitor_comparison_reports', ['competitor_name'], unique=False)
    op.create_index(op.f('ix_competitor_comparison_reports_id'), 'competitor_comparison_reports', ['id'], unique=True)
    op.create_index(op.f('ix_competitor_comparison_reports_is_latest'), 'competitor_comparison_reports', ['is_latest'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_competitor_comparison_reports_is_latest'), table_name='competitor_comparison_reports')
    op.drop_index(op.f('ix_competitor_comparison_reports_id'), table_name='competitor_comparison_reports')
    op.drop_index(op.f('ix_competitor_comparison_reports_competitor_name'), table_name='competitor_comparison_reports')
    op.drop_index(op.f('ix_competitor_comparison_reports_competitor_id'), table_name='competitor_comparison_reports')
    op.drop_table('competitor_comparison_reports')
