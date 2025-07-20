"""initaial

Revision ID: 98f8bb68cc11
Revises: 
Create Date: 2024-01-04 03:29:06.657925

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '98f8bb68cc11'
down_revision = None
branch_labels = None
depends_on = None

# Initial migration file (entrypoint) used to locate first migration
# If there is no --version-path provided in terminal args, this migration would be used to specify migrations location


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
