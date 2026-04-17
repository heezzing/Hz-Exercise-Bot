import { NextRequest, NextResponse } from 'next/server';
import pool from '@/lib/db';
import { verifyPassword, createAccessToken } from '@/lib/services/auth';

export async function POST(req: NextRequest) {
  try {
    const { name, password } = await req.json();
    const { rows } = await pool.query(
      `SELECT id, password_hash FROM users WHERE name = $1 LIMIT 1`,
      [name],
    );
    if (!rows.length) {
      return NextResponse.json({ detail: '사용자를 찾을 수 없습니다.' }, { status: 401 });
    }
    const valid = await verifyPassword(password, rows[0].password_hash as string);
    if (!valid) {
      return NextResponse.json({ detail: '비밀번호가 올바르지 않습니다.' }, { status: 401 });
    }
    const token = createAccessToken(rows[0].id as string);
    return NextResponse.json({ access_token: token, token_type: 'bearer', user_id: rows[0].id });
  } catch (e: unknown) {
    return NextResponse.json({ detail: String(e) }, { status: 500 });
  }
}
