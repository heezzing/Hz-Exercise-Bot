"use client";

import { useEffect, useRef, useState } from "react";
import {
  sendChatMessage, submitSurvey, completeMission, searchFacilities,
  ChatMessage, ChatSurveyData, OnboardingResult, Facility,
} from "@/lib/api";

type Step = "chat" | "result" | "facilities" | "mission_done";

function StarRating({ rating }: { rating: number | null }) {
  if (!rating) return <span className="text-gray-400 text-xs">평점 없음</span>;
  return (
    <span className="text-yellow-500 text-xs font-semibold">
      {"★".repeat(Math.round(rating))}{"☆".repeat(5 - Math.round(rating))} {rating.toFixed(1)}
    </span>
  );
}

function TypingDots() {
  return (
    <div className="flex items-center gap-1 px-4 py-3">
      {[0, 1, 2].map(i => (
        <span key={i} className="w-2 h-2 bg-orange-400 rounded-full animate-bounce"
          style={{ animationDelay: `${i * 0.15}s` }} />
      ))}
    </div>
  );
}

export default function Home() {
  const [step, setStep] = useState<Step>("chat");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OnboardingResult | null>(null);
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [locError, setLocError] = useState("");
  const [satisfaction, setSatisfaction] = useState(0);
  const [nextAction, setNextAction] = useState<{ message: string; next_mission_text?: string } | null>(null);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  /* 첫 인사 */
  useEffect(() => {
    setTyping(true);
    const timer = setTimeout(() => {
      setMessages([{
        role: "assistant",
        content: "안녕하세요! 저는 당신에게 딱 맞는 운동을 찾아드리는 AI예요 🏃\n\n먼저 간단한 질문 몇 가지를 드릴게요. 이름이 어떻게 되세요?",
      }]);
      setTyping(false);
    }, 800);
    return () => clearTimeout(timer);
  }, []);

  /* 새 메시지 오면 스크롤 */
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  /* ── 메시지 전송 ─────────────────────────── */
  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");

    const newMessages: ChatMessage[] = [...messages, { role: "user", content: text }];
    setMessages(newMessages);
    setTyping(true);
    setError("");

    try {
      const res = await sendChatMessage(newMessages);
      setTyping(false);
      setMessages(prev => [...prev, { role: "assistant", content: res.reply }]);

      if (res.survey_complete && res.survey_data) {
        /* 설문 완료 → 추천 요청 (누락 필드 기본값 보완) */
        setLoading(true);
        // 기본값 위에 Hermes 응답을 덮어씌움 (누락 필드 안전 처리)
        const defaults = { activity_level: "거의 없음", preferred_time: "저녁", social_pref: "혼자", stress_style: "조용하게", budget: 50000 };
        const payload = Object.assign(defaults, res.survey_data) as ChatSurveyData;
        try {
          const ob = await submitSurvey(payload);
          setResult(ob);
          setStep("result");
        } catch {
          setError("추천을 가져오지 못했어요. 잠시 후 다시 시도해주세요.");
        } finally {
          setLoading(false);
        }
      }
    } catch {
      setTyping(false);
      setError("응답을 받지 못했어요. 다시 시도해주세요.");
    }
  };

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  };

  /* ── 시설 탐색 ───────────────────────────── */
  const handleFindFacilities = () => {
    if (!result) return;
    setLocError("");
    if (!navigator.geolocation) { setLocError("위치 서비스를 지원하지 않는 브라우저예요."); return; }
    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const data = await searchFacilities(result.top_pick, pos.coords.latitude, pos.coords.longitude);
          setFacilities(data);
          setStep("facilities");
        } catch { setLocError("시설 검색 중 오류가 발생했어요."); }
        finally { setLoading(false); }
      },
      () => { setLocError("위치 권한이 거부됐어요."); setLoading(false); },
      { timeout: 8000 },
    );
  };

  /* ── 미션 완료 ───────────────────────────── */
  const handleComplete = async () => {
    if (!result || satisfaction === 0) return;
    setLoading(true);
    try {
      const res = await completeMission(result.mission_id, satisfaction);
      setNextAction(res);
      setStep("mission_done");
    } catch { setError("미션 완료 처리 중 오류가 발생했어요."); }
    finally { setLoading(false); }
  };

  const reset = () => {
    setStep("chat"); setMessages([]); setResult(null); setFacilities([]);
    setSatisfaction(0); setNextAction(null); setError("");
    setTyping(true);
    setTimeout(() => {
      setMessages([{ role: "assistant", content: "안녕하세요! 저는 당신에게 딱 맞는 운동을 찾아드리는 AI예요 🏃\n\n먼저 간단한 질문 몇 가지를 드릴게요. 이름이 어떻게 되세요?" }]);
      setTyping(false);
    }, 600);
  };

  /* ══════════════════════════════════════════
     화면 1 — 챗봇 대화
  ══════════════════════════════════════════ */
  if (step === "chat") return (
    <main className="min-h-screen bg-gradient-to-br from-orange-50 to-amber-100 flex flex-col items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-xl w-full max-w-md flex flex-col" style={{ height: "85vh" }}>

        {/* 헤더 */}
        <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-3">
          <div className="w-10 h-10 bg-orange-500 rounded-full flex items-center justify-center text-white text-lg">🤖</div>
          <div>
            <p className="font-bold text-gray-800 text-sm">운동 추천 AI</p>
            <p className="text-xs text-green-500">● 온라인</p>
          </div>
        </div>

        {/* 메시지 영역 */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              {m.role === "assistant" && (
                <div className="w-7 h-7 bg-orange-100 rounded-full flex items-center justify-center text-sm mr-2 mt-1 flex-shrink-0">🤖</div>
              )}
              <div className={`max-w-[78%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-line ${
                m.role === "user"
                  ? "bg-orange-500 text-white rounded-br-sm"
                  : "bg-gray-100 text-gray-800 rounded-bl-sm"
              }`}>
                {m.content}
              </div>
            </div>
          ))}

          {typing && (
            <div className="flex justify-start">
              <div className="w-7 h-7 bg-orange-100 rounded-full flex items-center justify-center text-sm mr-2 mt-1">🤖</div>
              <div className="bg-gray-100 rounded-2xl rounded-bl-sm">
                <TypingDots />
              </div>
            </div>
          )}

          {loading && (
            <div className="flex justify-start">
              <div className="w-7 h-7 bg-orange-100 rounded-full flex items-center justify-center text-sm mr-2 mt-1">🤖</div>
              <div className="bg-orange-50 border border-orange-200 rounded-2xl rounded-bl-sm px-4 py-3 text-sm text-orange-700">
                Hermes가 최적의 운동을 분석 중이에요 ✨
                <TypingDots />
              </div>
            </div>
          )}

          {error && <p className="text-center text-xs text-red-500">{error}</p>}
          <div ref={bottomRef} />
        </div>

        {/* 입력창 */}
        <div className="px-4 py-3 border-t border-gray-100">
          <div className="flex gap-2">
            <input
              className="flex-1 border border-gray-200 rounded-2xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-orange-300"
              placeholder="메시지를 입력하세요…"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={onKey}
              disabled={loading || typing}
            />
            <button
              onClick={send}
              disabled={loading || typing || !input.trim()}
              className="w-10 h-10 bg-orange-500 hover:bg-orange-600 text-white rounded-full flex items-center justify-center transition disabled:opacity-40"
            >
              ➤
            </button>
          </div>
        </div>
      </div>
    </main>
  );

  /* ══════════════════════════════════════════
     화면 2 — 추천 결과
  ══════════════════════════════════════════ */
  if (step === "result" && result) return (
    <main className="min-h-screen bg-gradient-to-br from-orange-50 to-amber-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-xl w-full max-w-md p-8 space-y-5">
        <div className="text-center">
          <div className="text-5xl mb-2">🎯</div>
          <h2 className="text-xl font-bold text-gray-800">추천 완료!</h2>
          <p className="text-orange-500 font-semibold mt-1 text-sm">"{result.encouragement}"</p>
        </div>

        <div className="space-y-3">
          {result.recommendations.map((rec, i) => (
            <div key={i} className={`rounded-2xl p-4 border-2 ${i === 0 ? "border-orange-400 bg-orange-50" : "border-gray-100"}`}>
              <div className="flex items-center gap-2 mb-1">
                {i === 0 && <span className="text-xs bg-orange-400 text-white px-2 py-0.5 rounded-full font-bold">TOP PICK</span>}
                <span className="font-bold text-gray-800">{rec.sport}</span>
                <span className="text-xs text-gray-400 ml-auto">{rec.difficulty}</span>
              </div>
              <p className="text-sm text-gray-600">{rec.reason}</p>
            </div>
          ))}
        </div>

        <div className="bg-amber-50 rounded-2xl p-4 border border-amber-200">
          <p className="text-xs font-bold text-amber-700 mb-1">🎯 이번 주 미션</p>
          <p className="text-sm text-gray-700">{result.mission_text}</p>
        </div>

        {locError && <p className="text-red-500 text-xs text-center">{locError}</p>}

        <div className="space-y-2">
          <button onClick={handleFindFacilities} disabled={loading}
            className="w-full py-3 bg-blue-500 hover:bg-blue-600 text-white font-bold rounded-2xl transition disabled:opacity-50">
            {loading ? "위치 확인 중…" : `📍 내 주변 ${result.top_pick} 시설 찾기`}
          </button>
          <button onClick={() => setStep("mission_done" as any)}
            className="w-full py-2 text-gray-400 text-sm hover:text-gray-600 transition">
            시설 건너뛰고 미션 완료하기 →
          </button>
        </div>
      </div>
    </main>
  );

  /* ══════════════════════════════════════════
     화면 3 — 주변 시설
  ══════════════════════════════════════════ */
  if (step === "facilities" && result) return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-xl w-full max-w-md p-8 space-y-4">
        <div className="text-center">
          <div className="text-4xl mb-2">📍</div>
          <h2 className="text-xl font-bold text-gray-800">주변 {result.top_pick} 시설</h2>
          <p className="text-sm text-gray-500 mt-1">반경 5km 이내 · 거리순</p>
        </div>

        {facilities.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <p className="text-3xl mb-2">🔍</p>
            <p className="text-sm">반경 5km 내 시설이 없어요.</p>
          </div>
        ) : (
          <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
            {facilities.map((f, i) => (
              <div key={f.id} className={`rounded-2xl p-4 border-2 ${i === 0 ? "border-blue-400 bg-blue-50" : "border-gray-100"}`}>
                <div className="flex items-start justify-between mb-1">
                  <div>
                    {i === 0 && <span className="text-xs bg-blue-400 text-white px-2 py-0.5 rounded-full font-bold mr-1">가장 가까움</span>}
                    <span className="font-bold text-gray-800 text-sm">{f.name}</span>
                  </div>
                  <span className="text-xs font-bold text-blue-600 ml-2">
                    {f.distance_m ? `${(f.distance_m / 1000).toFixed(1)}km` : ""}
                  </span>
                </div>
                {f.address && <p className="text-xs text-gray-500 mb-1">{f.address}</p>}
                <div className="flex items-center justify-between">
                  <StarRating rating={f.rating} />
                  <span className="text-xs text-gray-600">
                    {f.cost_per_session != null ? (f.cost_per_session === 0 ? "무료" : `${f.cost_per_session.toLocaleString()}원/회`) : ""}
                  </span>
                </div>
                {f.phone && <a href={`tel:${f.phone}`} className="text-xs text-blue-500 hover:underline mt-1 block">📞 {f.phone}</a>}
              </div>
            ))}
          </div>
        )}

        <div className="space-y-2 pt-2">
          <p className="text-sm text-center text-gray-500">미션 완료 후 만족도를 알려주세요</p>
          <div className="flex justify-center gap-2">
            {[1, 2, 3, 4, 5].map(n => (
              <button key={n} onClick={() => setSatisfaction(n)}
                className={`w-10 h-10 rounded-full font-bold text-sm transition ${satisfaction === n ? "bg-orange-500 text-white scale-110 shadow-md" : "bg-gray-100 hover:bg-orange-100 text-gray-600"}`}>
                {n}
              </button>
            ))}
          </div>
          <button onClick={handleComplete} disabled={loading || satisfaction === 0}
            className="w-full py-3 bg-green-500 hover:bg-green-600 text-white font-bold rounded-2xl transition disabled:opacity-50">
            {loading ? "처리 중…" : "미션 완료! ✅"}
          </button>
          {error && <p className="text-red-500 text-sm text-center">{error}</p>}
        </div>
      </div>
    </main>
  );

  /* ══════════════════════════════════════════
     화면 4 — 미션 완료
  ══════════════════════════════════════════ */
  return (
    <main className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-xl w-full max-w-md p-8 text-center space-y-5">
        <div className="text-6xl">🏆</div>
        <h2 className="text-2xl font-bold text-gray-800">미션 완료!</h2>
        <p className="text-gray-600">{nextAction?.message ?? "수고했어요!"}</p>
        {nextAction?.next_mission_text && (
          <div className="bg-green-50 rounded-2xl p-4 border border-green-200 text-left">
            <p className="text-xs font-bold text-green-700 mb-1">📋 다음 미션</p>
            <p className="text-sm text-gray-700">{nextAction.next_mission_text}</p>
          </div>
        )}
        <button onClick={reset}
          className="w-full py-3 bg-orange-500 hover:bg-orange-600 text-white font-bold rounded-2xl transition">
          처음부터 다시 →
        </button>
      </div>
    </main>
  );
}
