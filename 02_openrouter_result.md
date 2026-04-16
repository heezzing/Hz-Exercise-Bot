# OpenRouter 연결 결과

**일시:** 2026-04-14
**플랫폼:** macOS (darwin 25.4.0), zsh
**Hermes 실행 파일:** `/Users/hk/hermes-agent/venv/bin/hermes`

## 단계별 결과

| # | 단계 | 결과 | 비고 |
|---|------|------|------|
| 1 | `~/.hermes/.env`에서 `OPENROUTER_API_KEY` 확인 | 성공 | 유효한 `sk-or-v1-...` 형식 키 존재 (값 비노출) |
| 2 | `~/.hermes/config.yaml` 현재 provider/model 확인 | 성공 | 기존: `provider: "auto"`, `model.default: "anthropic/claude-opus-4.6"` |
| 3 | `~/.hermes/config.yaml.bak` 백업 | 성공 | 44,950 bytes 백업 생성 |
| 4 | config.yaml 수정 (provider/model/fallback) | 성공 | 아래 "변경 내용" 참조 |
| 5 | YAML 형식 유효성 (hermes가 로드 성공) | 성공 | doctor/chat 실행 시 파싱 오류 없음 |
| 6 | `hermes doctor` OpenRouter ✓ 확인 | 성공 | API Connectivity 섹션 `✓ OpenRouter API` |
| 7 | 연결 테스트 쿼리 | 성공 | `"OpenRouter connected!"` 응답 수신 |

## config.yaml 변경 내용 요약 (API 키 값 제외)

`model:` 섹션 핵심 필드:

- `default`: `"anthropic/claude-opus-4.6"` → `"anthropic/claude-sonnet-4-5"`
- `fallback_model`: (신규 추가) `"nousresearch/hermes-3-llama-3.1-405b:free"`
- `provider`: `"auto"` → `"openrouter"`
- `base_url`: `"https://openrouter.ai/api/v1"` (기존 값 유지)
- API 키: `~/.hermes/.env`의 `OPENROUTER_API_KEY`를 자동 로드 (config.yaml에 평문 키 저장 없음. 주석 처리된 `api_key` 필드는 그대로 둠 — .env 우선)

> 참고: 이 config.yaml 스키마에는 별도의 `openrouter:` 블록이 없고, OpenRouter 관련 설정은 `model:` 섹션 내에서 `provider`/`base_url`/`default`로 표현. 따라서 가이드 예시의 `openrouter.api_key: ${OPENROUTER_API_KEY}`는 이 버전의 기본 구조에서는 불필요하며, `.env`의 `OPENROUTER_API_KEY`가 base_url이 openrouter.ai인 경우 자동 사용됨.

## hermes doctor — OpenRouter 관련 출력

```
◆ Configuration Files
  ✓ ~/.hermes/.env file exists
  ✓ API key or custom endpoint configured
  ✓ ~/.hermes/config.yaml exists
  ✓ Config version up to date (v17)

◆ API Connectivity
  ✓ OpenRouter API

◆ Tool Availability
  ✓ moa           # (기존 ⚠ missing OPENROUTER_API_KEY → 이제 ✓)
  ✓ vision        # OPENROUTER_API_KEY 구성되어 ✓
```

(이전 `01_setup_result.md`의 ⚠ `OpenRouter API (not configured)` / ⚠ `moa (missing OPENROUTER_API_KEY)` / ⚠ `No API key found in ~/.hermes/.env` 항목이 전부 ✓로 전환됨.)

이슈 카운트: 3 → 2 (OpenRouter 관련 이슈 모두 해결, 잔여는 `tinker-atropos 미설치` 및 기타 선택 API 키 부재).

## 연결 테스트 결과

명령:
```bash
/Users/hk/hermes-agent/venv/bin/hermes chat -q "Say 'OpenRouter connected!'" -Q
```

(주: 이 버전의 Hermes에는 `hermes run` 서브커맨드가 없음. `hermes chat -q <query> -Q`가 비대화형 단일 쿼리 실행 방식.)

출력:
```
╭─ ⚕ Hermes ─────────────────────────────────────────────────────────────────
OpenRouter connected!

session_id: 20260414_151103_5f79a9
```

응답 정상 수신 → `anthropic/claude-sonnet-4-5` 경유 OpenRouter 엔드포인트 연결 확인.

## 보안

- API 키는 `~/.hermes/.env`에만 저장, config.yaml 및 본 결과 문서에는 값 미포함.
- config.yaml.bak 백업 생성 완료 (`~/.hermes/config.yaml.bak`).

## 실패한 단계

**없음.** 모든 단계 정상 완료.
