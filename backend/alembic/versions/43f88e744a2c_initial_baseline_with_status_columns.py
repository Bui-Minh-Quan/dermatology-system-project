"""Initial baseline with status columns

Revision ID: 43f88e744a2c
Revises: 
Create Date: 2026-05-20 04:57:46.969392

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '43f88e744a2c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. explicitly create the ENUM type in PostgreSQL first
    diagnosis_status = postgresql.ENUM('pending', 'processing', 'completed', 'rejected', 'failed', name='diagnosisstatusenum')
    diagnosis_status.create(op.get_bind(), checkfirst=True)

    # 2. Alembic's auto-generated column additions
    op.add_column('ai_diagnosis', sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'rejected', 'failed', name='diagnosisstatusenum'), nullable=True))
    op.add_column('ai_diagnosis', sa.Column('error_message', sa.Text(), nullable=True))
    op.drop_column('patient_profiles', 'avatar_url')


def downgrade() -> None:
    # 1. Alembic's auto-generated column drops
    op.add_column('patient_profiles', sa.Column('avatar_url', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('ai_diagnosis', 'error_message')
    op.drop_column('ai_diagnosis', 'status')

    # 2. explicitly drop the ENUM type
    diagnosis_status = postgresql.ENUM('pending', 'processing', 'completed', 'rejected', 'failed', name='diagnosisstatusenum')
    diagnosis_status.drop(op.get_bind(), checkfirst=True)
