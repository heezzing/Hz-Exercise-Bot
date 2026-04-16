"""미션 완료 분기 로직 테스트 (Hermes 호출 mock)."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

SURVEY = {
    "user_name": "테스트유저",
    "age": 28,
    "activity_level": "거의 없음",
    "preferred_time": "저녁",
    "social_pref": "혼자",
    "stress_style": "조용하게",
    "budget": 50000,
    "avoid": "물",
}

MOCK_HERMES_RESULT = {
    "recommendations": [
        {
            "sport": "클라이밍",
            "reason": "혼자 집중하며 성취감을 느낄 수 있어요.",
            "difficulty": "약간의 체력 필요",
            "first_mission": "이번 주말 클라이밍 체험 예약하기",
        }
    ],
    "top_pick": "클라이밍",
    "encouragement": "첫 발걸음이 가장 중요해요!",
}


@pytest.mark.asyncio
async def test_onboarding_creates_mission(client: AsyncClient):
    """온보딩 완료 시 mission_id와 mission_text가 응답에 포함된다."""
    with patch(
        "app.api.onboarding.get_sport_recommendations",
        new_callable=AsyncMock,
        return_value=MOCK_HERMES_RESULT,
    ), patch(
        "app.api.onboarding.generate_mission_text",
        new_callable=AsyncMock,
        return_value="이번 주말 클라이밍 체험 예약하기",
    ):
        res = await client.post("/api/v1/onboarding", json=SURVEY)

    assert res.status_code == 200
    body = res.json()
    assert body["top_pick"] == "클라이밍"
    assert "mission_id" in body
    assert "mission_text" in body
    assert "user_id" in body


@pytest.mark.asyncio
async def test_mission_complete_high_satisfaction(client: AsyncClient):
    """만족도 5점 → action: next_level, 다음 미션 생성."""
    with patch(
        "app.api.onboarding.get_sport_recommendations",
        new_callable=AsyncMock,
        return_value=MOCK_HERMES_RESULT,
    ), patch(
        "app.api.onboarding.generate_mission_text",
        new_callable=AsyncMock,
        return_value="클라이밍 2-3회 방문해보기",
    ):
        ob = await client.post("/api/v1/onboarding", json={**SURVEY, "user_name": "고만족유저"})
    mission_id = ob.json()["mission_id"]

    with patch(
        "app.services.hermes.generate_mission_text",
        new_callable=AsyncMock,
        return_value="클라이밍 기본기 배우기",
    ):
        res = await client.post(
            f"/api/v1/missions/{mission_id}/complete",
            json={"satisfaction": 5},
        )

    assert res.status_code == 200
    body = res.json()
    assert body["action"] == "next_level"
    assert body["next_mission_id"] is not None


@pytest.mark.asyncio
async def test_mission_complete_low_satisfaction(client: AsyncClient):
    """만족도 1점 → action: re_recommend."""
    with patch(
        "app.api.onboarding.get_sport_recommendations",
        new_callable=AsyncMock,
        return_value=MOCK_HERMES_RESULT,
    ), patch(
        "app.api.onboarding.generate_mission_text",
        new_callable=AsyncMock,
        return_value="미션 텍스트",
    ):
        ob = await client.post("/api/v1/onboarding", json={**SURVEY, "user_name": "저만족유저"})
    mission_id = ob.json()["mission_id"]

    res = await client.post(
        f"/api/v1/missions/{mission_id}/complete",
        json={"satisfaction": 1},
    )
    assert res.status_code == 200
    assert res.json()["action"] == "re_recommend"
