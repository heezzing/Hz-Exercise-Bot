"""POST /api/v1/onboarding — 설문 제출 → Hermes 추론 → 추천 + Level 1 미션 자동 생성."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Recommendation, User, UserMission
from app.schemas.onboarding import OnboardingResponse, SurveyRequest
from app.services.hermes import generate_mission_text, get_sport_recommendations
from app.services.rag import build_user_prompt, filter_sports_by_survey, vector_search_sports

router = APIRouter()


async def _get_rag_sports(db: AsyncSession, survey: dict) -> list[dict]:
    """pgvector 코사인 유사도 검색 → 실패 시 tag-based fallback."""
    # 1. 벡터 검색 시도
    vec_results = await vector_search_sports(db, survey, top_k=5)
    if vec_results:
        return vec_results

    # 2. Fallback: tag-based 점수 필터링
    result = await db.execute(
        text("SELECT id, name, cost_level, injury_risk, social_level, indoor, tags FROM sports")
    )
    rows = result.mappings().all()
    all_sports = [dict(r) for r in rows]
    return filter_sports_by_survey(all_sports, survey)


@router.post("", response_model=OnboardingResponse)
async def onboarding(body: SurveyRequest, db: AsyncSession = Depends(get_db)):
    # 1. 사용자 생성
    user = User(
        name=body.user_name,
        age=body.age,
        location_lat=body.location_lat,
        location_lng=body.location_lng,
        lifestyle_vector=body.model_dump(exclude={"location_lat", "location_lng"}),
    )
    db.add(user)
    await db.flush()

    # 2. RAG 컨텍스트 조회 (설문 기반 필터링)
    survey_dict = body.model_dump()
    rag_sports = await _get_rag_sports(db, survey_dict)

    # 3. Hermes 70B 추론
    user_prompt = build_user_prompt(survey_dict, rag_sports)
    try:
        result = await get_sport_recommendations(user_prompt)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # 4. 추천 결과 저장
    rec = Recommendation(
        user_id=user.id,
        sport_ids=[],
        hermes_reasoning=result.get("encouragement", ""),
    )
    db.add(rec)

    # 5. top_pick 종목의 Level 1 미션 자동 생성 (Hermes 8B)
    top_pick = result["top_pick"]
    top_item = next(
        (r for r in result["recommendations"] if r["sport"] == top_pick),
        result["recommendations"][0],
    )

    # Hermes가 생성한 first_mission을 기본으로 사용, 8B로 재생성 시도
    try:
        mission_text = await generate_mission_text(
            sport=top_pick,
            facility_name="근처 시설",
            user_name=body.user_name,
        )
    except Exception:
        mission_text = top_item["first_mission"]

    mission = UserMission(
        user_id=user.id,
        sport_id=None,  # sport UUID 매핑은 후속 작업
        mission_text=mission_text,
        level=1,
        due_date=date.today() + timedelta(days=7),  # 1주일 내 완료 목표
        completed=False,
    )
    db.add(mission)
    await db.commit()

    return OnboardingResponse(
        user_id=str(user.id),
        top_pick=top_pick,
        encouragement=result["encouragement"],
        recommendations=result["recommendations"],
        recommendation_id=str(rec.id),
        mission_id=str(mission.id),
        mission_text=mission_text,
    )
