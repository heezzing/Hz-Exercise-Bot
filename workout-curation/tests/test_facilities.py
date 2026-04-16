"""시설 검색 테스트."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_facility_search_returns_results(client: AsyncClient):
    """강남역 근처 클라이밍 시설 검색 → 결과 반환."""
    res = await client.get("/api/v1/facilities", params={
        "sport": "클라이밍",
        "lat": 37.498,
        "lng": 127.028,
        "radius_m": 5000,
    })
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    first = data[0]
    assert "name" in first
    assert "distance_m" in first
    assert first["distance_m"] > 0


@pytest.mark.asyncio
async def test_facility_search_no_result_far(client: AsyncClient):
    """먼 지역(제주도)에서 클라이밍 검색 → 빈 리스트."""
    res = await client.get("/api/v1/facilities", params={
        "sport": "클라이밍",
        "lat": 33.489,   # 제주
        "lng": 126.498,
        "radius_m": 5000,
    })
    assert res.status_code == 200
    assert res.json() == []


@pytest.mark.asyncio
async def test_facility_search_sorted_by_distance(client: AsyncClient):
    """검색 결과가 거리 오름차순으로 정렬되는지 확인."""
    res = await client.get("/api/v1/facilities", params={
        "sport": "클라이밍",
        "lat": 37.50,
        "lng": 127.00,
        "radius_m": 10000,
    })
    assert res.status_code == 200
    data = res.json()
    if len(data) >= 2:
        distances = [d["distance_m"] for d in data]
        assert distances == sorted(distances)
