"""종목 임베딩 생성 스크립트 — paraphrase-multilingual-MiniLM-L12-v2 (384-dim).

실행: python3.12 -m scripts.embed_sports
"""

import asyncio
import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings


def _build_sport_text(name: str, description: str, tags: list[str]) -> str:
    """임베딩용 종목 텍스트 조합."""
    tag_str = ", ".join(tags) if tags else ""
    return f"{name}: {description} 태그: {tag_str}"


async def embed():
    from sentence_transformers import SentenceTransformer

    print("모델 로딩 중… (첫 실행 시 다운로드)")
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(
            text("SELECT id, name, description, tags FROM sports")
        )
        sports = result.mappings().all()

        if not sports:
            print("종목 데이터 없음. seed_sports 먼저 실행하세요.")
            return

        texts = [
            _build_sport_text(s["name"], s["description"] or "", s["tags"] or [])
            for s in sports
        ]

        print(f"{len(sports)}개 종목 임베딩 생성 중…")
        embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)

        for sport, emb in zip(sports, embeddings):
            emb_list = emb.tolist()
            await session.execute(
                text("UPDATE sports SET embedding = :emb WHERE id = :id"),
                {"emb": json.dumps(emb_list), "id": str(sport["id"])},
            )

        await session.commit()

    print(f"✓ {len(sports)}개 종목 임베딩 저장 완료 (dim=384)")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(embed())
