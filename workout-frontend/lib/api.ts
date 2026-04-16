const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8001";

export interface Recommendation {
  sport: string;
  reason: string;
  difficulty: string;
  first_mission: string;
}

export interface OnboardingResult {
  user_id: string;
  top_pick: string;
  encouragement: string;
  recommendations: Recommendation[];
  recommendation_id: string;
  mission_id: string;
  mission_text: string;
}

/** 챗봇이 수집·추론한 사용자 정보 */
export interface ChatSurveyData {
  user_name: string;
  age: number;
  gender?: string;
  mbti?: string;
  // 운동 목적 및 신체 상태
  goal?: string;
  physical_limit?: string;
  fitness_level?: string;
  session_duration?: string;
  environment?: string;
  // 운동 경험
  had_exercise?: boolean;
  past_sport?: string;
  liked_aspect?: string;
  quit_reason?: string | null;
  // Hermes가 위 정보로부터 추론한 매핑 필드
  activity_level: string;
  preferred_time: string;
  social_pref: string;
  stress_style: string;
  budget: number;
  experience?: string;
  avoid?: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  reply: string;
  survey_complete: boolean;
  survey_data?: ChatSurveyData;
}

export async function sendChatMessage(messages: ChatMessage[]): Promise<ChatResponse> {
  const res = await fetch(`${BASE}/api/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function submitSurvey(data: ChatSurveyData): Promise<OnboardingResult> {
  const res = await fetch(`${BASE}/api/v1/onboarding`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export interface Facility {
  id: string;
  name: string;
  address: string | null;
  cost_per_session: number | null;
  phone: string | null;
  rating: number | null;
  distance_m: number | null;
}

export async function searchFacilities(
  sport: string,
  lat: number,
  lng: number,
  radiusM = 5000
): Promise<Facility[]> {
  const params = new URLSearchParams({
    sport,
    lat: String(lat),
    lng: String(lng),
    radius_m: String(radiusM),
  });
  const res = await fetch(`${BASE}/api/v1/facilities?${params}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function completeMission(
  missionId: string,
  satisfaction: number
): Promise<{ action: string; message: string; next_mission_id?: string; next_mission_text?: string }> {
  const res = await fetch(`${BASE}/api/v1/missions/${missionId}/complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ satisfaction }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
