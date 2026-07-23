"""created csv upload model

Revision ID: 652f51b309fb
Revises: 2c6f3c39427d
Create Date: 2026-07-23 14:28:48.956511

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '652f51b309fb'
down_revision: Union[str, Sequence[str], None] = '2c6f3c39427d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('csv_data_analyse_table',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('company_id', sa.UUID(), nullable=True),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('raw_csv_s3_key', sa.String(), nullable=True),
    sa.Column('parsed_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('health_score', sa.Integer(), nullable=True),
    sa.Column('health_score_reason', sa.Text(), nullable=True),
    sa.Column('growth_areas', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('problem_areas', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('metric_changes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('csv_data_analyse_table')
