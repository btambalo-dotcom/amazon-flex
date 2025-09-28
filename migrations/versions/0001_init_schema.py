
"""init schema

Revision ID: 0001
Revises: None
Create Date: 2025-09-28 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )
    op.create_table('shifts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('work_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=True),
        sa.Column('end_time', sa.Time(), nullable=True),
        sa.Column('manual_hours', sa.Float(), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True)
    )
    op.create_table('trips',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('shift_id', sa.Integer(), nullable=False),
        sa.Column('block_pay', sa.Float(), nullable=False, server_default='0'),
        sa.Column('tips', sa.Float(), nullable=True, server_default='0'),
        sa.Column('fuel_cost', sa.Float(), nullable=True),
        sa.Column('fuel_volume_gal', sa.Float(), nullable=True),
        sa.Column('odometer_start', sa.Integer(), nullable=True),
        sa.Column('odometer_end', sa.Integer(), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True)
    )
    op.create_foreign_key('fk_trips_shift', 'trips', 'shifts', ['shift_id'], ['id'], ondelete='CASCADE')

    op.create_table('expenses',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('shift_id', sa.Integer(), nullable=True),
        sa.Column('trip_id', sa.Integer(), nullable=True),
        sa.Column('exp_date', sa.Date(), nullable=False),
        sa.Column('category', sa.String(length=80), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('notes', sa.String(length=500), nullable=True)
    )
    op.create_foreign_key('fk_exp_shift', 'expenses', 'shifts', ['shift_id'], ['id'])
    op.create_foreign_key('fk_exp_trip', 'expenses', 'trips', ['trip_id'], ['id'])

    op.create_table('scheduled_rides',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('start_dt', sa.DateTime(), nullable=False),
        sa.Column('end_dt', sa.DateTime(), nullable=True),
        sa.Column('expected_block_pay', sa.Float(), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True)
    )

def downgrade():
    op.drop_table('scheduled_rides')
    op.drop_constraint('fk_exp_trip', 'expenses', type_='foreignkey')
    op.drop_constraint('fk_exp_shift', 'expenses', type_='foreignkey')
    op.drop_table('expenses')
    op.drop_constraint('fk_trips_shift', 'trips', type_='foreignkey')
    op.drop_table('trips')
    op.drop_table('shifts')
    op.drop_table('users')
