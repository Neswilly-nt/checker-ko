"""Deny direct Supabase Data API access to application tables."""
from alembic import op
from alembic import context

revision = '20261103_02'
down_revision = 'a21671b7d99d'
branch_labels = None
depends_on = None

TABLES = (
    'users', 'user_sessions', 'media_assets', 'media_analyses',
    'verification_cases', 'case_videos', 'case_social_posts', 'evidence',
    'source_assessments', 'source_assessment_history', 'verdicts',
    'source_directory', 'directory_contacts', 'statistical_observations',
    'audit_events', 'news_sources', 'news_items', 'news_syncs',
)


def upgrade() -> None:
    # SQLite has no row-level security; keep local development migrations usable.
    if context.get_context().dialect.name != 'postgresql':
        return
    # The API connects as its database owner; owner access remains available.
    # Supabase anon/authenticated roles get no table policy and are denied.
    for table in TABLES:
        op.execute(f'ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    if context.get_context().dialect.name != 'postgresql':
        return
    raise RuntimeError('Refusing to disable Supabase table RLS through an automatic downgrade.')
