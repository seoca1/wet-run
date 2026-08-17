# 🚀 Remote Dev Setup (Notion-Optimized)

> 다른 맥북에서 SSH + opencode로 작업을 계속하기 위한 환경 설정 가이드.
> Notion에 그대로 붙여넣기 가능한 마크다운 형식입니다.

---

## 📌 TL;DR (30분 요약)

```
1. brew install uv tmux tailscale          (5분)
2. git clone + uv sync + download_font     (10분)
3. Tailscale 로그인 + SSH 키 등록          (10분)
4. tmux + opencode 시작                    (5분)
```

---

## 🎯 핵심 도구 4개

| # | 도구 | 역할 |
|---|---|---|
| 1 | **uv** | Python 패키지 매니저 (pyenv + pip 대체) |
| 2 | **Tailscale** | VPN — 어디서든 안전 접속 |
| 3 | **tmux** | SSH 끊김 방지 세션 유지 |
| 4 | **opencode** | AI 에이전트 (작업 도구) |

---

## 1️⃣ 새 맥북 기본 환경 (15분)

### Xcode Command Line Tools

```bash
xcode-select --install
```

### Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 필수 도구 설치

```bash
brew install uv        # Python 패키지 매니저
brew install git       # (보통 이미 설치됨)
brew install tmux      # 터미널 멀티플렉서
# 또는
brew install zellij    # 더 현대적 대안
```

### SSH 키 생성

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
cat ~/.ssh/id_ed25519.pub  # 공개키 — GitHub/원격 머신에 등록
```

---

## 2️⃣ 원격 접속 설정 (20분)

### ✅ 방법 A: SSH 직접 (같은 LAN만)

```bash
# 새 맥북에서 SSH 서버 활성화
sudo systemsetup -setremotelogin on

# 접속
ssh your_username@<새 맥북 IP>
```

**단점**: 공유기 외부에서 접속하려면 포트포워딩 필요.

### 🌟 방법 B: Tailscale VPN (권장)

```bash
# 양쪽 맥북에 설치
brew install --cask tailscale

# 양쪽 로그인 (같은 계정)
# → 자동으로 VPN 연결됨 (각 머신에 100.x.x.x IP 할당)

# 접속
ssh your_username@100.x.x.x
```

**장점**:
- 공유기 포트포워딩 불필요
- 종단간 암호화 자동
- 공용 네트워크에서도 안전
- LAN 외부에서도 동작 (카페, 호텔)

### 방법 C: VSCode Remote SSH (GUI 선호 시)

VSCode 설치 → Remote SSH 확장 → `Ctrl+Shift+P` → "Remote-SSH: Connect to Host"

---

## 3️⃣ 프로젝트 클론 + 실행 (10분)

```bash
# SSH 접속 후
ssh your_username@<원격 IP>

cd ~/projects/Projects
git clone <repo-url> wet-run
cd wet-run/prototype

# Python 의존성 설치
uv sync --all-extras

# 폰트 다운로드 (최초 1회)
uv run python scripts/download_font.py

# 4단계 검증
uv run pytest          # 2284 tests pass
uv run ruff check .    # lint clean
uv run ruff format --check .  # format clean
uv run mypy src tests  # typecheck clean
```

---

## 4️⃣ opencode 실행

### 로컬 작업

```bash
cd ~/projects/Projects/wet-run/prototype
opencode
```

### 원격 작업 (SSH + tmux)

```bash
ssh your_username@<IP>

# tmux 세션 시작 (연결 끊겨도 세션 유지)
tmux new-session -s dev

# 세션 안에서
cd ~/projects/Projects/wet-run/prototype
opencode
```

### tmux 단축키

| 키 | 동작 |
|---|---|
| `Ctrl+B, D` | 세션 detach (백그라운드로) |
| `tmux attach -t dev` | 세션 복귀 |
| `Ctrl+B, %` | 세로 분할 |
| `Ctrl+B, "` | 가로 분할 |
| `Ctrl+B, 화살표` | 패널 간 이동 |

---

## 5️⃣ 데모 / 스크립트 실행

### 헤드리스 (SSH에서 OK)

```bash
# 전투 검증
uv run python scripts/combat_simulator.py --ppl 24 --enemy standard
uv run python scripts/combat_grades.py
uv run python scripts/death_in_action_demo.py

# 그래픽 노블
uv run python scripts/graphic_novel.py --mode novice
uv run python scripts/graphic_novel.py --continue

# 테스트
uv run pytest tests/unit/test_matrix_movement.py -v
```

### ⚠️ GUI / 사운드 (로컬만 권장)

```bash
# 사운드는 원격 SSH에서 출력 안 됨
uv run python scripts/graphic_novel.py --mode novice --with-sound

# GUI 앱은 X forwarding 또는 로컬 실행
uv run python scripts/play.py
```

---

## ⚠️ 원격 작업 시 주의사항

| 제약 | 영향 | 우회 방법 |
|---|---|---|
| **사운드 출력** | `--with-sound` silent | 빼고 실행, 사운드는 로컬 |
| **GUI 앱** | tcod 윈도우 직접 표시 어려움 | 헤드리스 OK, GUI는 로컬 |
| **SSH 끊김** | 진행 손실 | **tmux 필수** |
| **폰트 누락** | 그래픽 깨짐 | `download_font.py` 실행 |
| **큰 파일 전송** | git clone 느림 | git pull / rsync |

---

## 🔒 보안 체크리스트

### SSH 보안 강화

```bash
sudo nano /etc/ssh/sshd_config
```

```text
Port 2222                              # 22 → 2222 (스캐너 회피)
PasswordAuthentication no              # 비밀번호 로그인 비활성화
PermitRootLogin no                     # root 직접 차단
MaxAuthTries 3                         # 인증 시도 3회로 제한
AllowUsers your_username               # 허용 사용자 명시
```

```bash
sudo launchctl unload /System/Library/LaunchDaemons/ssh.plist
sudo launchctl load /System/Library/LaunchDaemons/ssh.plist
```

### 방화벽

```bash
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/sbin/sshd
```

### Tailscale 사용 시

- UPnP 비활성화 (라우터 설정)
- MagicDNS 사용 (IP 대신 hostname)

---

## 📦 환경 백업 + 동기화

### 정기 백업

```bash
cd wet-run
git add -A
git commit -m "wip: <설명>"
git push origin main
```

### 다른 머신에서 받기

```bash
git pull origin main
uv sync    # 새 의존성 자동 반영
```

### 의존성 변경 알림

`pyproject.toml` / `uv.lock` 변경 시 → 다른 머신에서 `uv sync` 필수.

---

## 📋 새 맥북 도착 시 체크리스트

- [ ] macOS 업데이트 완료
- [ ] Xcode CLT 설치 (`xcode-select --install`)
- [ ] Homebrew 설치
- [ ] `uv`, `tmux`, `tailscale` 설치
- [ ] SSH 키 생성 + GitHub 등록
- [ ] Tailscale 로그인 (양쪽 머신)
- [ ] git clone repo
- [ ] `uv sync --all-extras`
- [ ] 폰트 다운로드 (`download_font.py`)
- [ ] `uv run pytest` 통과 확인
- [ ] tmux + opencode 동작 확인

---

## 🔗 관련 문서

- README.md — 프로젝트 개요
- AGENTS.md — AI 에이전트 가이드
- SETUP_LOG.md — 초기 환경 구축 기록
- docs/DEPLOYMENT_GUIDE.md — GitHub Pages 자동 배포
- scripts/README.md — 데모 스크립트 가이드

---

## 💡 한 줄 명령어 (전체 요약)

```bash
brew install uv tmux tailscale && \
  git clone <repo-url> wet-run && \
  cd wet-run/prototype && \
  uv sync --all-extras && \
  uv run python scripts/download_font.py && \
  uv run pytest
```

---

**작성일**: 2026-06-21
**대상 독자**: 다른 머신에서 작업을 이어받을 AI 에이전트 / 개발자
**연관 ADR**: ADR-0045 (matrix movement UX — 가장 최근 작업)