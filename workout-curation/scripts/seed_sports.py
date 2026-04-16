"""초기 운동 종목 데이터 시드 스크립트.

실행: python -m scripts.seed_sports
"""

import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

SPORTS_SEED = [
    {
        "id": str(uuid.uuid4()),
        "name": "클라이밍",
        "cost_level": 3,
        "injury_risk": 2,
        "social_level": 2,
        "space_required": False,
        "indoor": True,
        "tags": ["근력", "집중력", "성취감"],
        "description": "실내 암벽 등반. 혼자 집중하면서도 성취감을 느낄 수 있어 스트레스 해소에 탁월.",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "수영",
        "cost_level": 2,
        "injury_risk": 1,
        "social_level": 1,
        "space_required": True,
        "indoor": True,
        "tags": ["유산소", "전신운동", "저충격"],
        "description": "전신 유산소 운동. 관절 부담 없이 꾸준히 할 수 있는 입문자 친화 종목.",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "테니스",
        "cost_level": 3,
        "injury_risk": 2,
        "social_level": 3,
        "space_required": True,
        "indoor": False,
        "tags": ["유산소", "반응속도", "사교"],
        "description": "파트너와 함께 즐기는 라켓 스포츠. 사교성과 경쟁심을 동시에 충족.",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "요가",
        "cost_level": 2,
        "injury_risk": 1,
        "social_level": 2,
        "space_required": False,
        "indoor": True,
        "tags": ["유연성", "멘탈", "호흡"],
        "description": "유연성과 정신 집중을 동시에 키우는 종목. 스트레스 해소에 특히 효과적.",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "러닝",
        "cost_level": 1,
        "injury_risk": 2,
        "social_level": 1,
        "space_required": False,
        "indoor": False,
        "tags": ["유산소", "자유", "멘탈"],
        "description": "가장 진입 장벽이 낮은 운동. 장비 없이 언제든 시작 가능.",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "배드민턴",
        "cost_level": 1,
        "injury_risk": 2,
        "social_level": 3,
        "space_required": True,
        "indoor": True,
        "tags": ["유산소", "반응속도", "사교"],
        "description": "저렴한 비용으로 친구나 동료와 즐길 수 있는 실내 라켓 스포츠.",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "필라테스",
        "cost_level": 4,
        "injury_risk": 1,
        "social_level": 2,
        "space_required": False,
        "indoor": True,
        "tags": ["코어", "자세교정", "유연성"],
        "description": "코어 근력과 자세 교정에 특화된 운동. 재활 목적으로도 많이 활용.",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "자전거",
        "cost_level": 3,
        "injury_risk": 2,
        "social_level": 2,
        "space_required": False,
        "indoor": False,
        "tags": ["유산소", "자유", "야외"],
        "description": "도시 이동과 운동을 겸할 수 있는 실용적 종목. 야외 활동을 즐기는 사람에게 적합.",
    },
]


async def seed():
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        from sqlalchemy import text
        for sport in SPORTS_SEED:
            await session.execute(
                text("""
                    INSERT INTO sports (id, name, cost_level, injury_risk, social_level,
                                       space_required, indoor, tags, description)
                    VALUES (:id, :name, :cost_level, :injury_risk, :social_level,
                            :space_required, :indoor, :tags, :description)
                    ON CONFLICT (name) DO NOTHING
                """),
                {**sport, "tags": sport["tags"]},
            )
        await session.commit()
    print(f"✓ {len(SPORTS_SEED)}개 종목 시드 완료")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
