import { NextRequest, NextResponse } from 'next/server';
import db from '@/lib/db';
import { hashPassword, createAccessToken } from '@/lib/services/auth';

export async function POST(req: NextRequest) {
  try {
    const { name, age, password } = await req.json();
    if (!name || !age || !password) {
      return NextResponse.json({ detail: '이름, 나이, 비밀번호는 필수입니다.' }, { status: 422 });
    }

    const hashed = await hashPassword(password as string);
    const id = crypto.randomUUID();
    await db.execute({
      sql: `INSERT INTO users (id, name, age, password_hash) VALUES (?, ?, ?, ?)`,
      args: [id, name, age, hashed],
    });

    const token = createAccessToken(id);
    return NextResponse.json({ access_token: token, token_type: 'bearer', user_id: id });
  } catch (e: unknown) {
    const msg = String(e);
    if (msg.includes('UNIQUE')) {
      return NextResponse.json({ detail: '이미 등록된 사용자입니다.' }, { status: 409 });
    }
    return NextResponse.json({ detail: msg }, { status: 500 });
  }
}
