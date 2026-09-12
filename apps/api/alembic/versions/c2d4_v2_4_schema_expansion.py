"""v2_4_schema_expansion

Revision ID: c2d4_v2_4_schema_expansion
Revises: 7b1c2b825c38
Create Date: 2026-09-11 15:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c2d4_v2_4_schema_expansion'
down_revision = '7b1c2b825c38'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Additive EXPAND columns for environmental_observations
    with op.batch_alter_table('environmental_observations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rainfall_12h', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('rainfall_72h', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('deep_soil_moisture', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('soil_moisture_change', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('river_level_change_1h', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('river_level_rate', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('temperature', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('humidity', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('surface_pressure', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('wind_speed', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('source_type', sa.String(length=40), nullable=False, server_default='AUTOMATED_STATION'))
        batch_op.add_column(sa.Column('data_state', sa.String(length=30), nullable=False, server_default='OBSERVED'))
        batch_op.add_column(sa.Column('data_quality_status', sa.String(length=30), nullable=False, server_default='VALID'))
        batch_op.add_column(sa.Column('data_quality_score', sa.Float(), nullable=True, server_default='1.0'))
        batch_op.add_column(sa.Column('source_timestamp', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('retrieved_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('environmental_observations', schema=None) as batch_op:
        batch_op.drop_column('retrieved_at')
        batch_op.drop_column('source_timestamp')
        batch_op.drop_column('data_quality_score')
        batch_op.drop_column('data_quality_status')
        batch_op.drop_column('data_state')
        batch_op.drop_column('source_type')
        batch_op.drop_column('wind_speed')
        batch_op.drop_column('surface_pressure')
        batch_op.drop_column('humidity')
        batch_op.drop_column('temperature')
        batch_op.drop_column('river_level_rate')
        batch_op.drop_column('river_level_change_1h')
        batch_op.drop_column('soil_moisture_change')
        batch_op.drop_column('deep_soil_moisture')
        batch_op.drop_column('rainfall_72h')
        batch_op.drop_column('rainfall_12h')
