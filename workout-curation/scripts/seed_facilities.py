"""서울 주요 운동 시설 시드 데이터 (PostGIS POINT 좌표 포함).

실행: python3.12 -m scripts.seed_facilities
"""

import asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy import text
from app.config import settings

# (종목명, 시설명, 주소, 위도, 경도, 1회 비용, 평점, 전화)
FACILITIES = [
    # 클라이밍
    ("클라이밍", "더클라이밍 강남점",    "서울 강남구 테헤란로 427",     37.5087, 127.0633, 18000, 4.7, "02-555-0001"),
    ("클라이밍", "클라이밍파크 홍대점",  "서울 마포구 양화로 160",       37.5567, 126.9239, 15000, 4.5, "02-333-0002"),
    ("클라이밍", "살리다클라이밍 신촌",  "서울 서대문구 신촌로 83",      37.5556, 126.9368, 14000, 4.4, "02-312-0003"),
    ("클라이밍", "더클라이밍 합정점",    "서울 마포구 합정동 372",       37.5500, 126.9148, 16000, 4.6, "02-333-0004"),
    ("클라이밍", "클라이밍 성수점",      "서울 성동구 성수이로 78",      37.5445, 127.0559, 17000, 4.8, "02-444-0005"),

    # 수영
    ("수영", "강남구청 수영장",          "서울 강남구 삼성로 212",       37.5172, 127.0473, 3000,  4.3, "02-3423-5800"),
    ("수영", "잠실실내수영장",           "서울 송파구 올림픽로 25",      37.5142, 127.0721, 3500,  4.4, "02-2147-2800"),
    ("수영", "마포구민체육센터 수영장",  "서울 마포구 월드컵북로 400",   37.5709, 126.9027, 3000,  4.2, "02-3153-9700"),
    ("수영", "서울시민체육관 수영장",    "서울 강남구 남부순환로 2477",  37.4813, 127.0449, 2500,  4.1, "02-2226-0201"),

    # 요가
    ("요가", "코어요가 강남",            "서울 강남구 역삼로 160",       37.5004, 127.0368, 20000, 4.8, "02-555-1001"),
    ("요가", "하늘요가 홍대",            "서울 마포구 어울마당로 65",    37.5570, 126.9246, 18000, 4.6, "02-322-1002"),
    ("요가", "요가원 이태원",            "서울 용산구 이태원로 177",     37.5344, 126.9940, 22000, 4.7, "02-795-1003"),
    ("요가", "선릉요가클럽",             "서울 강남구 선릉로 433",       37.5046, 127.0487, 19000, 4.5, "02-566-1004"),

    # 테니스
    ("테니스", "올림픽공원 테니스장",    "서울 송파구 올림픽로 424",     37.5213, 127.1220, 10000, 4.4, "02-2154-8100"),
    ("테니스", "한강 망원 테니스장",     "서울 마포구 마포나루길 467",   37.5582, 126.8987, 8000,  4.2, "02-3153-0001"),
    ("테니스", "뚝섬 테니스장",          "서울 광진구 자양로 290",       37.5473, 127.0657, 9000,  4.3, "02-450-1900"),

    # 러닝
    ("러닝", "한강공원 반포 러닝트랙",   "서울 서초구 신반포로11길 40",  37.5112, 126.9980, 0,     4.9, None),
    ("러닝", "한강공원 여의도 러닝트랙", "서울 영등포구 여의동로 330",   37.5283, 126.9336, 0,     4.8, None),
    ("러닝", "올림픽공원 러닝코스",      "서울 송파구 올림픽로 424",     37.5215, 127.1215, 0,     4.7, None),

    # 배드민턴
    ("배드민턴", "종로체육관 배드민턴",  "서울 종로구 창경궁로 124",     37.5743, 126.9998, 5000,  4.2, "02-765-3456"),
    ("배드민턴", "강서 배드민턴클럽",    "서울 강서구 공항대로 484",     37.5603, 126.8279, 6000,  4.3, "02-2668-1234"),

    # 필라테스
    ("필라테스", "바디앤필라테스 강남",  "서울 강남구 도산대로 201",     37.5263, 127.0388, 50000, 4.9, "02-547-2001"),
    ("필라테스", "코어필라테스 마포",    "서울 마포구 백범로 35",        37.5495, 126.9480, 45000, 4.7, "02-712-2002"),

    # 자전거
    ("자전거", "한강 자전거 대여소 뚝섬","서울 광진구 자양로 257",       37.5446, 127.0665, 3000,  4.5, "02-3780-0504"),
    ("자전거", "한강 자전거 대여소 반포","서울 서초구 올림픽대로 2085",  37.5121, 126.9985, 3000,  4.4, "02-3780-0521"),
]


async def seed():
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # 종목 ID 조회
        result = await session.execute(text("SELECT id, name FROM sports"))
        sport_map = {row.name: str(row.id) for row in result}

        inserted = 0
        skipped = 0
        for sport_name, facility_name, address, lat, lng, cost, rating, phone in FACILITIES:
            sport_id = sport_map.get(sport_name)
            if not sport_id:
                print(f"  ⚠ 종목 없음: {sport_name}")
                skipped += 1
                continue

            await session.execute(text("""
                INSERT INTO facilities
                    (id, name, sport_id, address, location, cost_per_session, rating, phone)
                VALUES (
                    gen_random_uuid(),
                    :name,
                    CAST(:sport_id AS uuid),
                    :address,
                    ST_SetSRID(ST_MakePoint(:lng, :lat), 4326),
                    :cost,
                    :rating,
                    :phone
                )
                ON CONFLICT DO NOTHING
            """), {
                "name": facility_name,
                "sport_id": sport_id,
                "address": address,
                "lat": lat,
                "lng": lng,
                "cost": cost,
                "rating": rating,
                "phone": phone,
            })
            inserted += 1

        await session.commit()

    print(f"✓ 시설 {inserted}개 삽입 완료 (건너뜀: {skipped}개)")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
