
"""init schema

Revision ID: 0001
Revises: 
Create Date: 2025-09-28
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('user',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(length=120), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table('shift',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('hours_worked', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table('trip',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('shift_id', sa.Integer(), nullable=False),
        sa.Column('fare_amount', sa.Float(), nullable=False),
        sa.Column('fuel_cost', sa.Float(), nullable=False),
        sa.Column('odometer', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['shift_id'], ['shift.id'])
    )

def downgrade():
    op.drop_table('trip')
    op.drop_table('shift')
    op.drop_table('user')
