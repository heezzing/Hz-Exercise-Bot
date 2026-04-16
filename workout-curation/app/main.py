import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat, facilities, feedback, missions, onboarding
from app.scheduler import start_scheduler, stop_scheduler

# sentence-transformers가 TF/JAX를 로드하지 않도록 설정
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("USE_JAX", "0")


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    # 임베딩 모델 미리 로드 (첫 요청 지연 방지)
    from app.services.rag import _get_model
    _get_model()
    yield
    stop_scheduler()


app = FastAPI(
    title="운동 큐레이션 서비스",
    description="Hermes + OpenRouter 기반 운동 취향 발굴 AI 서비스",
    version="0.4.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,       prefix="/api/v1/auth",       tags=["auth"])
app.include_router(chat.router,       prefix="/api/v1/chat",       tags=["chat"])
app.include_router(onboarding.router, prefix="/api/v1/onboarding", tags=["onboarding"])
app.include_router(facilities.router, prefix="/api/v1/facilities",  tags=["facilities"])
app.include_router(missions.router,   prefix="/api/v1/missions",    tags=["missions"])
app.include_router(feedback.router,   prefix="/api/v1/feedback",    tags=["feedback"])


@app.get("/health")
async def health():
    return {"status": "ok"}
