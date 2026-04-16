"""JWT 인증 테스트."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    """회원가입 → 로그인 → 토큰 발급 정상 흐름."""
    email = f"test_{uuid.uuid4().hex[:8]}@test.com"

    # 회원가입
    res = await client.post("/api/v1/auth/register", json={
        "name": "테스터", "email": email, "password": "pass1234", "age": 25,
    })
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert "user_id" in body
    token = body["access_token"]

    # 로그인
    res2 = await client.post("/api/v1/auth/login", json={
        "email": email, "password": "pass1234",
    })
    assert res2.status_code == 200
    assert res2.json()["access_token"]  # 토큰 발급 확인


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """잘못된 비밀번호 → 401."""
    email = f"wrong_{uuid.uuid4().hex[:8]}@test.com"
    await client.post("/api/v1/auth/register", json={
        "name": "테스터", "email": email, "password": "correct", "age": 25,
    })
    res = await client.post("/api/v1/auth/login", json={
        "email": email, "password": "wrong",
    })
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_email(client: AsyncClient):
    """이메일 중복 가입 → 409."""
    email = f"dup_{uuid.uuid4().hex[:8]}@test.com"
    payload = {"name": "A", "email": email, "password": "pw", "age": 20}
    await client.post("/api/v1/auth/register", json=payload)
    res = await client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 409
