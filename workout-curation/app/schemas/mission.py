from datetime import date

from pydantic import BaseModel, Field


class MissionResponse(BaseModel):
    id: str
    mission_text: str
    level: int
    due_date: date | None
    completed: bool
    satisfaction: int | None


class CompleteMissionRequest(BaseModel):
    satisfaction: int = Field(..., ge=1, le=5, description="만족도 1~5")


class CompleteMissionResponse(BaseModel):
    mission_id: str
    satisfaction: int
    action: str           # next_level | retry | re_recommend | completed_all
    message: str
    next_mission_id: str | None = None
    next_mission_text: str | None = None


class FeedbackRequest(BaseModel):
    mission_id: str
    satisfaction: int = Field(..., ge=1, le=5)
