import { NextRequest, NextResponse } from 'next/server';
import pool from '@/lib/db';
import { hashPassword, createAccessToken } from '@/lib/services/auth';

export async function POST(req: NextRequest) {
  try {
    const { name, age, password } = await req.json();
    if (!name || !age || !password) {
      return NextResponse.json({ detail: '이름, 나이, 비밀번호는 필수입니다.' }, { status: 422 });
    }

    const hashed = await hashPassword(password);
    const { rows } = await pool.query(
      `INSERT INTO users (name, age, password_hash) VALUES ($1, $2, $3) RETURNING id`,
      [name, age, hashed],
    );
    const userId = rows[0].id as string;
    const token = createAccessToken(userId);

    return NextResponse.json({ access_token: token, token_type: 'bearer', user_id: userId });
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    if (msg.includes('unique') || msg.includes('duplicate')) {
      return NextResponse.json({ detail: '이미 등록된 사용자입니다.' }, { status: 409 });
    }
    return NextResponse.json({ detail: msg }, { status: 500 });
  }
}
