"""GET /api/v1/facilities — PostGIS ST_DWithin 반경 검색."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.facility import FacilityResponse

router = APIRouter()


@router.get("", response_model=list[FacilityResponse])
async def search_facilities(
    sport: str = Query(..., description="종목명"),
    lat: float = Query(..., description="사용자 위도"),
    lng: float = Query(..., description="사용자 경도"),
    radius_m: int = Query(settings.facility_search_radius_m),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT
                f.id::text,
                f.name,
                f.address,
                f.cost_per_session,
                f.phone,
                f.rating,
                ST_Distance(
                    f.location::geography,
                    ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
                ) AS distance_m
            FROM facilities f
            JOIN sports s ON f.sport_id = s.id
            WHERE s.name = :sport
              AND ST_DWithin(
                    f.location::geography,
                    ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                    :radius_m
                  )
            ORDER BY distance_m
            LIMIT 10
        """),
        {"sport": sport, "lat": lat, "lng": lng, "radius_m": radius_m},
    )
    rows = result.mappings().all()
    return [
        FacilityResponse(
            id=row["id"],
            name=row["name"],
            address=row["address"],
            cost_per_session=row["cost_per_session"],
            phone=row["phone"],
            rating=row["rating"],
            distance_m=round(row["distance_m"], 1),
        )
        for row in rows
    ]
