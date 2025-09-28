"""Initial schema

Revision ID: 0001_init
Revises: 
Create Date: 2025-09-28
"""
from alembic import op
import sqlalchemy as sa

revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(length=120), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    op.create_table('shifts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('hours_worked', sa.Float(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    op.create_table('trips',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('shift_id', sa.Integer(), sa.ForeignKey('shifts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('fare_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('fuel_cost', sa.Float(), nullable=False, server_default='0'),
        sa.Column('odometer', sa.Float(), nullable=True),
        sa.Column('tips', sa.Float(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    op.create_table('expenses',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('shift_id', sa.Integer(), sa.ForeignKey('shifts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('trip_id', sa.Integer(), sa.ForeignKey('trips.id', ondelete='SET NULL'), nullable=True),
        sa.Column('exp_date', sa.Date(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

def downgrade():
    op.drop_table('expenses')
    op.drop_table('trips')
    op.drop_table('shifts')
    op.drop_table('users')
