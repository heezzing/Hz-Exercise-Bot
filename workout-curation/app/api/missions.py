"""미션 관련 엔드포인트."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import UserMission
from app.schemas.mission import CompleteMissionRequest, CompleteMissionResponse, MissionResponse
from app.services.mission import process_mission_completion

router = APIRouter()


@router.get("/current", response_model=list[MissionResponse])
async def get_current_missions(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(UserMission)
        .where(UserMission.user_id == uuid.UUID(user_id))
        .where(UserMission.completed == False)
        .order_by(UserMission.created_at.desc())
        .limit(5)
    )
    result = await db.execute(stmt)
    missions = result.scalars().all()
    return [
        MissionResponse(
            id=str(m.id),
            mission_text=m.mission_text,
            level=m.level,
            due_date=m.due_date,
            completed=m.completed,
            satisfaction=m.satisfaction,
        )
        for m in missions
    ]


@router.post("/{mission_id}/complete", response_model=CompleteMissionResponse)
async def complete_mission(
    mission_id: str,
    body: CompleteMissionRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserMission).where(UserMission.id == uuid.UUID(mission_id))
    )
    mission = result.scalar_one_or_none()
    if not mission:
        raise HTTPException(status_code=404, detail="미션을 찾을 수 없습니다")
    if mission.completed:
        raise HTTPException(status_code=400, detail="이미 완료된 미션입니다")

    # 완료 처리
    mission.completed = True
    mission.satisfaction = body.satisfaction

    # 만족도 기반 다음 행동 분기
    next_action = await process_mission_completion(mission, body.satisfaction, db)
    await db.commit()

    return CompleteMissionResponse(
        mission_id=mission_id,
        satisfaction=body.satisfaction,
        action=next_action["action"],
        message=next_action["message"],
        next_mission_id=next_action.get("mission_id"),
        next_mission_text=next_action.get("mission_text"),
    )
