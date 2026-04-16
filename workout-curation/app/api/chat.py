"""POST /api/v1/chat — Hermes 챗봇 대화 엔드포인트.

이름·나이·성별·MBTI·운동 이력·중단 이유를 대화로 수집 후
survey_complete: true 와 함께 추출된 설문 데이터를 반환한다.
"""

import json
import logging

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

_HEADERS = {
    "Authorization": f"Bearer {settings.openrouter_api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://workout-curation.app",
}

CHAT_SYSTEM_PROMPT = """당신은 친절한 운동 추천 AI 챗봇입니다.
사용자와 자연스러운 한국어 대화를 통해 아래 순서대로 정보를 수집하세요.

━━━ 수집 순서 ━━━

[1단계] 기본 정보
 - 이름, 나이

[2단계] 운동 목적 (가장 중요)
 - "운동을 통해 가장 얻고 싶은 게 뭐예요?" 라고 물어보세요
 - 보기: 스트레스 해소 / 체중 감량 / 체력·건강 유지 / 새로운 사람 만나기 / 성취감·도전

[3단계] 신체 상태
 - 불편한 관절·부위가 있는지 (무릎/허리/어깨/없음)
 - 현재 체력 수준 (낮음: 계단 오르면 숨참 / 보통: 30분 걷기 가능 / 양호: 가끔 운동 가능)

[4단계] 시간·예산
 - 운동 가능 시간대 (평일 아침 / 평일 저녁 / 주말)
 - 한 번에 쓸 수 있는 시간 (30분 이내 / 1시간 / 1시간 이상)
 - 월 운동 예산 (3만원 이하 / 5~10만원 / 10만원 이상)

[5단계] 환경·분위기 선호
 - 실내 vs 실외 선호
 - 혼자 / 1~2명과 함께 / 여러 사람과 활기차게

[6단계] 운동 경험
 - 이전에 운동한 적 있는지
 - 있다면: 어떤 운동이었는지, 좋았던 점과 그만둔 이유
 - 없다면 이 질문 건너뜀

[7단계] MBTI (선택)
 - "혹시 MBTI 아세요? 모르셔도 괜찮아요!" 라고 가볍게 물어보세요

━━━ 대화 규칙 ━━━
- 한 번에 하나의 질문만 하세요
- 친근하고 따뜻한 말투 유지
- 사용자 답변에 짧게 공감한 뒤 다음 질문으로 자연스럽게 넘어가세요
- 모든 단계 완료 시 survey_complete: true 설정

━━━ 응답 형식 (반드시 JSON만 출력) ━━━

수집 중:
{"reply": "응답 텍스트", "survey_complete": false}

완료 시:
{
  "reply": "완벽해요! 지금까지 알려주신 내용으로 딱 맞는 운동을 찾아드릴게요 🔍",
  "survey_complete": true,
  "survey_data": {
    "user_name": "이름",
    "age": 나이(숫자),
    "gender": "남성|여성|기타|미응답",
    "mbti": "MBTI 또는 모름",
    "goal": "스트레스해소|체중감량|체력유지|사교|성취감",
    "physical_limit": "무릎|허리|어깨|없음",
    "fitness_level": "낮음|보통|양호",
    "session_duration": "30분이내|1시간|1시간이상",
    "environment": "실내|실외|상관없음",
    "had_exercise": true|false,
    "past_sport": "이전 운동 종목 또는 null",
    "liked_aspect": "좋았던 점 또는 null",
    "quit_reason": "그만둔 이유 또는 null",
    "activity_level": "거의 없음|주 1-2회|주 3회 이상",
    "preferred_time": "아침|저녁|주말",
    "social_pref": "혼자|소수|단체",
    "stress_style": "격렬하게|조용하게|창의적으로",
    "budget": 50000,
    "experience": "경험 요약 1~2문장",
    "avoid": "신체 제약 기반 기피 요소"
  }
}

━━━ 필드 추론 규칙 ━━━

goal → stress_style:
 - 스트레스해소·체중감량 → "격렬하게"
 - 체력유지·성취감 → "조용하게" 또는 "격렬하게" (fitness_level 고려)
 - 사교 → "창의적으로"

goal → social_pref (환경 응답으로 덮어씀):
 - 사교 목적 → "단체"
 - 혼자 선호 → "혼자"
 - 1~2명 → "소수"

physical_limit → avoid:
 - 무릎 → "달리기,점프,계단"
 - 허리 → "무거운 중량,고충격"
 - 어깨 → "수영,테니스"
 - 없음 → ""

fitness_level + session_duration → activity_level:
 - 낮음 또는 30분이내 → "거의 없음"
 - 보통 또는 1시간 → "주 1-2회"
 - 양호 또는 1시간이상 → "주 3회 이상"

budget (월):
 - 3만원 이하 → 30000
 - 5~10만원 → 60000
 - 10만원 이상 → 120000

preferred_time:
 - 평일 아침 → "아침"
 - 평일 저녁 → "저녁"
 - 주말 → "주말"
 - J형 MBTI → "아침", P형 → "주말" (시간대 응답이 없을 때만 적용)

quit_reason 보정:
 - "지루", "반복" → stress_style = "창의적으로"
 - "비용", "돈" → budget = 30000
 - "시간", "바빠" → preferred_time = "주말"

liked_aspect 활용:
 - "사람들", "친구" 언급 → social_pref = "단체"
 - "혼자", "집중" 언급 → social_pref = "혼자"
 - "성취", "기록" 언급 → stress_style = "격렬하게"
"""


class ChatMessage(BaseModel):
    role: str   # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


class ChatResponse(BaseModel):
    reply: str
    survey_complete: bool = False
    survey_data: dict | None = None


@router.post("", response_model=ChatResponse)
async def chat(body: ChatRequest):
    messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
    for m in body.messages:
        messages.append({"role": m.role, "content": m.content})

    payload = {
        "model": settings.hermes_heavy,
        "messages": messages,
        "max_tokens": 600,
        "temperature": 0.5,
        "response_format": {"type": "json_object"},
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(settings.openrouter_base_url, json=payload, headers=_HEADERS)
            res.raise_for_status()
        raw = res.json()
        content = raw["choices"][0]["message"]["content"]
        parsed = json.loads(content)

        return ChatResponse(
            reply=parsed.get("reply", "..."),
            survey_complete=parsed.get("survey_complete", False),
            survey_data=parsed.get("survey_data"),
        )

    except json.JSONDecodeError:
        # JSON 파싱 실패 시 텍스트 그대로 반환
        return ChatResponse(reply=content, survey_complete=False)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Hermes API 오류: {e.response.status_code}")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Hermes 응답 타임아웃")
