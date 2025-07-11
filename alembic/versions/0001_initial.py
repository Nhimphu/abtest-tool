from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'flags',
        sa.Column('name', sa.String(), primary_key=True),
        sa.Column('enabled', sa.Integer(), nullable=False),
        sa.Column('rollout', sa.Float(), nullable=False),
    )
    op.create_table(
        'history',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('timestamp', sa.String()),
        sa.Column('test', sa.String()),
        sa.Column('result', sa.String()),
    )
    op.create_table(
        'session_states',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('payload', sa.String()),
        sa.Column('timestamp', sa.String()),
    )


def downgrade():
    op.drop_table('session_states')
    op.drop_table('history')
    op.drop_table('flags')
