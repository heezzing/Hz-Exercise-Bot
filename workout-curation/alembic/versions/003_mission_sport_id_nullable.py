"""user_missions.sport_id — NOT NULL 제거

Revision ID: 003
Create Date: 2026-04-16
"""
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE user_missions ALTER COLUMN sport_id DROP NOT NULL")
    op.execute("ALTER TABLE user_missions ADD COLUMN IF NOT EXISTS notified_at TIMESTAMPTZ")


def downgrade() -> None:
    op.execute("ALTER TABLE user_missions ALTER COLUMN sport_id SET NOT NULL")
