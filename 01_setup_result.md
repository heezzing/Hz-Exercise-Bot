# Hermes Agent 설치 결과

**일시:** 2026-04-14
**플랫폼:** macOS (darwin 25.4.0), zsh
**설치 경로:** `~/hermes-agent`
**설정 경로:** `~/.hermes`

## 단계별 결과

| # | 단계 | 결과 | 비고 |
|---|------|------|------|
| 1 | `git clone --recurse-submodules` | 성공 | 서브모듈 `tinker-atropos` 체크아웃 완료 (65f084e) |
| 2 | `uv venv venv --python 3.11` | 성공 | CPython 3.11.13 사용 |
| 3 | `uv pip install -e ".[all]"` | 성공 | 모든 extras 설치 완료 (5분 이내) |
| 4 | `npm install` | 성공 | 476 packages, 0 vulnerabilities, `agent-browser` 준비 완료 |
| 5 | `mkdir -p ~/.hermes/{...}` | 성공 | cron, sessions, logs, memories, skills, pairing, hooks, image_cache, audio_cache 생성 |
| 6 | config.yaml 생성 | 성공 (대체) | `config.example.yaml`은 저장소에 존재하지 않음. 대신 `cli-config.yaml.example`을 `~/.hermes/config.yaml`으로 복사 (44950 bytes) |
| 7 | `touch ~/.hermes/.env` | 성공 | 빈 파일 생성 |
| 8 | 설치 확인 (`hermes --version`, `hermes doctor`) | 성공 | 버전 출력 및 doctor 실행 정상 |

## 설치된 버전 정보

```
Hermes Agent v0.9.0 (2026.4.13)
Project: /Users/hk/hermes-agent
Python: 3.11.13
OpenAI SDK: 2.31.0
Up to date
```

- Python: 3.11.13 (venv)
- Node.js: v22.19.0 (시스템)
- uv: 0.8.17 (시스템)

## 경로 요약

- 저장소: `/Users/hk/hermes-agent`
- 가상환경: `/Users/hk/hermes-agent/venv`
- 실행 파일: `/Users/hk/hermes-agent/venv/bin/hermes`
- 설정 디렉토리: `/Users/hk/.hermes/`
- config: `/Users/hk/.hermes/config.yaml`
- env 파일: `/Users/hk/.hermes/.env` (빈 파일)

## hermes doctor 출력 전문

```
┌─────────────────────────────────────────────────────────┐
│                 🩺 Hermes Doctor                        │
└─────────────────────────────────────────────────────────┘

◆ Python Environment
  ✓ Python 3.11.13
  ✓ Virtual environment active

◆ Required Packages
  ✓ OpenAI SDK
  ✓ Rich (terminal UI)
  ✓ python-dotenv
  ✓ PyYAML
  ✓ HTTPX
  ✓ Croniter (cron expressions) (optional)
  ✓ python-telegram-bot (optional)
  ✓ discord.py (optional)

◆ Configuration Files
  ✓ ~/.hermes/.env file exists
  ⚠ No API key found in ~/.hermes/.env
  ✓ ~/.hermes/config.yaml exists
  ✓ Config version up to date (v17)

◆ Auth Providers
  ⚠ Nous Portal auth (not logged in)
  ⚠ OpenAI Codex auth (not logged in)
    → No Codex credentials stored. Run `hermes auth` to authenticate.
  ⚠ codex CLI not found (required for openai-codex login)

◆ Directory Structure
  ✓ ~/.hermes directory exists
  ✓ ~/.hermes/cron/ exists
  ✓ ~/.hermes/sessions/ exists
  ✓ ~/.hermes/logs/ exists
  ✓ ~/.hermes/skills/ exists
  ✓ ~/.hermes/memories/ exists
  ✓ ~/.hermes/SOUL.md exists (persona configured)
  ✓ ~/.hermes/memories/ directory exists
    → MEMORY.md not created yet (will be created when the agent first writes a memory)
    → USER.md not created yet (will be created when the agent first writes a memory)
    → ~/.hermes/state.db not created yet (will be created on first session)

◆ External Tools
  ✓ git
  ⚠ ripgrep (rg) not found (file search uses grep fallback)
    → Install for faster search: brew install ripgrep
  ✓ docker (optional)
  ✓ Node.js
  ✓ agent-browser (Node.js) (browser automation)
  ✓ Browser tools (agent-browser) deps (no known vulnerabilities)

◆ API Connectivity
  ⚠ OpenRouter API (not configured)

◆ Submodules
  ⚠ tinker-atropos found but not installed (run: uv pip install -e ./tinker-atropos)

◆ Tool Availability
  ✓ terminal
  ✓ file
  ✓ skills
  ✓ browser
  ✓ cronjob
  ✓ tts
  ✓ todo
  ✓ memory
  ✓ session_search
  ✓ clarify
  ✓ code_execution
  ✓ delegation
  ⚠ web (missing EXA_API_KEY, PARALLEL_API_KEY, TAVILY_API_KEY, FIRECRAWL_API_KEY, FIRECRAWL_API_URL)
  ⚠ vision (system dependency not met)
  ⚠ moa (missing OPENROUTER_API_KEY)
  ⚠ image_gen (system dependency not met)
  ⚠ rl (missing TINKER_API_KEY, WANDB_API_KEY)
  ⚠ messaging (system dependency not met)
  ⚠ homeassistant (system dependency not met)

◆ Skills Hub
  ⚠ Skills Hub directory not initialized (run: hermes skills list)
  ⚠ No GITHUB_TOKEN (60 req/hr rate limit — set in ~/.hermes/.env for better rates)

◆ Memory Provider
  ✓ Built-in memory active (no external provider configured — this is fine)

────────────────────────────────────────────────────────────
  Found 3 issue(s) to address:

  1. Run 'hermes setup' to configure API keys
  2. Install tinker-atropos: uv pip install -e ./tinker-atropos
  3. Run 'hermes setup' to configure missing API keys for full tool access

  Tip: run 'hermes doctor --fix' to auto-fix what's possible.
```

## 확인 사항 / 후속 조치

**핵심 환경은 모두 정상 (Python / venv / 의존성 / 디렉토리 / config / Node 툴 전부 ✓)**. 아래 경고는 설치 실패가 아니며 다음 단계(openrouter-connector 등)에서 처리 예정:

- `~/.hermes/.env` 비어있음 → OpenRouter/기타 API 키 구성은 다음 에이전트 담당.
- `tinker-atropos` 서브모듈은 체크아웃되었으나 패키지 미설치 (RL 도구 필요 시 `uv pip install -e ./tinker-atropos` 실행).
- `ripgrep` 미설치 (선택 — `brew install ripgrep` 권장).
- `codex` CLI 미설치 (OpenAI Codex provider 사용 시에만 필요, 선택).

## 실패한 단계

**없음.** 모든 8개 단계 정상 완료.
