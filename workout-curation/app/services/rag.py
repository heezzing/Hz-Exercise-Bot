"""RAG 컨텍스트 빌더 — 설문 응답 → pgvector 코사인 유사도 검색 → Hermes 프롬프트 주입."""

from __future__ import annotations

import functools
import json
from typing import TYPE_CHECKING, Any

from sqlalchemy import text

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


# ── 임베딩 모델 (지연 로딩 싱글톤) ────────────────────────────────────────────

@functools.lru_cache(maxsize=1)
def _get_model():
    """sentence-transformers 모델을 최초 호출 시 한 번만 로드."""
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    except Exception:
        return None


def _encode(text_str: str) -> list[float] | None:
    """텍스트를 384-dim 벡터로 변환. 모델 없으면 None 반환."""
    model = _get_model()
    if model is None:
        return None
    emb = model.encode(text_str, normalize_embeddings=True)
    return emb.tolist()


# ── 설문 → 쿼리 텍스트 ─────────────────────────────────────────────────────────

def _survey_to_query_text(survey: dict) -> str:
    """설문 응답을 임베딩 쿼리용 텍스트로 변환."""
    parts = []
    social = survey.get("social_pref", "")
    if social == "혼자":
        parts.append("혼자 조용히 집중하는 개인 운동")
    elif social == "단체":
        parts.append("여러 사람과 함께하는 단체 스포츠")
    else:
        parts.append("소규모 파트너와 함께하는 운동")

    stress = survey.get("stress_style", "")
    if stress == "격렬하게":
        parts.append("격렬하고 에너지 넘치는 유산소 운동")
    elif stress == "창의적으로":
        parts.append("창의적이고 기술적인 동작이 있는 운동")
    else:
        parts.append("조용하고 집중력이 필요한 운동")

    activity = survey.get("activity_level", "")
    if activity == "거의 없음":
        parts.append("입문자 친화 저강도")
    elif activity == "주 3회 이상":
        parts.append("고강도 체력 단련")

    avoid = survey.get("avoid", "")
    if avoid:
        parts.append(f"기피: {avoid}")

    return " / ".join(parts)


# ── pgvector 유사도 검색 ───────────────────────────────────────────────────────

async def vector_search_sports(
    db: "AsyncSession",
    survey: dict,
    top_k: int = 5,
) -> list[dict]:
    """pgvector 코사인 유사도로 설문에 맞는 종목 top_k 반환.

    임베딩이 없거나 모델 로드 실패 시 빈 리스트 반환 → fallback 사용.
    """
    query_text = _survey_to_query_text(survey)
    query_vec = _encode(query_text)

    if query_vec is None:
        return []

    # embedding IS NOT NULL인 종목만 코사인 거리 순 정렬 (<=>)
    # CAST 사용: asyncpg가 :param:: 구문을 잘못 파싱하는 문제 우회
    vec_str = json.dumps(query_vec)
    result = await db.execute(
        text("""
            SELECT id, name, cost_level, injury_risk, social_level, indoor, tags,
                   1 - (embedding <=> CAST(:qvec AS vector)) AS similarity
            FROM sports
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:qvec AS vector)
            LIMIT :k
        """),
        {"qvec": vec_str, "k": top_k},
    )
    rows = result.mappings().all()
    return [dict(r) for r in rows]


# ── tag-based fallback ─────────────────────────────────────────────────────────

def filter_sports_by_survey(sports: list[dict], survey: dict) -> list[dict]:
    """설문 응답 키워드로 종목 점수화 후 상위 5개 반환 (pgvector 임베딩 없을 때 fallback)."""
    avoid = (survey.get("avoid") or "").lower()
    social_pref = survey.get("social_pref", "")
    budget = survey.get("budget", 999999)

    def score(s: dict) -> int:
        pts = 0
        tags = " ".join(s.get("tags") or []).lower()
        name = s["name"].lower()
        if avoid and any(kw in name or kw in tags for kw in avoid.split(",")):
            return -999
        if social_pref == "혼자" and s["social_level"] <= 2:
            pts += 2
        elif social_pref == "단체" and s["social_level"] >= 4:
            pts += 2
        elif social_pref == "소수" and 2 <= s["social_level"] <= 3:
            pts += 2
        if budget < 30000 and s["cost_level"] <= 2:
            pts += 2
        elif budget >= 80000 or s["cost_level"] <= 3:
            pts += 1
        return pts

    scored = sorted(sports, key=score, reverse=True)
    return [s for s in scored if score(s) > -999][:5]


# ── RAG 컨텍스트 + Hermes 프롬프트 ────────────────────────────────────────────

def build_rag_context(sports: list[dict[str, Any]]) -> str:
    """검색 결과 최대 3개를 텍스트로 변환."""
    lines = []
    for s in sports[:3]:
        sim_str = f", 유사도={s['similarity']:.2f}" if "similarity" in s else ""
        lines.append(
            f"- {s['name']}: 비용수준={s['cost_level']}/5, "
            f"부상위험={s['injury_risk']}/5, "
            f"사교성={s['social_level']}/5, "
            f"실내={'예' if s['indoor'] else '아니오'}, "
            f"태그={','.join(s.get('tags') or [])}{sim_str}"
        )
    return "\n".join(lines) if lines else "참고 종목 정보 없음"


def build_user_prompt(survey: dict[str, Any], rag_sports: list[dict[str, Any]]) -> str:
    """챗봇 수집 정보 + RAG 컨텍스트 → Hermes 추천 프롬프트."""
    rag_context = build_rag_context(rag_sports)

    # 챗봇이 직접 수집한 정보 (있을 때만 표시)
    personal = []
    if survey.get("gender"):
        personal.append(f"- 성별: {survey['gender']}")
    if survey.get("mbti"):
        personal.append(f"- MBTI: {survey['mbti']}")
    if survey.get("goal"):
        personal.append(f"- 운동 목적: {survey['goal']}")
    if survey.get("physical_limit"):
        personal.append(f"- 신체 제약: {survey['physical_limit']}")
    if survey.get("fitness_level"):
        personal.append(f"- 체력 수준: {survey['fitness_level']}")
    if survey.get("session_duration"):
        personal.append(f"- 운동 가능 시간: {survey['session_duration']}")
    if survey.get("environment"):
        personal.append(f"- 선호 환경: {survey['environment']}")
    if survey.get("had_exercise") is not None:
        had = "있음" if survey["had_exercise"] else "없음"
        personal.append(f"- 운동 경험: {had}")
    if survey.get("past_sport"):
        personal.append(f"- 이전 운동 종목: {survey['past_sport']}")
    if survey.get("liked_aspect"):
        personal.append(f"- 운동에서 좋았던 점: {survey['liked_aspect']}")
    if survey.get("quit_reason"):
        personal.append(f"- 운동 중단 이유: {survey['quit_reason']}")
    personal_str = "\n".join(personal) if personal else ""

    return f"""다음은 사용자 정보입니다:
- 이름: {survey['user_name']}
- 나이: {survey['age']}
{personal_str}
- 현재 활동량: {survey['activity_level']}
- 선호 시간대: {survey['preferred_time']}
- 사교 성향: {survey['social_pref']}
- 스트레스 해소 방식: {survey['stress_style']}
- 월 예산: {survey['budget']}원
- 기피 요소: {survey.get('avoid') or '없음'}

참고할 종목 정보 (벡터 유사도 검색):
{rag_context}"""
