"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-04-24 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'city_reference',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('place_id', sa.String(255), nullable=True, unique=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('state', sa.String(100), nullable=False),
        sa.Column('country', sa.String(10), nullable=False, server_default='US'),
        sa.Column('normalized_label', sa.String(200), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
    )

    op.create_index('idx_city_reference_normalized_label', 'city_reference', ['normalized_label'])
    op.create_index('idx_city_reference_place_id', 'city_reference', ['place_id'])

    op.create_table(
        'carriers',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(200), nullable=False, unique=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
    )

    op.create_table(
        'carrier_routes',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('origin_city_id', sa.Uuid(as_uuid=True), sa.ForeignKey('city_reference.id'), nullable=True),
        sa.Column('destination_city_id', sa.Uuid(as_uuid=True), sa.ForeignKey('city_reference.id'), nullable=True),
        sa.Column('carrier_id', sa.Uuid(as_uuid=True), sa.ForeignKey('carriers.id'), nullable=False),
        sa.Column('daily_trucks', sa.SmallInteger(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
    )

    op.create_index('idx_carrier_routes_cities', 'carrier_routes', ['origin_city_id', 'destination_city_id'])
    op.create_unique_constraint('uix_route_carrier', 'carrier_routes', ['origin_city_id', 'destination_city_id', 'carrier_id'])
    op.create_check_constraint('ck_both_null_or_both_not_null', 'carrier_routes', '(origin_city_id IS NULL) = (destination_city_id IS NULL)')


def downgrade():
    op.drop_constraint('ck_both_null_or_both_not_null', 'carrier_routes', type_='check')
    op.drop_constraint('uix_route_carrier', 'carrier_routes', type_='unique')
    op.drop_index('idx_carrier_routes_cities', table_name='carrier_routes')
    op.drop_table('carrier_routes')
    op.drop_table('carriers')
    op.drop_index('idx_city_reference_place_id', table_name='city_reference')
    op.drop_index('idx_city_reference_normalized_label', table_name='city_reference')
    op.drop_table('city_reference')
