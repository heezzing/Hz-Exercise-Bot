"""initial schema with PostGIS and pgvector

Revision ID: 001
Create Date: 2026-04-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
from geoalchemy2 import Geometry

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostGIS, pgvector 확장 활성화
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("age", sa.Integer, nullable=False),
        sa.Column("location_lat", sa.Float, nullable=True),
        sa.Column("location_lng", sa.Float, nullable=True),
        sa.Column("lifestyle_vector", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "sports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("cost_level", sa.Integer, nullable=False),
        sa.Column("injury_risk", sa.Integer, nullable=False),
        sa.Column("social_level", sa.Integer, nullable=False),
        sa.Column("space_required", sa.Boolean, default=False),
        sa.Column("indoor", sa.Boolean, default=True),
        sa.Column("tags", ARRAY(sa.String), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("embedding", sa.Text, nullable=True),  # vector(1536) — raw DDL로 처리
    )
    # pgvector 컬럼은 raw DDL로
    op.execute("ALTER TABLE sports ALTER COLUMN embedding TYPE vector(1536) USING NULL::vector(1536)")

    op.create_table(
        "facilities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("sport_id", UUID(as_uuid=True), sa.ForeignKey("sports.id"), nullable=False),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("location", Geometry("POINT", srid=4326), nullable=True),
        sa.Column("cost_per_session", sa.Float, nullable=True),
        sa.Column("open_hours", JSONB, nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("rating", sa.Float, nullable=True),
    )
    op.create_index("idx_facilities_location", "facilities", ["location"], postgresql_using="gist", if_not_exists=True)

    op.create_table(
        "user_missions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("sport_id", UUID(as_uuid=True), sa.ForeignKey("sports.id"), nullable=False),
        sa.Column("facility_id", UUID(as_uuid=True), sa.ForeignKey("facilities.id"), nullable=True),
        sa.Column("mission_text", sa.Text, nullable=False),
        sa.Column("level", sa.Integer, default=1),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("completed", sa.Boolean, default=False),
        sa.Column("satisfaction", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "recommendations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("sport_ids", ARRAY(UUID(as_uuid=True)), nullable=False),
        sa.Column("hermes_reasoning", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("recommendations")
    op.drop_table("user_missions")
    op.drop_index("idx_facilities_location", table_name="facilities")
    op.drop_table("facilities")
    op.drop_table("sports")
    op.drop_table("users")
