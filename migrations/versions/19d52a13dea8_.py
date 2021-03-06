"""empty message

Revision ID: 19d52a13dea8
Revises: 95fb17c0c4cc
Create Date: 2019-05-30 15:16:33.133384

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '19d52a13dea8'
down_revision = '95fb17c0c4cc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('todo_type', sa.Column('type_name', sa.String(length=50), nullable=False))
    op.drop_column('todo_type', 'name')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('todo_type', sa.Column('name', mysql.VARCHAR(length=50), nullable=False))
    op.drop_column('todo_type', 'type_name')
    # ### end Alembic commands ###
