"""POST /api/v1/feedback — 만족도 입력 (미션과 독립적인 직접 피드백)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import UserMission
from app.schemas.mission import FeedbackRequest
from app.services.mission import process_mission_completion
import uuid

router = APIRouter()


@router.post("")
async def submit_feedback(body: FeedbackRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserMission).where(UserMission.id == uuid.UUID(body.mission_id))
    )
    mission = result.scalar_one_or_none()
    if not mission:
        raise HTTPException(status_code=404, detail="미션을 찾을 수 없습니다")

    mission.satisfaction = body.satisfaction
    if not mission.completed:
        mission.completed = True

    next_action = await process_mission_completion(mission, body.satisfaction, db)
    await db.commit()

    return {
        "received": True,
        "satisfaction": body.satisfaction,
        **next_action,
    }
