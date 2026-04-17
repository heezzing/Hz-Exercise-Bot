import { NextRequest, NextResponse } from 'next/server';
import db from '@/lib/db';
import { decodeToken, extractBearerToken } from '@/lib/services/auth';

export async function GET(req: NextRequest) {
  try {
    const token = extractBearerToken(req.headers.get('authorization'));
    if (!token) return NextResponse.json({ detail: '인증이 필요합니다.' }, { status: 401 });

    const { sub: userId } = decodeToken(token);
    const result = await db.execute({
      sql: `SELECT m.id, m.mission_text, m.level, m.due_date, m.completed, s.name AS sport_name
            FROM user_missions m
            LEFT JOIN sports s ON s.id = m.sport_id
            WHERE m.user_id = ? AND m.completed = 0
            ORDER BY m.created_at DESC
            LIMIT 1`,
      args: [userId],
    });

    if (!result.rows.length) {
      return NextResponse.json({ detail: '진행 중인 미션이 없습니다.' }, { status: 404 });
    }
    return NextResponse.json(result.rows[0]);
  } catch (e: unknown) {
    return NextResponse.json({ detail: String(e) }, { status: 500 });
  }
}
