"""POST /api/v1/auth/register, /login — JWT 인증."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.auth import create_access_token, decode_token, hash_password, verify_password

router = APIRouter()
bearer = HTTPBearer()


# ── 스키마 ──────────────────────────────────────────
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    age: int


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str


# ── 엔드포인트 ──────────────────────────────────────
@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # 이메일 중복 확인
    row = await db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": body.email},
    )
    if row.first():
        raise HTTPException(status_code=409, detail="이미 사용 중인 이메일입니다")

    result = await db.execute(
        text("""
            INSERT INTO users (id, name, email, password_hash, age)
            VALUES (gen_random_uuid(), :name, :email, :pw, :age)
            RETURNING id::text
        """),
        {
            "name": body.name,
            "email": body.email,
            "pw": hash_password(body.password),
            "age": body.age,
        },
    )
    user_id = result.scalar()
    await db.commit()

    return TokenResponse(
        access_token=create_access_token(user_id),
        user_id=user_id,
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    row = await db.execute(
        text("SELECT id::text, password_hash FROM users WHERE email = :email"),
        {"email": body.email},
    )
    user = row.mappings().first()
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다")

    return TokenResponse(
        access_token=create_access_token(user["id"]),
        user_id=user["id"],
    )


# ── 의존성: 보호 라우트용 ──────────────────────────
async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> str:
    try:
        return decode_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
