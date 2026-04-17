import db from '../db';

interface Survey {
  social_pref?: string;
  stress_style?: string;
  activity_level?: string;
  avoid?: string;
  goal?: string;
  physical_limit?: string;
  fitness_level?: string;
  session_duration?: string;
  environment?: string;
  past_sport?: string;
  liked_aspect?: string;
  quit_reason?: string;
  mbti?: string;
  budget?: number;
  user_name?: string;
  age?: number;
  preferred_time?: string;
  [key: string]: unknown;
}

interface Sport {
  id: string;
  name: string;
  cost_level: number;
  injury_risk: number;
  social_level: number;
  indoor: number | boolean;
  tags: string | string[];
  similarity?: number;
}

function getTags(sport: Sport): string[] {
  if (Array.isArray(sport.tags)) return sport.tags;
  try { return JSON.parse(sport.tags as string); } catch { return []; }
}

function surveyToQueryText(survey: Survey): string {
  const parts: string[] = [];
  if (survey.social_pref === '혼자') parts.push('혼자 조용히 집중하는 개인 운동');
  else if (survey.social_pref === '단체') parts.push('여러 사람과 함께하는 단체 스포츠');
  else parts.push('소규모 파트너와 함께하는 운동');

  if (survey.stress_style === '격렬하게') parts.push('격렬하고 에너지 넘치는 유산소 운동');
  else if (survey.stress_style === '창의적으로') parts.push('창의적이고 기술적인 동작이 있는 운동');
  else parts.push('조용하고 집중력이 필요한 운동');

  if (survey.activity_level === '거의 없음') parts.push('입문자 친화 저강도');
  else if (survey.activity_level === '주 3회 이상') parts.push('고강도 체력 단련');
  if (survey.avoid) parts.push(`기피: ${survey.avoid}`);
  return parts.join(' / ');
}

// Turso 네이티브 벡터 검색
export async function vectorSearchSports(survey: Survey, topK = 5): Promise<Sport[]> {
  let queryVec: number[] | null = null;
  try {
    const { pipeline } = await import('@xenova/transformers');
    const extractor = await pipeline(
      'feature-extraction',
      'Xenova/paraphrase-multilingual-MiniLM-L12-v2',
    );
    const queryText = surveyToQueryText(survey);
    const output = await extractor(queryText, { pooling: 'mean', normalize: true });
    queryVec = Array.from(output.data as Float32Array);
  } catch {
    return [];
  }

  if (!queryVec) return [];

  try {
    // Turso vector_distance_cos 사용
    const vecJson = JSON.stringify(queryVec);
    const result = await db.execute({
      sql: `SELECT id, name, cost_level, injury_risk, social_level, indoor, tags,
                   vector_distance_cos(embedding, vector(?)) AS distance
            FROM sports
            WHERE embedding IS NOT NULL
            ORDER BY distance
            LIMIT ?`,
      args: [vecJson, topK],
    });
    return result.rows.map((r) => ({
      ...(r as unknown as Sport),
      similarity: 1 - (r.distance as number),
    }));
  } catch {
    return [];
  }
}

export function filterSportsBySurvey(sports: Sport[], survey: Survey): Sport[] {
  const avoid = (survey.avoid ?? '').toLowerCase();
  const socialPref = survey.social_pref ?? '';
  const budget = (survey.budget as number) ?? 999999;

  const score = (s: Sport): number => {
    let pts = 0;
    const tags = getTags(s).join(' ').toLowerCase();
    const name = s.name.toLowerCase();
    if (avoid && avoid.split(',').some((kw) => name.includes(kw) || tags.includes(kw))) return -999;
    if (socialPref === '혼자' && s.social_level <= 2) pts += 2;
    else if (socialPref === '단체' && s.social_level >= 4) pts += 2;
    else if (socialPref === '소수' && s.social_level >= 2 && s.social_level <= 3) pts += 2;
    if (budget < 30000 && s.cost_level <= 2) pts += 2;
    else if (budget >= 80000 || s.cost_level <= 3) pts += 1;
    return pts;
  };

  return sports
    .filter((s) => score(s) > -999)
    .sort((a, b) => score(b) - score(a))
    .slice(0, 5);
}

export function buildRagContext(sports: Sport[]): string {
  if (!sports.length) return '참고 종목 정보 없음';
  return sports
    .slice(0, 3)
    .map((s) => {
      const sim = s.similarity !== undefined ? `, 유사도=${s.similarity.toFixed(2)}` : '';
      const indoor = s.indoor === 1 || s.indoor === true ? '예' : '아니오';
      return `- ${s.name}: 비용수준=${s.cost_level}/5, 부상위험=${s.injury_risk}/5, 사교성=${s.social_level}/5, 실내=${indoor}, 태그=${getTags(s).join(',')}${sim}`;
    })
    .join('\n');
}

export function buildUserPrompt(survey: Survey, ragSports: Sport[]): string {
  const ragContext = buildRagContext(ragSports);
  const lines: string[] = [];
  if (survey.gender) lines.push(`- 성별: ${survey.gender}`);
  if (survey.mbti) lines.push(`- MBTI: ${survey.mbti}`);
  if (survey.goal) lines.push(`- 운동 목적: ${survey.goal}`);
  if (survey.physical_limit) lines.push(`- 신체 제약: ${survey.physical_limit}`);
  if (survey.fitness_level) lines.push(`- 체력 수준: ${survey.fitness_level}`);
  if (survey.session_duration) lines.push(`- 운동 가능 시간: ${survey.session_duration}`);
  if (survey.environment) lines.push(`- 선호 환경: ${survey.environment}`);
  if (survey.had_exercise !== undefined)
    lines.push(`- 운동 경험: ${survey.had_exercise ? '있음' : '없음'}`);
  if (survey.past_sport) lines.push(`- 이전 운동 종목: ${survey.past_sport}`);
  if (survey.liked_aspect) lines.push(`- 운동에서 좋았던 점: ${survey.liked_aspect}`);
  if (survey.quit_reason) lines.push(`- 운동 중단 이유: ${survey.quit_reason}`);

  return `다음은 사용자 정보입니다:
- 이름: ${survey.user_name}
- 나이: ${survey.age}
${lines.join('\n')}
- 현재 활동량: ${survey.activity_level ?? '거의 없음'}
- 선호 시간대: ${survey.preferred_time ?? '저녁'}
- 사교 성향: ${survey.social_pref ?? '혼자'}
- 스트레스 해소 방식: ${survey.stress_style ?? '조용하게'}
- 월 예산: ${survey.budget ?? 50000}원
- 기피 요소: ${survey.avoid ?? '없음'}

참고할 종목 정보 (벡터 유사도 검색):
${ragContext}`;
}
