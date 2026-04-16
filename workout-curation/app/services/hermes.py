"""OpenRouter Hermes 추론 서비스."""

import json
import logging

import httpx

from app.config import settings
from app.services.prompts import MISSION_SYSTEM_PROMPT, get_active_prompt

logger = logging.getLogger(__name__)

MAX_TOKENS = {
    "recommendation": 800,
    "mission_text": 200,
    "encouragement": 100,
}

_HEADERS = {
    "Authorization": f"Bearer {settings.openrouter_api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://workout-curation.app",
}


async def _call(
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_tokens: int,
) -> dict:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            settings.openrouter_base_url,
            json=payload,
            headers=_HEADERS,
        )
        response.raise_for_status()
        return response.json()


def _parse_recommendation(raw: dict) -> dict:
    """OpenRouter 응답에서 추천 JSON 추출 및 검증."""
    try:
        content = raw["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        assert "recommendations" in parsed, "recommendations 키 누락"
        assert "top_pick" in parsed, "top_pick 키 누락"
        assert len(parsed["recommendations"]) >= 1, "추천 결과 없음"
        return parsed

    except (KeyError, IndexError) as e:
        logger.error("OpenRouter 응답 구조 오류: %s", e)
        raise ValueError("Hermes API 응답 형식 오류") from e

    except json.JSONDecodeError as e:
        logger.error("JSON 파싱 실패: %s", e)
        content = raw["choices"][0]["message"]["content"]
        start, end = content.find("{"), content.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(content[start:end])
        raise ValueError("JSON 파싱 불가") from e

    except AssertionError as e:
        logger.error("응답 유효성 검사 실패: %s", e)
        raise ValueError(str(e)) from e


async def get_sport_recommendations(user_prompt: str) -> dict:
    """설문 + RAG 컨텍스트 → Hermes 70B → 종목 추천."""
    prompt_cfg = get_active_prompt()
    try:
        raw = await _call(
            system_prompt=prompt_cfg["system"],
            user_prompt=user_prompt,
            model=settings.hermes_heavy,
            max_tokens=prompt_cfg["max_tokens"],
        )
        return _parse_recommendation(raw)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise RuntimeError("OpenRouter 요청 한도 초과") from e
        raise RuntimeError(f"API 오류 {e.response.status_code}") from e
    except httpx.TimeoutException:
        raise RuntimeError("Hermes API 응답 타임아웃 (30s)")


async def generate_mission_text(sport: str, facility_name: str, user_name: str) -> str:
    """미션 문장 생성 — Hermes 8B (비용 절약)."""
    user_prompt = f"{user_name}님을 위한 미션: {facility_name}에서 {sport} 체험. 친근한 한국어 1문장으로."
    try:
        raw = await _call(
            system_prompt=MISSION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=settings.hermes_light,
            max_tokens=MAX_TOKENS["mission_text"],
        )
        return raw["choices"][0]["message"]["content"].strip()
    except httpx.TimeoutException:
        return f"{facility_name}에서 {sport} 첫 체험에 도전해보세요!"
