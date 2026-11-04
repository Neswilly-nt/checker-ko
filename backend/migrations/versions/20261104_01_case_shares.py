"""Add revocable, read-only capability links for dossier sharing."""
from alembic import context, op
import sqlalchemy as sa

revision = '20261104_01'
down_revision = '20261103_02'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('case_shares',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['verification_cases.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('case_id'),
        sa.UniqueConstraint('token_hash'),
    )
    op.create_index('ix_case_shares_case_id', 'case_shares', ['case_id'], unique=True)
    op.create_index('ix_case_shares_token_hash', 'case_shares', ['token_hash'], unique=True)
    if context.get_context().dialect.name == 'postgresql':
        op.execute('ALTER TABLE public.case_shares ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    op.drop_index('ix_case_shares_token_hash', table_name='case_shares')
    op.drop_index('ix_case_shares_case_id', table_name='case_shares')
    op.drop_table('case_shares')
