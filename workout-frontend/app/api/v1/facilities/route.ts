import { NextRequest, NextResponse } from 'next/server';
import db from '@/lib/db';

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const sport = searchParams.get('sport');
    const lat = parseFloat(searchParams.get('lat') ?? '');
    const lng = parseFloat(searchParams.get('lng') ?? '');
    const radiusM = parseFloat(searchParams.get('radius_m') ?? '5000');

    if (!sport || isNaN(lat) || isNaN(lng)) {
      return NextResponse.json({ detail: 'sport, lat, lng는 필수입니다.' }, { status: 422 });
    }

    // Haversine 공식으로 거리 계산 (PostGIS 대체)
    const result = await db.execute({
      sql: `SELECT f.id, f.name, f.address, f.phone, f.rating, f.cost_per_session,
                   6371000 * 2 * asin(sqrt(
                     (sin((f.lat - ?) * 3.14159265358979 / 360.0)) *
                     (sin((f.lat - ?) * 3.14159265358979 / 360.0)) +
                     cos(f.lat * 3.14159265358979 / 180.0) *
                     cos(? * 3.14159265358979 / 180.0) *
                     (sin((f.lng - ?) * 3.14159265358979 / 360.0)) *
                     (sin((f.lng - ?) * 3.14159265358979 / 360.0))
                   )) AS distance_m
            FROM facilities f
            JOIN sports s ON s.id = f.sport_id
            WHERE s.name = ?
            HAVING distance_m <= ?
            ORDER BY distance_m
            LIMIT 20`,
      args: [lat, lat, lat, lng, lng, sport, radiusM],
    });

    return NextResponse.json(result.rows);
  } catch (e: unknown) {
    console.error('[facilities error]', e);
    return NextResponse.json({ detail: String(e) }, { status: 500 });
  }
}
