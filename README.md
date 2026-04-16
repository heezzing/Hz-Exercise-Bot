# 운동 취향 발굴 서비스

Hermes (NousResearch) + OpenRouter 기반 AI 운동 큐레이션 서비스.  
사용자의 성향과 라이프스타일을 분석해 **"무엇을 시작할지"** 결정해주고, 주변 시설 매칭과 주간 미션을 제공합니다.

---

## 아키텍처

```
Next.js (3000)
    ↓ REST
FastAPI (8000)
    ├── OpenRouter Hermes 70B  →  종목 추천 추론
    ├── OpenRouter Hermes 8B   →  미션 문장 생성
    ├── PostgreSQL + pgvector  →  종목 벡터 검색 (RAG)
    └── PostgreSQL + PostGIS   →  시설 반경 검색
```

---

## 빠른 시작

### 1. 환경변수 설정

```bash
cp workout-curation/.env.example workout-curation/.env
# .env에서 OPENROUTER_API_KEY 입력
```

### 2. 전체 실행 (Docker)

```bash
docker compose up -d
```

### 3. DB 초기화

```bash
# 마이그레이션
docker compose exec backend alembic upgrade head

# 시드 데이터
docker compose exec backend python -m scripts.seed_sports
docker compose exec backend python -m scripts.seed_facilities

# pgvector 임베딩 생성 (paraphrase-multilingual-MiniLM-L12-v2, 384-dim)
docker compose exec backend python -m scripts.embed_sports
```

### 4. 접속

| 서비스 | URL |
|--------|-----|
| 프론트엔드 | http://localhost:3000 |
| API 문서 (Swagger) | http://localhost:8000/docs |

---

## 로컬 개발

```bash
# 백엔드
cd workout-curation
pip install -r requirements.txt
cp .env.example .env         # API 키 입력
docker compose up -d db      # DB만 실행
alembic upgrade head
python3.12 -m scripts.seed_sports
python3.12 -m scripts.seed_facilities
python3.12 -m scripts.embed_sports   # pgvector 임베딩 생성
uvicorn app.main:app --reload

# 프론트엔드
cd workout-frontend
npm install
npm run dev
```

---

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/auth/register` | 회원가입 |
| POST | `/api/v1/auth/login` | 로그인 (JWT 발급) |
| POST | `/api/v1/onboarding` | 설문 제출 → 추천 + 미션 자동 생성 |
| GET | `/api/v1/facilities` | PostGIS 반경 시설 검색 |
| GET | `/api/v1/missions/current` | 현재 미완료 미션 조회 |
| POST | `/api/v1/missions/{id}/complete` | 미션 완료 + 만족도 기반 분기 |
| POST | `/api/v1/feedback` | 만족도 직접 입력 |

---

## 모델 전략 ($5 예산)

| 용도 | 모델 | 비용 |
|------|------|------|
| 종목 추천 추론 | `hermes-3-llama-3.1-70b` | ~$0.001/회 |
| 미션 문장 생성 | `hermes-3-llama-3.1-8b` | ~$0.0001/회 |

→ $5 예산으로 약 **4,000회 이상** 추천 가능

---

## 테스트

```bash
cd workout-curation
python3.12 -m pytest tests/ -v
```

**커버리지:** 인증(3) + 시설검색(3) + 미션플로우(3) = 총 9개 테스트
