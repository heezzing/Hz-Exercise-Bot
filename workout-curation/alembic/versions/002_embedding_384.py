"""embedding column: vector(1536) → vector(384) for paraphrase-multilingual-MiniLM

Revision ID: 002
Create Date: 2026-04-15
"""
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # NULL로 초기화 후 차원 변경 (기존 1536-dim 데이터 없음)
    op.execute("ALTER TABLE sports ALTER COLUMN embedding TYPE vector(384) USING NULL::vector(384)")


def downgrade() -> None:
    op.execute("ALTER TABLE sports ALTER COLUMN embedding TYPE vector(1536) USING NULL::vector(1536)")
