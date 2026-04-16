from pydantic import BaseModel, Field


class SurveyRequest(BaseModel):
    """챗봇 대화로 수집·추론된 사용자 정보."""

    # ── 기본 정보 ──────────────────────────────
    user_name: str = Field(..., description="이름")
    age: int = Field(..., ge=10, le=100)
    gender: str | None = Field(None, description="남성|여성|기타|미응답")

    # ── 운동 목적 (핵심) ───────────────────────
    goal: str | None = Field(None, description="스트레스해소|체중감량|체력유지|사교|성취감")

    # ── 신체 상태 ──────────────────────────────
    physical_limit: str | None = Field(None, description="무릎|허리|어깨|없음")
    fitness_level: str | None = Field(None, description="낮음|보통|양호")

    # ── 시간·환경 ──────────────────────────────
    session_duration: str | None = Field(None, description="30분이내|1시간|1시간이상")
    environment: str | None = Field(None, description="실내|실외|상관없음")

    # ── 운동 경험 ──────────────────────────────
    had_exercise: bool | None = Field(None)
    past_sport: str | None = Field(None, description="이전 운동 종목")
    liked_aspect: str | None = Field(None, description="좋았던 점")
    quit_reason: str | None = Field(None, description="중단 이유")

    # ── MBTI (보조) ────────────────────────────
    mbti: str | None = Field(None)

    # ── Hermes 추론 매핑 필드 (기본값 있음) ─────
    activity_level: str = Field("거의 없음", description="거의 없음|주 1-2회|주 3회 이상")
    preferred_time: str = Field("저녁", description="아침|저녁|주말")
    social_pref: str = Field("혼자", description="혼자|소수|단체")
    stress_style: str = Field("조용하게", description="격렬하게|조용하게|창의적으로")
    budget: int = Field(50000, description="월 예산 (원)")
    experience: str | None = Field(None)
    avoid: str | None = Field(None)
    location_lat: float | None = None
    location_lng: float | None = None


class RecommendationItem(BaseModel):
    sport: str
    reason: str
    difficulty: str
    first_mission: str


class OnboardingResponse(BaseModel):
    user_id: str
    top_pick: str
    encouragement: str
    recommendations: list[RecommendationItem]
    recommendation_id: str
    mission_id: str
    mission_text: str
