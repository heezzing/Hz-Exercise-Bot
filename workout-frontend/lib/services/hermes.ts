const BASE_URL = 'https://openrouter.ai/api/v1/chat/completions';
const HEADERS = {
  'Authorization': `Bearer ${process.env.OPENROUTER_API_KEY}`,
  'Content-Type': 'application/json',
  'HTTP-Referer': 'https://workout-curation.app',
};

const HEAVY = process.env.HERMES_HEAVY ?? 'nousresearch/hermes-3-llama-3.1-70b';
const LIGHT = process.env.HERMES_LIGHT ?? 'nousresearch/hermes-3-llama-3.1-8b';

const RECOMMENDATION_SYSTEM_PROMPT = `당신은 운동 큐레이션 전문가입니다.
사용자의 성향, MBTI, 운동 이력, 라이프스타일을 분석하여 최적의 운동 종목을 추천합니다.
반드시 아래 JSON 형식으로만 응답하세요.

{
  "recommendations": [
    {
      "sport": "종목명",
      "reason": "이 사람에게 맞는 이유 (2-3문장, 목표·신체상태·이력 반영)",
      "difficulty": "입문자도 괜찮음 | 약간의 체력 필요 | 도전적",
      "first_mission": "이번 주말 할 수 있는 구체적인 미션 (1문장)"
    }
  ],
  "top_pick": "종목명",
  "encouragement": "사용자에게 전하는 한 마디 (1문장)"
}`;

export const CHAT_SYSTEM_PROMPT = `당신은 친절한 운동 추천 AI 챗봇입니다.
사용자와 자연스러운 한국어 대화를 통해 아래 순서대로 정보를 수집하세요.

━━━ 수집 순서 ━━━

[1단계] 기본 정보
 - 이름, 나이

[2단계] 운동 목적 (가장 중요)
 - "운동을 통해 가장 얻고 싶은 게 뭐예요?" 라고 물어보세요
 - 보기: 스트레스 해소 / 체중 감량 / 체력·건강 유지 / 새로운 사람 만나기 / 성취감·도전

[3단계] 신체 상태
 - 불편한 관절·부위가 있는지 (무릎/허리/어깨/없음)
 - 현재 체력 수준 (낮음: 계단 오르면 숨참 / 보통: 30분 걷기 가능 / 양호: 가끔 운동 가능)

[4단계] 시간·예산
 - 운동 가능 시간대 (평일 아침 / 평일 저녁 / 주말)
 - 한 번에 쓸 수 있는 시간 (30분 이내 / 1시간 / 1시간 이상)
 - 월 운동 예산 (3만원 이하 / 5~10만원 / 10만원 이상)

[5단계] 환경·분위기 선호
 - 실내 vs 실외 선호
 - 혼자 / 1~2명과 함께 / 여러 사람과 활기차게

[6단계] 운동 경험
 - 이전에 운동한 적 있는지
 - 있다면: 어떤 운동이었는지, 좋았던 점과 그만둔 이유
 - 없다면 이 질문 건너뜀

[7단계] MBTI (선택)
 - "혹시 MBTI 아세요? 모르셔도 괜찮아요!" 라고 가볍게 물어보세요

━━━ 대화 규칙 ━━━
- 한 번에 하나의 질문만 하세요
- 친근하고 따뜻한 말투 유지
- 사용자 답변에 짧게 공감한 뒤 다음 질문으로 자연스럽게 넘어가세요
- 모든 단계 완료 시 survey_complete: true 설정

━━━ 응답 형식 (반드시 JSON만 출력) ━━━

수집 중:
{"reply": "응답 텍스트", "survey_complete": false}

완료 시:
{
  "reply": "완벽해요! 지금까지 알려주신 내용으로 딱 맞는 운동을 찾아드릴게요 🔍",
  "survey_complete": true,
  "survey_data": {
    "user_name": "이름",
    "age": 나이(숫자),
    "gender": "남성|여성|기타|미응답",
    "mbti": "MBTI 또는 모름",
    "goal": "스트레스해소|체중감량|체력유지|사교|성취감",
    "physical_limit": "무릎|허리|어깨|없음",
    "fitness_level": "낮음|보통|양호",
    "session_duration": "30분이내|1시간|1시간이상",
    "environment": "실내|실외|상관없음",
    "had_exercise": true,
    "past_sport": "이전 운동 종목 또는 null",
    "liked_aspect": "좋았던 점 또는 null",
    "quit_reason": "그만둔 이유 또는 null",
    "activity_level": "거의 없음|주 1-2회|주 3회 이상",
    "preferred_time": "아침|저녁|주말",
    "social_pref": "혼자|소수|단체",
    "stress_style": "격렬하게|조용하게|창의적으로",
    "budget": 50000,
    "experience": "경험 요약 1~2문장",
    "avoid": "신체 제약 기반 기피 요소"
  }
}`;

async function callOpenRouter(
  messages: { role: string; content: string }[],
  model: string,
  maxTokens: number,
): Promise<string> {
  const res = await fetch(BASE_URL, {
    method: 'POST',
    headers: HEADERS,
    body: JSON.stringify({
      model,
      messages,
      max_tokens: maxTokens,
      temperature: 0.3,
      response_format: { type: 'json_object' },
    }),
  });
  if (!res.ok) throw new Error(`OpenRouter error: ${res.status}`);
  const data = await res.json();
  return data.choices[0].message.content as string;
}

export async function getSportRecommendations(userPrompt: string): Promise<{
  recommendations: { sport: string; reason: string; difficulty: string; first_mission: string }[];
  top_pick: string;
  encouragement: string;
}> {
  const content = await callOpenRouter(
    [
      { role: 'system', content: RECOMMENDATION_SYSTEM_PROMPT },
      { role: 'user', content: userPrompt },
    ],
    HEAVY,
    800,
  );
  return JSON.parse(content);
}

export async function generateMissionText(
  sport: string,
  level: number,
  userName: string,
): Promise<string> {
  const prompt = `운동 종목: ${sport}, 레벨: ${level}, 사용자 이름: ${userName}
레벨별 미션:
- 레벨1: 체험권/1일권으로 첫 방문하는 미션
- 레벨2: 2-3회 방문해서 기본기를 배우는 미션
- 레벨3: 월 정기권 or 동호회 가입하는 미션
위 레벨에 맞는 구체적인 미션 문장 1개만 JSON으로 반환: {"mission": "미션 문장"}`;

  const content = await callOpenRouter(
    [{ role: 'user', content: prompt }],
    LIGHT,
    200,
  );
  const parsed = JSON.parse(content);
  return parsed.mission as string;
}

export async function chatWithHermes(
  messages: { role: string; content: string }[],
): Promise<{ reply: string; survey_complete: boolean; survey_data?: Record<string, unknown> }> {
  const res = await fetch(BASE_URL, {
    method: 'POST',
    headers: HEADERS,
    body: JSON.stringify({
      model: LIGHT,
      messages,
      max_tokens: 600,
      temperature: 0.5,
      response_format: { type: 'json_object' },
    }),
  });
  if (!res.ok) throw new Error(`OpenRouter error: ${res.status}`);
  const data = await res.json();
  const content = data.choices[0].message.content as string;
  const parsed = JSON.parse(content);
  return {
    reply: parsed.reply ?? '...',
    survey_complete: parsed.survey_complete ?? false,
    survey_data: parsed.survey_data,
  };
}
