from pydantic import BaseModel


class FacilityResponse(BaseModel):
    id: str
    name: str
    address: str | None
    cost_per_session: float | None
    phone: str | None
    rating: float | None
    distance_m: float | None = None
