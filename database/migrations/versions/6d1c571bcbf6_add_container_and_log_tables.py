"""Add container and log tables

Revision ID: 6d1c571bcbf6
Revises: 
Create Date: 2023-03-08 21:56:32.334845

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6d1c571bcbf6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('container',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('port', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('container', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_container_port'), ['port'], unique=True)

    op.create_table('logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('container_id', sa.Integer(), nullable=True),
    sa.Column('message', sa.String(length=255), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['container_id'], ['container.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('logs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_logs_message'), ['message'], unique=False)
        batch_op.create_index(batch_op.f('ix_logs_timestamp'), ['timestamp'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('logs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_logs_timestamp'))
        batch_op.drop_index(batch_op.f('ix_logs_message'))

    op.drop_table('logs')
    with op.batch_alter_table('container', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_container_port'))

    op.drop_table('container')
    # ### end Alembic commands ###
