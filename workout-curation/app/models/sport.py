import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Sport(Base):
    __tablename__ = "sports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    cost_level: Mapped[int] = mapped_column(Integer, nullable=False)       # 1~5
    injury_risk: Mapped[int] = mapped_column(Integer, nullable=False)      # 1~5
    social_level: Mapped[int] = mapped_column(Integer, nullable=False)     # 1(혼자)~5(단체)
    space_required: Mapped[bool] = mapped_column(Boolean, default=False)
    indoor: Mapped[bool] = mapped_column(Boolean, default=True)
    tags: Mapped[list] = mapped_column(ARRAY(String), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    embedding: Mapped[list] = mapped_column(Vector(1536), nullable=True)   # pgvector
