"""create site_content table

Revision ID: 8a6ba9be6730
Revises: b2c3d4e5f6g7
Create Date: 2026-07-25 07:27:45.041659

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a6ba9be6730'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'site_content',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.JSON(), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_site_content_id'), 'site_content', ['id'], unique=False)
    op.create_index(op.f('ix_site_content_key'), 'site_content', ['key'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_site_content_key'), table_name='site_content')
    op.drop_index(op.f('ix_site_content_id'), table_name='site_content')
    op.drop_table('site_content')
