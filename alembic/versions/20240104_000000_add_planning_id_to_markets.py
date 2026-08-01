"""Add planning_id column to markets table

Add foreign key relationship between markets and market_plannings:
- Add planning_id column to markets table
- Add foreign key constraint to market_plannings.id

Revision ID: 004
Revises: 003
Create Date: 2024-01-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add planning_id column to markets table
    op.add_column('markets', sa.Column('planning_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_markets_planning_id',
        'markets', 'market_plannings',
        ['planning_id'], ['id']
    )
    
    # Create index for planning_id
    op.create_index('ix_markets_planning_id', 'markets', ['planning_id'])


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_markets_planning_id', table_name='markets')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_markets_planning_id', 'markets', type_='foreignkey')
    
    # Drop column
    op.drop_column('markets', 'planning_id')
