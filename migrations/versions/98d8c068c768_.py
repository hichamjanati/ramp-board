"""empty message

Revision ID: 98d8c068c768
Revises: 68f8b62efa49
Create Date: 2016-07-04 15:50:02.958274

"""

# revision identifiers, used by Alembic.
revision = '98d8c068c768'
down_revision = '68f8b62efa49'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('events', sa.Column('official_score_index', sa.Integer(), nullable=True))
    op.drop_column('events', 'official_score_name')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('events', sa.Column('official_score_name', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('events', 'official_score_index')
    ### end Alembic commands ###
