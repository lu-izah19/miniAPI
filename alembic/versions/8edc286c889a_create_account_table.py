"""create account table

Revision ID: 8edc286c889a
Revises: 
Create Date: 2026-09-18 09:03:42.850948

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8edc286c889a'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'usuarios',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('nome', sa.String(50), nullable=False),
        sa.Column('email', sa.String(50), nullable=False),
        sa.Column('senha', sa.String(8), nullable=False),
        sa.Column('papel', sa.String(8), nullable=False),
    )
    pass


def downgrade():
    op.drop_table('usuarios')
    pass
