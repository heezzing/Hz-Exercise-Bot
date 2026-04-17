import { NextRequest, NextResponse } from 'next/server';
import db from '@/lib/db';
import { getSportRecommendations } from '@/lib/services/hermes';

export const maxDuration = 60;
import { vectorSearchSports, filterSportsBySurvey, buildUserPrompt } from '@/lib/services/rag';

export async function POST(req: NextRequest) {
  try {
    const survey = await req.json();
    if (!survey.user_name || !survey.age) {
      return NextResponse.json({ detail: 'user_name과 age는 필수입니다.' }, { status: 422 });
    }

    // 1. 사용자 저장
    const userId = crypto.randomUUID();
    await db.execute({
      sql: `INSERT INTO users (id, name, age, location_lat, location_lng, lifestyle_vector)
            VALUES (?, ?, ?, ?, ?, ?)`,
      args: [
        userId,
        survey.user_name,
        survey.age,
        survey.location_lat ?? null,
        survey.location_lng ?? null,
        JSON.stringify(survey),
      ],
    });

    // 2. RAG 검색 (벡터 → tag-based fallback)
    let ragSports = await vectorSearchSports(survey);
    if (!ragSports.length) {
      const all = await db.execute(`SELECT id, name, cost_level, injury_risk, social_level, indoor, tags FROM sports`);
      ragSports = filterSportsBySurvey(all.rows as never, survey);
    }

    // 3. Hermes 추천
    const userPrompt = buildUserPrompt(survey, ragSports);
    const hermes = await getSportRecommendations(userPrompt);

    // 4. top_pick 스포츠 ID 조회
    const sportRes = await db.execute({
      sql: `SELECT id FROM sports WHERE name = ? LIMIT 1`,
      args: [hermes.top_pick],
    });
    const topSportId: string | null = (sportRes.rows[0]?.id as string) ?? null;

    // 5. 추천 저장
    const recommendationId = crypto.randomUUID();
    await db.execute({
      sql: `INSERT INTO recommendations (id, user_id, sport_ids, hermes_reasoning)
            VALUES (?, ?, ?, ?)`,
      args: [recommendationId, userId, JSON.stringify(topSportId ? [topSportId] : []), hermes.encouragement],
    });

    // 6. 레벨1 미션 생성
    const firstMission =
      hermes.recommendations[0]?.first_mission ?? `${hermes.top_pick} 체험권으로 첫 방문해보세요!`;
    const dueDate = new Date();
    dueDate.setDate(dueDate.getDate() + 7);
    const missionId = crypto.randomUUID();
    await db.execute({
      sql: `INSERT INTO user_missions (id, user_id, sport_id, mission_text, level, due_date)
            VALUES (?, ?, ?, ?, 1, ?)`,
      args: [missionId, userId, topSportId, firstMission, dueDate.toISOString().split('T')[0]],
    });

    return NextResponse.json({
      user_id: userId,
      top_pick: hermes.top_pick,
      encouragement: hermes.encouragement,
      recommendations: hermes.recommendations,
      recommendation_id: recommendationId,
      mission_id: missionId,
      mission_text: firstMission,
    });
  } catch (e: unknown) {
    console.error('[onboarding error]', e);
    return NextResponse.json({ detail: String(e) }, { status: 500 });
  }
}
