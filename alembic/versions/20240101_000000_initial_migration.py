"""Initial migration

Create all tables for the public markets management system

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    
    # Create markets table
    op.create_table(
        'markets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('market_number', sa.String(length=50), nullable=True),
        sa.Column('object', sa.Text(), nullable=True),
        sa.Column('owner', sa.String(length=200), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=True),
        sa.Column('procurement_mode', sa.String(length=100), nullable=True),
        sa.Column('budget', sa.Float(), nullable=True),
        sa.Column('credits', sa.Float(), nullable=True),
        sa.Column('responsible_service', sa.String(length=100), nullable=True),
        sa.Column('followup_responsibles', sa.Text(), nullable=True),
        sa.Column('participating_companies', sa.Text(), nullable=True),
        sa.Column('awardee', sa.String(length=200), nullable=True),
        sa.Column('estimated_amount', sa.Float(), nullable=True),
        sa.Column('final_amount', sa.Float(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('expected_end_date', sa.DateTime(), nullable=True),
        sa.Column('actual_end_date', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id'], )
    )
    
    # Create stages table
    op.create_table(
        'stages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('market_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('progress_percentage', sa.Float(), nullable=True),
        sa.Column('planned_date', sa.DateTime(), nullable=True),
        sa.Column('actual_date', sa.DateTime(), nullable=True),
        sa.Column('responsible', sa.String(length=100), nullable=True),
        sa.Column('observations', sa.Text(), nullable=True),
        sa.Column('is_late', sa.Boolean(), nullable=True),
        sa.Column('delay_days', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['market_id'], ['markets.id'], )
    )
    
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('market_id', sa.Integer(), nullable=True),
        sa.Column('stage_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['market_id'], ['markets.id'], ),
        sa.ForeignKeyConstraint(['stage_id'], ['stages.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], )
    )
    
    # Create history table
    op.create_table(
        'history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('market_id', sa.Integer(), nullable=True),
        sa.Column('stage_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('old_values', sa.Text(), nullable=True),
        sa.Column('new_values', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['market_id'], ['markets.id'], ),
        sa.ForeignKeyConstraint(['stage_id'], ['stages.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )
    
    # Create indexes for better performance
    op.create_index('ix_markets_market_number', 'markets', ['market_number'])
    op.create_index('ix_markets_status', 'markets', ['status'])
    op.create_index('ix_markets_created_at', 'markets', ['created_at'])
    op.create_index('ix_stages_market_id', 'stages', ['market_id'])
    op.create_index('ix_stages_status', 'stages', ['status'])
    op.create_index('ix_history_market_id', 'history', ['market_id'])
    op.create_index('ix_history_created_at', 'history', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_history_created_at', table_name='history')
    op.drop_index('ix_history_market_id', table_name='history')
    op.drop_index('ix_stages_status', table_name='stages')
    op.drop_index('ix_stages_market_id', table_name='stages')
    op.drop_index('ix_markets_created_at', table_name='markets')
    op.drop_index('ix_markets_status', table_name='markets')
    op.drop_index('ix_markets_market_number', table_name='markets')
    
    # Drop tables
    op.drop_table('history')
    op.drop_table('documents')
    op.drop_table('stages')
    op.drop_table('markets')
    op.drop_table('users')
