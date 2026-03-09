"""Add extended reconnaissance and enemy knowledge

Revision ID: add_extended_recon
Revises: 5e6012dc0e16
Create Date: 2026-03-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_extended_recon'
down_revision: Union[str, None] = '5e6012dc0e16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add extended reconnaissance fields to units table
    op.add_column('units', sa.Column('confidence_score', sa.Integer(), nullable=True))
    op.add_column('units', sa.Column('estimated_x', sa.Float(), nullable=True))
    op.add_column('units', sa.Column('estimated_y', sa.Float(), nullable=True))
    op.add_column('units', sa.Column('position_accuracy', sa.Integer(), nullable=True))
    op.add_column('units', sa.Column('last_known_type', sa.String(), nullable=True))
    op.add_column('units', sa.Column('observation_sources', sa.JSON(), nullable=True))

    # Add extended fields to player_knowledge
    op.add_column('player_knowledge', sa.Column('confidence_score', sa.Integer(), nullable=True))
    op.add_column('player_knowledge', sa.Column('position_accuracy', sa.Integer(), nullable=True))

    # Create enemy_knowledge table (tracks what enemy knows about player units)
    op.create_table('enemy_knowledge',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=True),
        sa.Column('player_unit_id', sa.Integer(), nullable=True),
        sa.Column('known_x', sa.Float(), nullable=True),
        sa.Column('known_y', sa.Float(), nullable=True),
        sa.Column('area_name', sa.String(), nullable=True),
        sa.Column('confidence', sa.String(), nullable=True),
        sa.Column('confidence_score', sa.Integer(), nullable=True),
        sa.Column('last_observed_turn', sa.Integer(), nullable=True),
        sa.Column('interpreted_type', sa.String(), nullable=True),
        sa.Column('is_deceptive', sa.Boolean(), nullable=True),
        sa.Column('position_accuracy', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
        sa.ForeignKeyConstraint(['player_unit_id'], ['units.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_enemy_knowledge_id'), 'enemy_knowledge', ['id'], unique=False)


def downgrade() -> None:
    # Drop enemy_knowledge table
    op.drop_index(op.f('ix_enemy_knowledge_id'), table_name='enemy_knowledge')
    op.drop_table('enemy_knowledge')

    # Remove extended fields from player_knowledge
    op.drop_column('player_knowledge', 'position_accuracy')
    op.drop_column('player_knowledge', 'confidence_score')

    # Remove extended fields from units
    op.drop_column('units', 'observation_sources')
    op.drop_column('units', 'last_known_type')
    op.drop_column('units', 'position_accuracy')
    op.drop_column('units', 'estimated_y')
    op.drop_column('units', 'estimated_x')
    op.drop_column('units', 'confidence_score')
