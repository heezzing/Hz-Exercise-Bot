"""RAG 서비스 유닛 테스트 — 임베딩 모델 mock."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.rag import (
    _survey_to_query_text,
    build_rag_context,
    build_user_prompt,
    filter_sports_by_survey,
)

SAMPLE_SPORTS = [
    {"name": "클라이밍", "cost_level": 3, "injury_risk": 2, "social_level": 2, "indoor": True, "tags": ["근력", "집중력"]},
    {"name": "수영",     "cost_level": 2, "injury_risk": 1, "social_level": 1, "indoor": True, "tags": ["유산소", "저충격"]},
    {"name": "테니스",   "cost_level": 3, "injury_risk": 2, "social_level": 3, "indoor": False, "tags": ["사교"]},
    {"name": "러닝",     "cost_level": 1, "injury_risk": 2, "social_level": 1, "indoor": False, "tags": ["유산소", "자유"]},
]


class TestSurveyToQueryText:
    def test_solo_quiet(self):
        survey = {"social_pref": "혼자", "stress_style": "조용하게", "activity_level": "거의 없음", "avoid": ""}
        text = _survey_to_query_text(survey)
        assert "혼자" in text
        assert "조용" in text
        assert "입문자" in text

    def test_group_intense(self):
        survey = {"social_pref": "단체", "stress_style": "격렬하게", "activity_level": "주 3회 이상", "avoid": ""}
        text = _survey_to_query_text(survey)
        assert "단체" in text
        assert "고강도" in text

    def test_avoid_included(self):
        survey = {"social_pref": "혼자", "stress_style": "조용하게", "activity_level": "거의 없음", "avoid": "물"}
        text = _survey_to_query_text(survey)
        assert "물" in text


class TestFilterSportsBySurvey:
    def test_solo_prefers_low_social(self):
        survey = {"social_pref": "혼자", "budget": 50000, "avoid": ""}
        result = filter_sports_by_survey(SAMPLE_SPORTS, survey)
        names = [r["name"] for r in result]
        # social_level 1~2인 종목이 앞에 와야 함
        assert "테니스" not in names[:2]

    def test_avoid_keyword_excluded(self):
        survey = {"social_pref": "혼자", "budget": 50000, "avoid": "수영"}
        result = filter_sports_by_survey(SAMPLE_SPORTS, survey)
        assert all(r["name"] != "수영" for r in result)

    def test_low_budget_prefers_cheap(self):
        survey = {"social_pref": "혼자", "budget": 20000, "avoid": ""}
        result = filter_sports_by_survey(SAMPLE_SPORTS, survey)
        # cost_level 1~2인 수영, 러닝이 우선 추천돼야 함
        cheap = [r for r in result if r["cost_level"] <= 2]
        assert len(cheap) > 0
        assert result[0]["cost_level"] <= 2


class TestBuildRagContext:
    def test_top_3_only(self):
        sports = SAMPLE_SPORTS + [
            {"name": "배드민턴", "cost_level": 1, "injury_risk": 2, "social_level": 3, "indoor": True, "tags": []}
        ]
        context = build_rag_context(sports)
        lines = [l for l in context.split("\n") if l.startswith("-")]
        assert len(lines) == 3

    def test_similarity_shown_when_present(self):
        sports = [{**SAMPLE_SPORTS[0], "similarity": 0.85}]
        context = build_rag_context(sports)
        assert "유사도=0.85" in context

    def test_empty_returns_fallback(self):
        assert build_rag_context([]) == "참고 종목 정보 없음"


class TestBuildUserPrompt:
    def test_contains_survey_fields(self):
        survey = {
            "age": 30, "activity_level": "주 1-2회", "preferred_time": "아침",
            "social_pref": "소수", "stress_style": "창의적으로",
            "budget": 80000, "experience": "없음", "avoid": "없음",
        }
        prompt = build_user_prompt(survey, SAMPLE_SPORTS[:2])
        assert "30" in prompt
        assert "주 1-2회" in prompt
        assert "클라이밍" in prompt


@pytest.mark.asyncio
async def test_vector_search_fallback_when_no_embedding(client):
    """임베딩 없는 종목 → vector_search_sports 빈 리스트 반환."""
    from unittest.mock import AsyncMock, patch

    from app.services.rag import vector_search_sports

    survey = {"social_pref": "혼자", "stress_style": "조용하게", "activity_level": "거의 없음", "avoid": ""}

    # 임베딩 인코드를 None으로 강제 → fallback 경로
    with patch("app.services.rag._encode", return_value=None):
        mock_db = AsyncMock()
        result = await vector_search_sports(mock_db, survey)
    assert result == []
