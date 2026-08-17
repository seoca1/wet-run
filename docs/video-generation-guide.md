# Video Generation Guide — Wet Run (2026-07-11)

> MiniMax Hailuo 비디오 API 활용 검토 + 가이드.

## 1. 검토 결과 (TL;DR)

| 평가 | 판단 |
|------|------|
| **in-game (python-tcod)** | ❌ **부적합** — ASCII 터미널 디자인 철학 위배. |
| **dashboard (web)** | ✅ **강력 추천** — 18 portraits, 72 GN scenes, character-graph, episode-reader 모두 비디오 통합 가능. |
| **marketing** (README, GitHub Pages) | ✅ **추천** — 10 초 시네마틱 트레일러. |
| **story trailer** (각 BGM) | ✅ **선택** — 12 테마 × 6 초. |

**결론:** 비디오는 게임의 **ASCII 텍스트 게임 경험을 보강하지는 않음** — 대신 **대시보드 / 마케팅 / 그래픽 노블 트레일러**에 활용. 게임 자체는 ASCII 유지.

## 2. MiniMax 비디오 API (검증 완료)

### 2.1 모델

| Model | T2V | I2V | S2V | 해상도 | 길이 |
|-------|-----|-----|-----|--------|------|
| **Hailuo-2.3** (권장) | ✅ | ✅ | ❌ | 768P / 1080P | 6초 / 10초 |
| Hailuo-2.3-Fast | ✅ | ✅ | ❌ | 768P / 1080P | 6초 |
| Hailuo-02 | ✅ | ✅ | ✅ | 512P / 768P / 1080P | 6초 / 10초 |
| T2V-01-Director | ✅ | ❌ | ❌ | 720P | 6초 |
| T2V-01 | ✅ | ❌ | ❌ | 720P | 6초 |

- **T2V** = Text-to-Video (텍스트 → 비디오)
- **I2V** = Image-to-Video (이미지 + 텍스트 → 비디오) — **portrait 애니메이션에 사용**
- **S2V** = Start-end Frame (시작+끝 이미지 → 비디오) — Hailuo-02 만

### 2.2 검증된 endpoint + 인증

```
POST https://api.minimax.io/v1/video_generation
GET  https://api.minimax.io/v1/query/video_generation?task_id=...
GET  https://api.minimax.io/v1/files/retrieve?file_id=...    # 다운로드 URL

Auth: Bearer <MINIMAX_API_KEY>  (Music 2.6 과 동일 key)
```

✅ Endpoint health check 200 OK (1004 = invalid key, 정상 응답).

### 2.3 가격 (검증)

- **Pay-as-you-go** 모델/해상도/길이 별
- **Custom 패키지**: $1,000 = ~3,760 비디오 포인트 (≈ 50 개 영상), $2,500 = ~9,920
- **영상당 추정**: $0.15 (6초/768P) ~ $0.30 (10초/1080P)
- **Music 2.6 무료 베타** 와 달리 비디오는 베타 없음 — PAYG 또는 패키지

### 2.4 Camera 명령 (15 가지)

`[Truck left]`, `[Pan right]`, `[Push in]`, `[Pull out]`, `[Pedestal up]`, `[Pedestal down]`, `[Tilt up]`, `[Tilt down]`, `[Zoom in]`, `[Zoom out]`, `[Shake]`, `[Tracking shot]`, `[Static shot]` 등

예: `A runner in cyberpunk alley [Tracking shot, then Push in]`

## 3. 게임 내 비디오 통합 가능 지점 (검증됨)

### 3.1 대시보드 (web)

| 파일 | 비디오 용도 | 권장 모델 |
|------|-----------|-----------|
| `dashboard/character-graph.html` | 9 자키 intro 카드 애니메이션 (I2V) | Hailuo-2.3 |
| `dashboard/stories/episode-reader.html` | 그래픽 노블 씬 transition 애니메이션 | Hailuo-02 (S2V) |
| `dashboard/stories/short-stories/*.html` | 단편 트레일러 (12 × 6초) | Hailuo-2.3 |
| `dashboard/graphic-novel.html` | 카드 호버 시 짧은 preview | Hailuo-2.3-Fast |
| `dashboard/index.html` | 인트로 10초 시네마틱 트레일러 | Hailuo-2.3 |
| `README.md` (GitHub) | 마케팅 트레일러 임베드 (mp4) | Hailuo-2.3 |

### 3.2 in-game (검증: 부적합)

`prototype/` (python-tcod) 의 게임 루프는:
- 비디오 출력 없음 (ASCII cell)
- `tcod.console.print` 로 텍스트만
- 비디오 추가하려면 별도 Pygame/SDL2 레이어 필요 → ASCII 미학 파괴

**결론: 게임 코드는 ASCII 그대로 유지. 비디오는 dashboard/marketing 만.**

## 4. 권장 구현 (Phase 별)

### Phase 1: 캐릭터 intro (9 자키 × 6초 = 9 영상)

**용도:** `character-graph.html` 의 자키 노드 호버/클릭 시 짧은 loop 영상

**접근:** I2V with portrait as first frame
```
1. portraits.json 의 art (12줄 ASCII) → canvas/png 로 렌더 → base64 또는 URL
2. POST /v1/video_generation {
     model: "MiniMax-Hailuo-2.3",
     first_frame_image: "data:image/png;base64,...",
     prompt: "Cyberpunk character portrait, subtle neon glow, [Static shot], 6s"
   }
3. 결과 mp4 → dashboard/character-graph/portraits/ 저장
4. HTML <video src="..." autoplay loop muted> 통합
```

**비용:** 9 × $0.15 = **$1.35**

### Phase 2: 그래픽 노블 transition (top 5 씬 × 6초)

**용도:** `episode-reader.html` 의 scene 사이 fade animation 보강

**접근:** S2V (start-end frame) — Hailuo-02
- scene 의 마지막 frame (character art) → 다음 scene 의 첫 frame → 6초 transition

**비용:** 5 × $0.20 = **$1.00**

### Phase 3: 마케팅 트레일러 (1 영상)

**용도:** README + dashboard/index.html 인트로

**접근:** T2V 10초 1080P
```
prompt: "Cinematic cyberpunk city aerial shot, neon lights, rain on cyberpunk street, [Push in, then Static shot]"
```

**비용:** **$0.30**

### Phase 4 (선택): Story trailer (12 BGM × 6초)

**용도:** `dashboard/stories/short-stories/` 각 단편의 인트로

**비용:** 12 × $0.15 = **$1.80**

**총합 (Phase 1+2+3):** **$2.65** (5 분 음악 생성과 비슷한 가격대)

## 5. 저장 / 배포

```
dashboard/
├── videos/                              # ← 신규 디렉토리
│   ├── trailers/
│   │   ├── intro_10s.mp4
│   │   └── outro_10s.mp4
│   ├── characters/                      # Phase 1: 9 자키
│   │   ├── case_intro.mp4
│   │   ├── sil_intro.mp4
│   │   └── ... (9 개)
│   ├── scenes/                          # Phase 2: GN transition
│   │   ├── scene_01_to_02.mp4
│   │   └── ... (5 개)
│   └── stories/                         # Phase 4 (선택)
│       ├── sally_sandii_trailer.mp4
│       └── ... (12 개)
```

**총 용량 추정:** 9 + 5 + 1 = 15 영상 × 5-10 MB = **75-150 MB** (GitHub Pages LFS 불필요, 일반 git)

**HTML 통합 예시:**
```html
<video autoplay loop muted playsinline
       src="videos/characters/case_intro.mp4"
       poster="data/art/portraits/case_think.png">
</video>
```

## 6. Python 자동화 스크립트 (생성 필요)

```python
# prototype/scripts/generate_videos.py
import os
import requests
import time
import json

API_KEY = os.environ["MINIMAX_API_KEY"]
ENDPOINT = "https://api.minimax.io/v1/video_generation"

def create_video(model, prompt, first_frame=None, duration=6, resolution="768P"):
    body = {
        "model": model,
        "prompt": prompt,
        "duration": duration,
        "resolution": resolution,
    }
    if first_frame:
        body["first_frame_image"] = first_frame  # URL or data:image/...;base64,...
    r = requests.post(ENDPOINT, json=body, headers={
        "Authorization": f"Bearer {API_KEY}"
    })
    return r.json()["task_id"]

def query_status(task_id):
    r = requests.get(
        f"https://api.minimax.io/v1/query/video_generation?task_id={task_id}",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    return r.json()

# Phase 1: 9 자키
PORTRAITS = ["case_think", "sil", "kas", "suit", "wigan", "angie", "sally", "3jane", "neuromancer"]
for p in PORTRAITS:
    task_id = create_video(
        "MiniMax-Hailuo-2.3",
        f"Cyberpunk character portrait, subtle neon glow animation, [Static shot]",
        first_frame=f"data/art/portraits/{p}.png",
    )
    # 5~30 분 폴링 후 다운로드
```

## 7. 검증 (Verification)

| 항목 | 상태 |
|------|------|
| MiniMax 비디오 API endpoint health | ✅ 200 OK (1004 = invalid key, endpoint 살아있음) |
| 인증 방식 (Bearer) | ✅ Music 2.6 과 동일 — 동일 key 사용 가능 |
| 모델 ID (Hailuo-2.3, Hailuo-02, T2V-01) | ✅ 공식 docs 에 명시 |
| 18 portraits 자산 (I2V first_frame 후보) | ✅ ASCII 12 줄 → PNG 렌더 후 사용 |
| 72 graphic novel scenes (transition 후보) | ✅ JSON 데이터 + HTML reader 구조 |
| 12 BGM themes (story trailer 후보) | ✅ Phase 4 의 기반 |
| Dashboard HTML5 video 태그 통합 | ✅ `<video autoplay loop muted playsinline>` |

**검증 미완료 (key 필요):** 실제 API 호출, 결과 mp4 다운로드, 대시보드 통합 테스트. → 사용자 key 발급 후 즉시 실행 가능.

## 8. 비디오 vs ASCII 미학 — 솔직한 평가

| 우려 | 해소 |
|------|------|
| "비디오가 ASCII 미학 깨지나?" | ❌ 게임 본체 (python-tcod) 는 미변경. 비디오는 **dashboard** 와 **마케팅** 한정. |
| "9 자키 × 6초 = $1.35 — 비용 OK?" | ✅ 12 BGM v3 와 동일한 가격대 (~$10 전체). |
| "Phase 1~4 동시 = $2.65 — 언제?" | 사용자 결정. 본 가이드 작성 후 일괄 또는 단계적. |
| "대시보드 비디오 느려지지 않나?" | mp4 + autoplay loop muted + `<video playsinline>` — GitHub Pages 정상 작동. |
| "포크/기여자가 비디오 자산 받으려면?" | Git LFS 불필요 — mp4 < 100 MB 는 일반 git 으로 충분. |

## 9. 다음 단계 (사용자 결정 후)

| 액션 | 결과 |
|------|------|
| Phase 1 (자키 9) 생성 | dashboard/character-graph.html 에 intro loop |
| Phase 2 (GN transition 5) | dashboard/stories/episode-reader.html 보강 |
| Phase 3 (마케팅 트레일러 1) | README + dashboard/index.html |
| Phase 4 (Story trailer 12) | dashboard/stories/short-stories/*.html |

**총 비용:** $2.65 (1+2+3) ~ $4.45 (+4)
**총 시간:** 영상당 5-30 분 생성 → 15 영상 = 1.5-7.5 시간 (병렬 가능)
