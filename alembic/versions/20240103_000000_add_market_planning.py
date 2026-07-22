"""Add market planning tables

Add tables for Market Planning module:
- market_plannings
- planning_documents

Revision ID: 003
Revises: 002
Create Date: 2024-01-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types for PostgreSQL if needed
    # For SQLite, enums are stored as strings
    
    # Table: market_plannings
    op.create_table(
        'market_plannings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('planning_number', sa.String(length=50), nullable=False),
        sa.Column('fiscal_year', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('project_type', sa.String(length=50), nullable=False),
        sa.Column('procedure_type', sa.String(length=50), nullable=False),
        sa.Column('estimated_budget', sa.Float(), nullable=False),
        sa.Column('funding_source', sa.String(length=200), nullable=True),
        sa.Column('requesting_service_id', sa.Integer(), nullable=True),
        sa.Column('requesting_service_name', sa.String(length=200), nullable=True),
        sa.Column('responsible_id', sa.Integer(), nullable=True),
        sa.Column('responsible_name', sa.String(length=200), nullable=True),
        sa.Column('priority', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('launch_date', sa.DateTime(), nullable=True),
        sa.Column('bid_opening_date', sa.DateTime(), nullable=True),
        sa.Column('attribution_date', sa.DateTime(), nullable=True),
        sa.Column('notification_date', sa.DateTime(), nullable=True),
        sa.Column('service_order_date', sa.DateTime(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('observations', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('modified_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('planning_number'),
        sa.ForeignKeyConstraint(['requesting_service_id'], ['services.id'], ),
        sa.ForeignKeyConstraint(['responsible_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['modified_by'], ['users.id'], )
    )
    
    # Create indexes for market_plannings
    op.create_index('ix_market_plannings_planning_number', 'market_plannings', ['planning_number'])
    op.create_index('ix_market_plannings_fiscal_year', 'market_plannings', ['fiscal_year'])
    op.create_index('ix_market_plannings_status', 'market_plannings', ['status'])
    op.create_index('ix_market_plannings_project_type', 'market_plannings', ['project_type'])
    op.create_index('ix_market_plannings_procedure_type', 'market_plannings', ['procedure_type'])
    op.create_index('ix_market_plannings_created_at', 'market_plannings', ['created_at'])
    
    # Table: planning_documents
    op.create_table(
        'planning_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('planning_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Float(), nullable=True),
        sa.Column('file_type', sa.String(length=100), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['planning_id'], ['market_plannings.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], )
    )
    
    # Create indexes for planning_documents
    op.create_index('ix_planning_documents_planning_id', 'planning_documents', ['planning_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_planning_documents_planning_id', table_name='planning_documents')
    op.drop_index('ix_market_plannings_created_at', table_name='market_plannings')
    op.drop_index('ix_market_plannings_procedure_type', table_name='market_plannings')
    op.drop_index('ix_market_plannings_project_type', table_name='market_plannings')
    op.drop_index('ix_market_plannings_status', table_name='market_plannings')
    op.drop_index('ix_market_plannings_fiscal_year', table_name='market_plannings')
    op.drop_index('ix_market_plannings_planning_number', table_name='market_plannings')
    
    # Drop tables
    op.drop_table('planning_documents')
    op.drop_table('market_plannings')
