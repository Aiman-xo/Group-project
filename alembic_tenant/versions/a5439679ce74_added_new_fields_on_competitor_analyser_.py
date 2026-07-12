"""added new fields on competitor_analyser and profile data

Revision ID: a5439679ce74
Revises: 9fd852b47cf0
Create Date: 2026-07-10 21:05:46.288635

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5439679ce74'
down_revision: Union[str, Sequence[str], None] = '9fd852b47cf0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('company_profile_datas', sa.Column('instagram', sa.String(), nullable=True))
    op.add_column('company_profile_datas', sa.Column('rating_score', sa.String(), nullable=True))
    op.add_column('company_profile_datas', sa.Column('total_reviews', sa.Integer(), nullable=True))
    op.add_column('company_profile_datas', sa.Column('review_source', sa.String(), nullable=True))
    op.add_column('company_profile_datas', sa.Column('positive_themes', sa.ARRAY(sa.Text()), nullable=True))
    op.add_column('company_profile_datas', sa.Column('negative_themes', sa.ARRAY(sa.Text()), nullable=True))
    op.add_column('company_profile_datas', sa.Column('community_insights', sa.ARRAY(sa.Text()), nullable=True))

    op.add_column('competitor_analyses', sa.Column('instagram', sa.String(), nullable=True))
    op.add_column('competitor_analyses', sa.Column('rating_score', sa.String(), nullable=True))
    op.add_column('competitor_analyses', sa.Column('total_reviews', sa.Integer(), nullable=True))
    op.add_column('competitor_analyses', sa.Column('review_source', sa.String(), nullable=True))
    op.add_column('competitor_analyses', sa.Column('positive_themes', sa.ARRAY(sa.Text()), nullable=True))
    op.add_column('competitor_analyses', sa.Column('negative_themes', sa.ARRAY(sa.Text()), nullable=True))
    op.add_column('competitor_analyses', sa.Column('community_insights', sa.ARRAY(sa.Text()), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('competitor_analyses', 'community_insights')
    op.drop_column('competitor_analyses', 'negative_themes')
    op.drop_column('competitor_analyses', 'positive_themes')
    op.drop_column('competitor_analyses', 'review_source')
    op.drop_column('competitor_analyses', 'total_reviews')
    op.drop_column('competitor_analyses', 'rating_score')
    op.drop_column('competitor_analyses', 'instagram')

    op.drop_column('company_profile_datas', 'community_insights')
    op.drop_column('company_profile_datas', 'negative_themes')
    op.drop_column('company_profile_datas', 'positive_themes')
    op.drop_column('company_profile_datas', 'review_source')
    op.drop_column('company_profile_datas', 'total_reviews')
    op.drop_column('company_profile_datas', 'rating_score')
    op.drop_column('company_profile_datas', 'instagram')
