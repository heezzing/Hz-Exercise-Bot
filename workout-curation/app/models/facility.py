import uuid

from geoalchemy2 import Geometry
from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Facility(Base):
    __tablename__ = "facilities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sport_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sports.id"), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    location = mapped_column(Geometry("POINT", srid=4326), nullable=True)  # PostGIS
    cost_per_session: Mapped[int] = mapped_column(Float, nullable=True)
    open_hours: Mapped[dict] = mapped_column(JSONB, nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
