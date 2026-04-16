"""미션 확장 시나리오 테스트 — 만족도 3점(retry), 현재 미션 조회, 중복 완료, 피드백."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

SURVEY_BASE = {
    "user_name": "확장테스트",
    "age": 30,
    "activity_level": "주 1-2회",
    "preferred_time": "저녁",
    "social_pref": "소수",
    "stress_style": "창의적으로",
    "budget": 60000,
    "avoid": "",
}

MOCK_HERMES = {
    "recommendations": [
        {
            "sport": "테니스",
            "reason": "파트너와 즐길 수 있어요.",
            "difficulty": "약간의 체력 필요",
            "first_mission": "테니스장 체험 예약하기",
        }
    ],
    "top_pick": "테니스",
    "encouragement": "시작이 반이에요!",
}


async def _do_onboarding(client: AsyncClient, user_name: str, mission_text: str = "테니스장 체험 예약하기") -> dict:
    with (
        patch("app.api.onboarding.get_sport_recommendations", new_callable=AsyncMock, return_value=MOCK_HERMES),
        patch("app.api.onboarding.generate_mission_text", new_callable=AsyncMock, return_value=mission_text),
    ):
        res = await client.post("/api/v1/onboarding", json={**SURVEY_BASE, "user_name": user_name})
    assert res.status_code == 200
    return res.json()


@pytest.mark.asyncio
async def test_mission_complete_retry(client: AsyncClient):
    """만족도 3점 → action: retry (동일 레벨 재알림)."""
    ob = await _do_onboarding(client, "만족도3유저")
    mission_id = ob["mission_id"]

    res = await client.post(f"/api/v1/missions/{mission_id}/complete", json={"satisfaction": 3})
    assert res.status_code == 200
    body = res.json()
    assert body["action"] == "retry"
    # retry는 현재 미션 ID를 반환 (새 미션 없음)
    assert body["next_mission_id"] == mission_id


@pytest.mark.asyncio
async def test_get_current_missions(client: AsyncClient):
    """온보딩 후 GET /api/v1/missions/current → 미완료 미션 1개 반환."""
    ob = await _do_onboarding(client, "현재미션유저")
    user_id = ob["user_id"]

    res = await client.get(f"/api/v1/missions/current?user_id={user_id}")
    assert res.status_code == 200
    missions = res.json()
    assert len(missions) >= 1
    assert missions[0]["completed"] is False
    assert "mission_text" in missions[0]


@pytest.mark.asyncio
async def test_mission_already_completed(client: AsyncClient):
    """이미 완료된 미션 재완료 시도 → 400."""
    ob = await _do_onboarding(client, "중복완료유저")
    mission_id = ob["mission_id"]

    # 첫 번째 완료
    await client.post(f"/api/v1/missions/{mission_id}/complete", json={"satisfaction": 4})

    # 두 번째 완료 시도
    res = await client.post(f"/api/v1/missions/{mission_id}/complete", json={"satisfaction": 4})
    assert res.status_code == 400
    assert "이미 완료" in res.json()["detail"]


@pytest.mark.asyncio
async def test_mission_not_found(client: AsyncClient):
    """존재하지 않는 mission_id → 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    res = await client.post(f"/api/v1/missions/{fake_id}/complete", json={"satisfaction": 3})
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_feedback_endpoint(client: AsyncClient):
    """POST /api/v1/feedback → 만족도 저장 + action 반환."""
    ob = await _do_onboarding(client, "피드백유저")
    mission_id = ob["mission_id"]

    res = await client.post("/api/v1/feedback", json={"mission_id": mission_id, "satisfaction": 4})
    assert res.status_code == 200
    body = res.json()
    assert body["received"] is True
    assert body["satisfaction"] == 4
    assert "action" in body
