"""added more fields to registered instagram and competitor instagram models

Revision ID: 0569c27bd5e4
Revises: 502fe67fc6d2
Create Date: 2026-08-01 13:44:01.594520

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0569c27bd5e4'
down_revision: Union[str, Sequence[str], None] = '502fe67fc6d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # instagram_analysis
    op.add_column('instagram_analysis', sa.Column('content_type_performance', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('instagram_analysis', sa.Column('posting_frequency_per_week', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('instagram_analysis', sa.Column('has_external_links', sa.Boolean(), nullable=True))
    op.add_column('instagram_analysis', sa.Column('avg_hashtags_per_post', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('instagram_analysis', sa.Column('avg_caption_length', sa.Numeric(precision=10, scale=2), nullable=True))

    # instagram_competitor_profile
    op.add_column('instagram_competitor_profile', sa.Column('content_type_performance', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('instagram_competitor_profile', sa.Column('posting_frequency_per_week', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('instagram_competitor_profile', sa.Column('has_external_links', sa.Boolean(), nullable=True))
    op.add_column('instagram_competitor_profile', sa.Column('avg_hashtags_per_post', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('instagram_competitor_profile', sa.Column('avg_caption_length', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('instagram_competitor_profile', sa.Column('latest_posts', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('instagram_competitor_profile', 'latest_posts')
    op.drop_column('instagram_competitor_profile', 'avg_caption_length')
    op.drop_column('instagram_competitor_profile', 'avg_hashtags_per_post')
    op.drop_column('instagram_competitor_profile', 'has_external_links')
    op.drop_column('instagram_competitor_profile', 'posting_frequency_per_week')
    op.drop_column('instagram_competitor_profile', 'content_type_performance')

    op.drop_column('instagram_analysis', 'avg_caption_length')
    op.drop_column('instagram_analysis', 'avg_hashtags_per_post')
    op.drop_column('instagram_analysis', 'has_external_links')
    op.drop_column('instagram_analysis', 'posting_frequency_per_week')
    op.drop_column('instagram_analysis', 'content_type_performance')
    # ### end Alembic commands ###
