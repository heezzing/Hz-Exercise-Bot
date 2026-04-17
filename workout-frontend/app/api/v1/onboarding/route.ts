import { NextRequest, NextResponse } from 'next/server';
import pool from '@/lib/db';
import { getSportRecommendations } from '@/lib/services/hermes';
import { vectorSearchSports, filterSportsBySurvey, buildUserPrompt } from '@/lib/services/rag';

export async function POST(req: NextRequest) {
  try {
    const survey = await req.json();

    if (!survey.user_name || !survey.age) {
      return NextResponse.json({ detail: 'user_name과 age는 필수입니다.' }, { status: 422 });
    }

    // 1. 사용자 저장
    const { rows: userRows } = await pool.query(
      `INSERT INTO users (name, age, location_lat, location_lng, lifestyle_vector)
       VALUES ($1, $2, $3, $4, $5) RETURNING id`,
      [
        survey.user_name,
        survey.age,
        survey.location_lat ?? null,
        survey.location_lng ?? null,
        JSON.stringify(survey),
      ],
    );
    const userId = userRows[0].id as string;

    // 2. RAG 검색 (pgvector → tag-based fallback)
    let ragSports = await vectorSearchSports(survey);
    if (!ragSports.length) {
      const { rows: allSports } = await pool.query(
        `SELECT id, name, cost_level, injury_risk, social_level, indoor, tags FROM sports`,
      );
      ragSports = filterSportsBySurvey(allSports, survey);
    }

    // 3. Hermes 추천
    const userPrompt = buildUserPrompt(survey, ragSports);
    const hermes = await getSportRecommendations(userPrompt);

    // 4. 추천 저장
    const topSportRow = await pool.query(
      `SELECT id FROM sports WHERE name ILIKE $1 LIMIT 1`,
      [hermes.top_pick],
    );
    const topSportId: string | null = topSportRow.rows[0]?.id ?? null;

    const { rows: recRows } = await pool.query(
      `INSERT INTO recommendations (user_id, sport_ids, hermes_reasoning)
       VALUES ($1, $2, $3) RETURNING id`,
      [userId, topSportId ? [topSportId] : [], hermes.encouragement],
    );
    const recommendationId = recRows[0].id as string;

    // 5. 레벨1 미션 생성
    const firstMission =
      hermes.recommendations[0]?.first_mission ?? `${hermes.top_pick} 체험권으로 첫 방문해보세요!`;

    const dueDate = new Date();
    dueDate.setDate(dueDate.getDate() + 7);

    const { rows: missionRows } = await pool.query(
      `INSERT INTO user_missions (user_id, sport_id, mission_text, level, due_date)
       VALUES ($1, $2, $3, 1, $4) RETURNING id`,
      [userId, topSportId, firstMission, dueDate],
    );
    const missionId = missionRows[0].id as string;

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
