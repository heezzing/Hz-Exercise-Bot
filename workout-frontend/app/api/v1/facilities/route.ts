import { NextRequest, NextResponse } from 'next/server';
import pool from '@/lib/db';

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

    const { rows } = await pool.query(
      `SELECT f.id, f.name, f.address, f.phone, f.rating, f.cost_per_session,
              ST_Distance(
                f.location::geography,
                ST_SetSRID(ST_MakePoint($2, $3), 4326)::geography
              ) AS distance_m
       FROM facilities f
       JOIN sports s ON s.id = f.sport_id
       WHERE s.name ILIKE $1
         AND ST_DWithin(
               f.location::geography,
               ST_SetSRID(ST_MakePoint($2, $3), 4326)::geography,
               $4
             )
       ORDER BY distance_m
       LIMIT 20`,
      [sport, lng, lat, radiusM],
    );

    return NextResponse.json(rows);
  } catch (e: unknown) {
    console.error('[facilities error]', e);
    return NextResponse.json({ detail: String(e) }, { status: 500 });
  }
}
