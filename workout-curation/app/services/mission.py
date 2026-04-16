"""미션 진행 분기 로직.

만족도 ≥ 4 → 다음 레벨 미션 생성
만족도 ≤ 2 → 재추천 트리거 (다른 종목 플래그)
만족도 3    → 동일 레벨 미션 유지
"""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserMission
from app.services.hermes import generate_mission_text

LEVEL_LABELS = {1: "탐색", 2: "입문", 3: "정착"}
LEVEL_DESCRIPTIONS = {
    1: "체험권/1일권으로 처음 방문만 해보기",
    2: "2-3회 방문, 기본기 배우기",
    3: "월 정기권 결제 또는 동호회 가입",
}


async def process_mission_completion(
    mission: UserMission,
    satisfaction: int,
    db: AsyncSession,
) -> dict:
    """미션 완료 후 만족도에 따라 다음 행동 결정.

    Returns:
        {"action": "next_level" | "retry" | "re_recommend", "mission_id": str | None}
    """
    sport_name = mission.sport_id  # 실제로는 sport 조회 필요, 여기선 미션 텍스트 활용
    user_name = "사용자"

    if satisfaction >= 4:
        next_level = mission.level + 1
        if next_level > 3:
            return {"action": "completed_all", "mission_id": None, "message": "모든 레벨 완료! 정식 회원이 되셨네요 🎉"}

        # 다음 레벨 미션 생성 (Hermes 8B)
        try:
            level_hint = LEVEL_DESCRIPTIONS[next_level]
            mission_text = await generate_mission_text(
                sport=f"이전 미션 종목 (Level {next_level}: {level_hint})",
                facility_name="같은 시설",
                user_name=user_name,
            )
        except Exception:
            mission_text = f"Level {next_level} 미션: {LEVEL_DESCRIPTIONS[next_level]}"

        new_mission = UserMission(
            user_id=mission.user_id,
            sport_id=mission.sport_id,
            facility_id=mission.facility_id,
            mission_text=mission_text,
            level=next_level,
            due_date=date.today() + timedelta(days=14),
            completed=False,
        )
        db.add(new_mission)
        await db.flush()
        return {
            "action": "next_level",
            "mission_id": str(new_mission.id),
            "message": f"좋아요! Level {next_level} 미션이 생성됐어요.",
            "mission_text": mission_text,
        }

    elif satisfaction <= 2:
        # 재추천 트리거 — 프론트에서 /onboarding 재호출 유도
        return {
            "action": "re_recommend",
            "mission_id": None,
            "message": "다른 종목을 찾아드릴게요. 새로운 추천을 받아보세요!",
        }

    else:
        # 만족도 3 — 동일 레벨 재도전
        return {
            "action": "retry",
            "mission_id": str(mission.id),
            "message": "한 번 더 도전해봐요! 다음엔 더 재밌을 거예요.",
        }
