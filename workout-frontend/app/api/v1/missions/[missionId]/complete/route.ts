import { NextRequest, NextResponse } from 'next/server';
import { processMissionCompletion } from '@/lib/services/mission';

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ missionId: string }> },
) {
  try {
    const { missionId } = await params;
    const { satisfaction } = await req.json();

    if (typeof satisfaction !== 'number' || satisfaction < 1 || satisfaction > 5) {
      return NextResponse.json({ detail: 'satisfaction은 1~5 숫자여야 합니다.' }, { status: 422 });
    }

    const result = await processMissionCompletion(missionId, satisfaction);
    return NextResponse.json(result);
  } catch (e: unknown) {
    const msg = String(e);
    if (msg.includes('not found')) return NextResponse.json({ detail: msg }, { status: 404 });
    return NextResponse.json({ detail: msg }, { status: 500 });
  }
}
