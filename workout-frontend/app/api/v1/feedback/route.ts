import { NextRequest, NextResponse } from 'next/server';
import { processMissionCompletion } from '@/lib/services/mission';

export async function POST(req: NextRequest) {
  try {
    const { mission_id, satisfaction } = await req.json();
    if (!mission_id || typeof satisfaction !== 'number') {
      return NextResponse.json({ detail: 'mission_id와 satisfaction은 필수입니다.' }, { status: 422 });
    }
    const result = await processMissionCompletion(mission_id as string, satisfaction);
    return NextResponse.json(result);
  } catch (e: unknown) {
    return NextResponse.json({ detail: String(e) }, { status: 500 });
  }
}
