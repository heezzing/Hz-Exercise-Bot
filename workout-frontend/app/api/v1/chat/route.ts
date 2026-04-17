import { NextRequest, NextResponse } from 'next/server';
import { chatWithHermes, CHAT_SYSTEM_PROMPT } from '@/lib/services/hermes';

export const runtime = 'edge'; // 타임아웃 10s → 30s

export async function POST(req: NextRequest) {
  try {
    const { messages } = await req.json();

    const fullMessages = [
      { role: 'system', content: CHAT_SYSTEM_PROMPT },
      ...messages,
    ];

    const result = await chatWithHermes(fullMessages);
    return NextResponse.json(result);
  } catch (e: unknown) {
    return NextResponse.json({ detail: String(e) }, { status: 500 });
  }
}
