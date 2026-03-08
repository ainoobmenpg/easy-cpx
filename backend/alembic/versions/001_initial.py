"""Initial database schema

Revision ID: 001_initial
Revises:
Create Date: 2026-03-08

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create games table
    op.create_table('games',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('current_turn', sa.Integer(), nullable=True),
        sa.Column('current_time', sa.String(), nullable=True),
        sa.Column('weather', sa.String(), nullable=True),
        sa.Column('phase', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_games_id'), 'games', ['id'], unique=False)

    # Create units table
    op.create_table('units',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('unit_type', sa.String(), nullable=False),
        sa.Column('side', sa.String(), nullable=False),
        sa.Column('x', sa.Float(), nullable=False),
        sa.Column('y', sa.Float(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('ammo', sa.String(), nullable=True),
        sa.Column('fuel', sa.String(), nullable=True),
        sa.Column('readiness', sa.String(), nullable=True),
        sa.Column('strength', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_units_id'), 'units', ['id'], unique=False)

    # Create turns table
    op.create_table('turns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=True),
        sa.Column('turn_number', sa.Integer(), nullable=False),
        sa.Column('time', sa.String(), nullable=False),
        sa.Column('weather', sa.String(), nullable=True),
        sa.Column('phase', sa.String(), nullable=True),
        sa.Column('sitrep', sa.JSON(), nullable=True),
        sa.Column('excon_orders', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_turns_id'), 'turns', ['id'], unique=False)

    # Create orders table
    op.create_table('orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=True),
        sa.Column('unit_id', sa.Integer(), nullable=True),
        sa.Column('turn_id', sa.Integer(), nullable=True),
        sa.Column('order_type', sa.String(), nullable=False),
        sa.Column('target_units', sa.JSON(), nullable=True),
        sa.Column('intent', sa.Text(), nullable=False),
        sa.Column('location_x', sa.Float(), nullable=True),
        sa.Column('location_y', sa.Float(), nullable=True),
        sa.Column('location_name', sa.String(), nullable=True),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('parsed_order', sa.JSON(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('outcome', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ),
        sa.ForeignKeyConstraint(['turn_id'], ['turns.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_id'), 'orders', ['id'], unique=False)

    # Create events table
    op.create_table('events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('turn_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['turn_id'], ['turns.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_id'), 'events', ['id'], unique=False)

    # Create player_knowledge table
    op.create_table('player_knowledge',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=True),
        sa.Column('unit_id', sa.Integer(), nullable=True),
        sa.Column('x', sa.Float(), nullable=True),
        sa.Column('y', sa.Float(), nullable=True),
        sa.Column('area_name', sa.String(), nullable=True),
        sa.Column('confidence', sa.String(), nullable=True),
        sa.Column('last_observed_turn', sa.Integer(), nullable=True),
        sa.Column('interpreted_type', sa.String(), nullable=True),
        sa.Column('interpreted_side', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_player_knowledge_id'), 'player_knowledge', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_player_knowledge_id'), table_name='player_knowledge')
    op.drop_table('player_knowledge')
    op.drop_index(op.f('ix_events_id'), table_name='events')
    op.drop_table('events')
    op.drop_index(op.f('ix_orders_id'), table_name='orders')
    op.drop_table('orders')
    op.drop_index(op.f('ix_turns_id'), table_name='turns')
    op.drop_table('turns')
    op.drop_index(op.f('ix_units_id'), table_name='units')
    op.drop_table('units')
    op.drop_index(op.f('ix_games_id'), table_name='games')
    op.drop_table('games')
