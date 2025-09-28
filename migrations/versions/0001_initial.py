"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2025-09-28 16:54:06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table('shifts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('work_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=True),
        sa.Column('end_time', sa.Time(), nullable=True),
        sa.Column('manual_hours', sa.Float(), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shifts_work_date'), 'shifts', ['work_date'], unique=False)

    op.create_table('trips',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shift_id', sa.Integer(), nullable=False),
        sa.Column('block_pay', sa.Float(), nullable=False),
        sa.Column('tips', sa.Float(), nullable=False),
        sa.Column('fuel_cost', sa.Float(), nullable=True),
        sa.Column('fuel_volume_gal', sa.Float(), nullable=True),
        sa.Column('odometer_start', sa.Integer(), nullable=True),
        sa.Column('odometer_end', sa.Integer(), nullable=True),
        sa.Column('receipt_path', sa.String(length=300), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['shift_id'], ['shifts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trips_shift_id'), 'trips', ['shift_id'], unique=False)

    op.create_table('scheduled_rides',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('start_dt', sa.DateTime(), nullable=False),
        sa.Column('end_dt', sa.DateTime(), nullable=True),
        sa.Column('expected_block_pay', sa.Float(), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scheduled_rides_start_dt'), 'scheduled_rides', ['start_dt'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_scheduled_rides_start_dt'), table_name='scheduled_rides')
    op.drop_table('scheduled_rides')
    op.drop_index(op.f('ix_trips_shift_id'), table_name='trips')
    op.drop_table('trips')
    op.drop_index(op.f('ix_shifts_work_date'), table_name='shifts')
    op.drop_table('shifts')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
