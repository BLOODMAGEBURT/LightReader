"""phone

Revision ID: 6a87fdb34e4f
Revises: 7047d743ce25
Create Date: 2019-04-24 17:41:46.252280

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6a87fdb34e4f'
down_revision = '7047d743ce25'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('phone', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'phone')
    # ### end Alembic commands ###
