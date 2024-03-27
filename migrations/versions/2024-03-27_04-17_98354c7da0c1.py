"""empty message

Revision ID: 98354c7da0c1
Revises: 
Create Date: 2024-03-27 04:17:41.668625

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '98354c7da0c1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('hashed_tg_id', sa.TEXT(), nullable=False),
    sa.Column('vktoken', sa.TEXT(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('users')
    # ### end Alembic commands ###