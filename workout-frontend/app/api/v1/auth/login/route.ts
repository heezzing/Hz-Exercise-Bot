import { NextRequest, NextResponse } from 'next/server';
import db from '@/lib/db';
import { verifyPassword, createAccessToken } from '@/lib/services/auth';

export async function POST(req: NextRequest) {
  try {
    const { name, password } = await req.json();
    const result = await db.execute({
      sql: `SELECT id, password_hash FROM users WHERE name = ? LIMIT 1`,
      args: [name],
    });
    if (!result.rows.length) {
      return NextResponse.json({ detail: '사용자를 찾을 수 없습니다.' }, { status: 401 });
    }
    const row = result.rows[0];
    const valid = await verifyPassword(password as string, row.password_hash as string);
    if (!valid) {
      return NextResponse.json({ detail: '비밀번호가 올바르지 않습니다.' }, { status: 401 });
    }
    const token = createAccessToken(row.id as string);
    return NextResponse.json({ access_token: token, token_type: 'bearer', user_id: row.id });
  } catch (e: unknown) {
    return NextResponse.json({ detail: String(e) }, { status: 500 });
  }
}
