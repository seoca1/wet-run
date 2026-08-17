

---

# ⚠️ Actual Working Path (2026-07-11 업데이트)

**원래 가이드는 Udio API 위주로 작성 (Section 1-3)**. 그러나 **실제 사용된 경로**는 미니맥스 Music 2.6 무료 베타 웹 UI 입니다 (이 가이드 작성 후 사용자 결정으로 변경).

## 실제 워크플로 (미니맥스 웹 UI)

### Step 1: 계정/결제 등록
```
1. https://www.minimax.io 접속 (Chrome 시크릿 + 영문 우선 → 중국 페이지 회피)
2. Google/Github 계정 가입
3. 결제 수단 등록 (PayPal 권장 — 해외 카드 OK)
4. 무료 베타 (Music 2.6) — 14 일간 일 500 회 무료
```

### Step 2: 12 트랙 프롬프트 + 생성
- 위 Section 2 의 12 개 정확한 영어 프롬프트 그대로 사용
- 웹 UI: "Custom" 모드 / Lyrics 비우기 / **is_instrumental=true** / 16:9 long (BGM 길이)
- 트랙당 4-10 회 재생성 (quota 일 500 회이므로 충분)

### Step 3: 다운로드 + 자동 처리
```bash
# ~/Downloads/<name>.mp3 + (f)/(m).mp3 다운로드 후:
./dashboard/scripts/import_minimax_track.sh <name> ~/Downloads/<name>.mp3

# (f)/(m) 변형은 mp3 그대로 sounds/full/ 에 배치 (장소 절약)
```

### Step 4: 검증
```bash
# 12 BGM 일괄 검증
python3 prototype/scripts/demo_minimax_bgms.py --silent

# 30 초씩 전곡 청취 (감상용)
python3 prototype/scripts/demo_minimax_bgms.py --full
```

### 비용 (12 트랙 × 5-10 회 재생성)
- **베타 기간 (14 일)**: $0
- **이후 PAYG**: $0.15/곡 × ~60 회 = $9
- **구독 ($20/월)**: 불필요 — 수동 웹 UI 로 충분

### 라이선스 (확인 필요)
- 미니맥스 Music 2.6 베타 트랙: 사용자 상업 사용 가능 (베타 종료 후 PAYG 도 동일)
- 생성 직후 screenshots + 영수증 보관 권장 (정책 변경 가능성 대비)

> 즉 본 가이드의 Section 1-3 (Udio 10$/월) **가 아닌**, 미니맥스 무료 베타로 진행. Section 2 의 12 개 정확한 프롬프트 + Section 4 의 비용 추정 + Section 6 의 자동화 코드 (verify_sounds.py / demo_minimax_bgms.py) 그대로 활용.

# BGM External Generation Guide — Gibson Sprawl Cyberpunk

> 작성일: 2026-07-11 | 대상: `dashboard/sounds/` 의 12개 theme BGM 트랙
> 검증환경: macOS 26.5.2 / Python 3.14 / ffmpeg 8.1.1

## 0. 왜 이 가이드가 필요한가

현재 `dashboard/sounds/` 의 12개 WAV 는 3초짜리 짧은 루프 + 단순 사인파 합성으로 만들어져:

- **3초 루프** → BGM 으로 부적합 (게임 1 사이클 30초~2분)
- **낮은 음량** (-47~-40 dBFS) → 일부 사용자 듣기 어려움
- **테마 변별 부족** → 12개 트랙이 톤이 비슷함

ffmpeg 신호처리 (이전 단계에서 구현) 로 일부 개선 가능하지만, **진짜 새 멜로디/화성** 도입은 외부 생성 서비스가 유일한 옵션. 이 가이드는 외부에서 만든 트랙을 게임에 통합하는 전체 워크플로를 정리.

## 1. 서비스 선택

### 1.1 후보 비교 (2026-07 기준)

| 서비스 | 가격 | 월 credit | 특징 | 게임 BGM 적합성 |
|---|---|---|---|---|
| **Suno** Pro | $10/mo | 2,500 | v5.5 모델, 보컬 강점, 빠른 생성 | ⭐⭐⭐⭐ 인스트루멘털 강제 시 |
| **Udio** Standard | $10/mo | 2,400 | 스템 export, Voice Control, 130초 generation | ⭐⭐⭐⭐⭐ BGM에 최적 |
| **ElevenLabs** Music | paid only | (별도) | 고품질, 보컬 특화 | ⭐⭐⭐ 짧은 stinger 용 |
| **Suno Free** | $0 | 50/일 (~10 songs) | 비영리용, 빠른 실험 | ⭐⭐ 학습/시도 |
| **Udio Free** | $0 | 10/일 + 100/월 | 극히 제한 | ⭐ 잘 안 됨 |

### 1.2 권장: **Udio Standard 1개월** ($10)

이유:

1. **130초 (2:10) 길이 단일 생성** → BGM 트랙에 충분한 길이
2. **스템 export** (free는 안 됨, Standard도 wav stem 직접 export는 Pro 한정 → 일단 mp3/m4a 도 OK)
3. **Voice Control 비활성화 + Instrumental 모드** → 깔끔한 인스트루멘털 보장
4. **Inpainting (섹션 재생성)** → 특정 부분 마음에 안 들면 그 구간만 다시 생성
5. **Audio upload 가능** → v1/v2 트랙을 reference 로 업로드해서 톤 일치

Suno 가 더 저렴하고 많이 알려져 있지만 vocal-heavy 하고 instrumental mode 일관성이 약함. **Udio 가 BGM 에 안정적.**

총 비용: **$10 (1개월)** + 12 트랙 × ~5-10 회 재생성 = 약 **200-400 credits** (Standard 한도 2,400 의 1/6~1/12).

## 2. 프롬프트 라이브러리 — 12개 테마

각 트랙은 Gibson 의 Sprawl 3부작 (Neuromancer / Count Zero / Mona Lisa Overdrive) 분위기 + Sprawl 게임 컨텍스트에 맞춤. **보컬 없음 + 인스트루멘털** (BGM 인스). 길이 60-120초 목표.

### 공통 메타 프롬프트 템플릿

```
[장르] [분위기] [악기], [BPM 70-110], [결 구조], [모티프 설명]
Mood references: [레퍼런스 음악 또는 분위기 키워드]
```

### 2.1 개별 프롬프트 (12개)

#### `theme_matrix_rain.wav` (전개부 — 매트릭스 진입)
```
BPM: 96 | 길이: 90s | loop-ready
"Dark ambient cyberpunk, opening descent into the matrix.
Rain texture over deep analog synth bass (C2), glitchy modular
synth arpeggios (A minor pentatonic), occasional distant radio
chatter. Sparse, atmospheric, low energy 0:00-0:30 builds
slightly with radio static at 0:45. Cinematic, sci-fi noir,
William Gibson Neuromancer vibe. Instrumental only, no vocals.
No percussion except very subtle glitch clicks."
```

#### `theme_cyberspace.wav` (탐색 — 깊은 매트릭스)
```
BPM: 88 | 길이: 90s | loop-ready
"Cyberspace exploration, deep matrix dive. Hypnotic analog
synth pads (G minor), slow-evolving arpeggiated sequence with
low pass filter sweep, distant digital chirps, granular
texture like data streams. Sparse hi-hat clicks only, no
drums. Long sustained tones, sense of vast digital space.
Cinematic tension, no resolution, just hovering presence."
```

#### `theme_chiba.wav` (도시 — 네온 거리)
```
BPM: 110 | 길이: 75s | loop-friendly
"Nighttime Chiba City cyberpunk street, neon-soaked jazz-funk
fusion. Saxophone lead melody (mysterious minor), muted bass
groove (walking line), lo-fi MPC drums (boom-bap swung),
Rhodes electric piano comp, FM synth pads. Tape hiss, distant
traffic, Japanese city alley atmosphere. Headphones music,
Blade Runner meets Casiopea. Instrumental, smooth groove."
```

#### `theme_sense_net.wav` (기업 — Tessier-Ashpool)
```
BPM: 78 | 길이: 90s | loop-ready
"Corporate minimal techno, AI entity's domain. Cold precise
sequencer bass (white noise + sub), sparse modular synth
melody in D Dorian, no humanizing, all quantized. Glass-like
tonal pads, occasional crystal bells, mechanical clock tick
rhythm. Sense of vast empty server space. Cocoon-like,
isolation. Instrumental only. Slightly unsettling, like being
watched by an ancient intelligence."
```

#### `theme_finn_office.wav` (브리핑)
```
BPM: 92 | 길이: 60s | loop-ready
"Downtempo noir lounge, private investigation office.
Muted trumpet (Miles Davis style), upright bass,
brushes on snare, Fender Rhodes, sparse piano comp chords.
Detective story atmosphere, urban night, vinyl record warmth.
Slow chord progression in D minor, no resolution to major.
Saxophone in second half. Instrumental lounge jazz, Walter
Bezzerra meets Blade Runner bar scene."
```

#### `theme_hammer_alert.wav` (긴급/전투) — 짧고 강렬하게
```
BPM: 132 | 길이: 45s | loop-ready
"Industrial breakcore aggressive action. Distorted 808 bass
hits, glitchy chopped amen break drums, distorted synth
stabs, alarm siren loop, impact SFX every 4 bars. Aggressive
tension building to climax at 0:30 then tearing back.
Cyberpunk combat scenario. Heavy digital distortion, bit
crushed, filter sweeps. Loops cleanly back to start. No
vocals, no melodic resolution — pure kinetic energy."
```

#### `theme_industrial.wav` (전투 — 긴장)
```
BPM: 124 | 길이: 80s | loop-ready
"Industrial EBM combat. Driving 4-on-the-floor kick drum,
distorted analog bassline (A minor), metallic percussion,
harsh modular synth lead melody. Repetitive but evolving,
tension without resolution. Dark warehouse rave, cybernetic
combat scenario, mechanical body horror. Influences:
Front 242, Nitzer Ebb, cyberpunk industrial. Punchy low end,
mid-range bite. Clean mix, vocals only as chopped shouts."
```

#### `theme_broadcast.wav` (스토리/이벤트)
```
BPM: 84 | 길이: 75s | loop-friendly
"Ambient news broadcast soundtrack. Subliminal vintage radio
broadcast tone underlay (30% volume), pulsing analog synth
pad (F minor), tape echo delays on atmospheric lead melody.
Hammond organ chord swells, world music percussion (light
frame drum, doumbek). Sense of impending news, plot
unfolding, slight unease. Saturated analog warmth. Loops
cleanly. Instrumental, cinematic."
```

#### `theme_loa_drum.wav` (잭-아웃 — 신비)
```
BPM: 92 | 길이: 60s | loop-friendly
"Ritualistic voodoo cyberpunk drum circle. Deep hand drum
(Djembe + conga) ostinato with reverb tail, analog synth
drone bass (B minor pentatonic), ominous chants as texture
(no actual lyrics, just vowel pad), occasional bell strikes.
Haunted Bayou meets cyberspace, loa spirits communicating.
Mystical undertone. Space between drums important. Builds
intensity every 8 bars. Loop-ready. Gospel choir texture
without words."
```

#### `theme_loa_drum_fade.wav` (Death Summary — 체념)
```
BPM: 60 | 길이: 60s | loop-friendly
"Somber death farewell dronescape. Solo church organ playing
slow minor chords (D Dorian), distant weeping bowed guitar,
hammond organ with slow Leslie swirl, sparse tympani hits
every 8 bars. Building finality, accepting death. Long
reverb tails across whole mix. No drums, no percussion.
Tchaikovsky meets industrial ambient. Sacred minimal.
Fade out end for game over screen. No resolution — fades to
silent."
```

#### `theme_loa_channel.wav` (Hall of Dead — 사이버 귀신)
```
BPM: 84 | 길이: 75s | loop-friendly
"Ghosts in the wires, hallucinated afterlife. Granular
synthesizer pad that never repeats, white noise mist,
distant church bell played backwards, low string drone in
C minor, ghostly male choir vowel swells (wordless, 30%
volume only, distant), occasional plucked harp arpeggios.
Reverb-heavy, spatial sound design. Dreampunk spiritual.
Cyberpunk ghost story, voices of dead constructs trapped in
matrix. No drums, no percussion, no melody — pure atmosphere."
```

#### `theme_manarase_drone.wav` (엔딩 크레딧 — 차분한 여운)
```
BPM: 76 | 길이: 120s | non-looping
"End credits somber ambient. Solo nylon string guitar finger
picking slow arpeggio in F# minor, soft analog synth pad
underneath, very subtle bowed vibraphone, distant female
choir vowel drone (no lyrics). Slow build to hopeful but
melancholic resolution, ends on suspended chord. 90 sec total,
tails into silence for end credits. Kim Cascone meets Nick
Drake. Reflective, accepting, post-story contemplation.
Very quiet dynamics, mostly pianissimo."
```

#### `theme_sense_net.wav` 재확인 (corporate 전용)
↑ 위 2.4 항목 참조 (중복이지만 별도 페이지 만들지 않을 거면 그대로 사용)

## 3. 워크플로

### 3.1 Step 1: 계정 생성 + 플랜 가입

```
1. https://udio.com 접속
2. 우상단 [Get Started] → 이메일/Google 계정 가입
3. 결제 정보 없이 Free 로 시작 가능 (10 credits/일)
4. 한 달 사용 예정이면 → $10/mo Standard 결제
   - Settings → Subscription → Standard 선택
5. 일회성 1달 구독 → 1달 후 자동 해지 (Reminder 설정)
```

### 3.2 Step 2: 프롬프트 입력 (12개)

```
1. udio.com/new (Generate 페이지)
2. 모드: "Custom" 
3. Lyrics: 비워두기 (인스트루멘털)
4. "Styles & Tags" 섹션: 위 프롬프트의 **음악적 특성**만 추출:
   예: theme_matrix_rain → [ambient, cyberpunk, dark, atmospheric, 
   downtempo, modular synth, no vocals, no drums, 90s]
5. "Lyric Snippets" / style description 에 위 길고 자세한 프롬프트
6. "Generate" 클릭 → 2 variations 자동 생성
7. 마음에 드는 variation 선택 → 다운로드 (mp3 또는 wav)
```

**각 트랙당 5-10 회 재생성** 예상. 좋은 결과 안 나오면 prompt 조정.

### 3.3 Step 3: 파일 명명 + 다운로드

다운로드 시 반드시 다음 이름으로 저장 (sound.html 의 SOUNDS_BASE 와 매핑):

```
theme_matrix_rain.wav    (또는 _v3 붙여서 기존과 분리)
theme_cyberspace.wav
theme_chiba.wav
theme_sense_net.wav
theme_finn_office.wav
theme_hammer_alert.wav
theme_industrial.wav
theme_broadcast.wav
theme_loa_drum.wav
theme_loa_drum_fade.wav
theme_loa_channel.wav
theme_manarase_drone.wav
```

`theme_loa_drum_fade` 는 fade out 포함 → 30초까지 trim 가능한지 확인.

### 3.4 Step 4: 형식 표준화

다운로드 파일이 WAV 가 아닐 수 있음 (mp3/m4a). 정규화 필요:

```bash
# 단일 트랙 변환 예시
ffmpeg -i "downloaded_theme_matrix_rain.mp3" \
  -ar 44100 -ac 2 -c:a pcm_s16le \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11" \
  "/Users/emilio/projects/Projects/Game/wet_run/dashboard/sounds/theme_matrix_rain.wav"

# 12개 일괄 변환 (bash 루프)
cd ~/Downloads/udio_exports
for f in *.mp3 *.m4a; do
  base=$(basename "$f" | sed 's/\.\(mp3\|m4a\)$//')
  ffmpeg -y -i "$f" \
    -ar 44100 -ac 2 -c:a pcm_s16le \
    -af "loudnorm=I=-16:TP=-1.5:LRA=11" \
    "/Users/emilio/projects/Projects/Game/wet_run/dashboard/sounds/${base}.wav"
done
```

### 3.5 Step 5: 검증

```bash
# 12개 WAV 일괄 검증
python3 /Users/emilio/projects/Projects/Game/wet_run/scripts/verify_sounds.py

# 각 트랙 청취
python3 /Users/emilio/projects/Projects/scripts/verify_sounds.py --play-all
```

체크리스트:
- [ ] 12개 모두 audible (RMS > 50)
- [ ] 12개 모두 dBFS > -25 (조용한 트랙 없음)
- [ ] 비트율 1411 kbps (16-bit stereo 44.1kHz)
- [ ] 파일명 정확히 일치 (sound.html 의 SOUNDS_BASE 매핑)
- [ ] 끝→시작 루프 자연스러운지 (직접 청취 확인)

### 3.6 Step 6: 사운드 페이지 통합

```bash
# 기존 v2 디렉토리 백업 (검증된 fallback)
mv /Users/emilio/projects/Projects/Game/wet_run/dashboard/sounds/v2 \
   /Users/emilio/projects/Projects/Game/wet_run/dashboard/sounds/v2_20260711_enhanced

# 새 트랙들은 이미 Step 4 에서 sounds/ 에 들어감
# sound.html 은 자동으로 새 파일 사용 (파일명이 같으므로)

# 브라우저에서 즉시 검증
open http://localhost:8765/sound.html
# 각 버튼 클릭 → 새 트랙 재생되는지
```

### 3.7 Step 7: 문제 발생 시 롤백

```bash
# 새 트랙 백업 + 즉시 롤백
mkdir -p /Users/emilio/projects/Projects/Game/wet_run/dashboard/sounds/v3_ext
cp /Users/emilio/projects/Projects/Game/wet_run/dashboard/sounds/theme_*.wav \
   /Users/emilio/projects/Projects/Game/wet_run/dashboard/sounds/v3_ext/

# v2 로 되돌리기 (ffmpeg 강화 버전)
cp /Users/emilio/projects/Projects/Game/wet_run/dashboard/sounds/v2_20260711_enhanced/theme_*.wav \
   /Users/emilio/projects/Projects/Game/wet_run/dashboard/sounds/

# v1 (원본) 로 완전 롤백 (이미 사라졌으면 git 에서)
# git checkout dashboard/sounds/theme_*.wav
```

## 4. 비용/시간 추정

| 항목 | 추정값 |
|---|---|
| 구독료 | $10 (Udio Standard 1개월) |
| credit 사용 | ~200-400 (12 트랙 × 5-20 회 재생성) |
| 생성 시간 | 30초-2분 per generation, 트랙당 5-10 회 = 약 1시간 |
| 다운로드 시간 | 자동, ~30초 |
| ffmpeg 정규화 | 30초 total (12 트랙 일괄) |
| 검증 + sound.html 통합 | 30분 (청취 시간 포함) |
| **총 시간** | **3-4 시간** |
| **총 비용** | **$10** (구독료) |

## 5. 라이선스 (중요)

Udio Standard 의 commercial rights:

- 생성된 트랙은 Standard 구독 상태에서 만들어졌을 때만 상업적 사용 가능
- Free tier 에서 만든 트랙은 비영리 / 개인 테스트 용도만
- **1개월 구독 내** 만들어진 12개는 모두 상업적 사용 가능
- 1개월 후 구독 해지해도, 그 기간 중 만들어진 트랙의 권한은 유지됨

즉:
1. 1개월 Standard 구독 ($10)
2. 그 안에서 12 트랙 모두 생성
3. 구독 취소 — 트랙의 상업적 사용권은 유지

게임/포트폴리오에 활용 가능. 단, generative music 서비스 정책은 자주 바뀌므로 **생성 직후 screenshots + 영수증 보관 권장**.

## 6. 자동화 가능성 (선택)

장기적으로 자동화하고 싶다면:

### Option A: 공식 API (Udio 현재 없음)
- Udio 는 공식 API 없음 (web app 만)
- Suno 도 2026 중반 developer API 베타 예정

### Option B: 서드파티 API
- MusicAPI ($0.06-0.18 per track, Google Lyria 3 Pro)
- 발급 키 + 인증 자동화로 12개 일괄 생성 가능
- 자동 ffmpeg 정규화 + 사운드 페이지 자동 통합

### Option C: 로컬 모델 (추후)
- MusicGen (Meta) — 오픈소스, 로컬 실행 가능
- 향후 Apple Silicon 성능 개선 시 실용화 가능

지금 시점에서는 **수동 워크플로 (Step 3.1~3.7)** 가 가장 빠르고 안전.

## 7. 체크리스트 (실행용)

```
[  ] 1. Udio Standard 구독 ($10)
[  ] 2. 12개 프롬프트 준비 (위 Section 2)
[  ] 3. theme_matrix_rain 생성 → 청취 → 다운로드
[  ] 4. theme_cyberspace 생성 → 청취 → 다운로드
[  ] 5. theme_chiba 생성 → 청취 → 다운로드
[  ] 6. theme_sense_net 생성 → 청취 → 다운로드
[  ] 7. theme_finn_office 생성 → 청취 → 다운로드
[  ] 8. theme_hammer_alert 생성 → 청취 → 다운로드
[  ] 9. theme_industrial 생성 → 청취 → 다운로드
[  ] 10. theme_broadcast 생성 → 청취 → 다운로드
[  ] 11. theme_loa_drum 생성 → 청취 → 다운로드
[  ] 12. theme_loa_drum_fade 생성 → 청취 → 다운로드
[  ] 13. theme_loa_channel 생성 → 청취 → 다운로드
[  ] 14. theme_manarase_drone 생성 → 청취 → 다운로드
[  ] 15. ffmpeg 일괄 정규화 (Step 4)
[  ] 16. verify_sounds.py 검증 (Step 5)
[  ] 17. sound.html 통합 + 브라우저 청취 (Step 6)
[  ] 18. v2 백업 정리 (Step 7)
[  ] 19. log.md 에 기록
```

---

## 부록: 음악적 토큰 참조집

### Sprawl 세계 분위기 키워드 (프롬프트에 자유 조합)

```
cyberpunk, dark ambient, sci-fi noir, retrofuture 80s,
analog synth, modular synth, arpeggiator, sound design,
cinematic, atmospheric, dystopian, neon noir, ghost in
the shell, blade runner, William Gibson, William S.
Burroughs, TV static, tape hiss, lo-fi, vinyl warm,
saturated, glitch, granular synthesis
```

### 악기별 음색 키워드

```
Bass: sub bass, 808, deep analog, walking bass, upright
Leads: muted trumpet, saxophone, FM bell, nylon guitar
Pad: warm analog pad, slow Leslie, organ swell, glass
Perc: brushed snare, lo-fi MPC, hand drum, glass marimba
Texture: granular, distorted, bit-crushed, FM bell, glass,
electric piano, Rhodes, tape echo, reverb field
```

### Reference 음악 (프롬프트에 넣으면 일관성 ↑)

```
- Blade Runner (Vangelis) — 분위기
- Mr. Robot score (Mac Quayle) — 사이버펑크
- Cowboy Bebop OST (Seatbelts) — 도시 + 재즈 + 일렉
- Akira soundtrack (Geinoh Yamashirogumi) — 리추얼
- Hotline Miami OST — 전투 + 일렉
- Cyberpunk 2077 OST — 사이버펑크 (참고용, 차용 X)
- 모비 (Massive Attack) — Trip-hop / 쿨
- 보석의之国 OST — 미니멀 일렉
```

## 부록: 상세 자체 비교

| 기준 | Suno Pro | Udio Standard | ElevenLabs |
|---|---|---|---|
| 가격 | $10/mo | $10/mo | (별도) |
| v5.5 vs v4 | v5.5 | 모델 | - |
| 인스트루멘털 모드 | 있음 (선택) | 기본 | 약함 |
| Stems | Pro 에서 12 stems | Pro 만 wav, Standard mp3 | - |
| Inpainting | 없음 | Standard | - |
| 130초 (BGM 적합) | 짧은 60s 잘 함 | 130초 강점 | 30초 ~ 1m |
| Audio upload | Pro tier | Standard | - |
| API | 베타 (2026 중반) | 없음 | 있음 |
| 무료 티어 | 50 credits/day | 10/day + 100/mo | 거의 없음 |
| 게임 적합 | 좋음 | **가장 좋음** | 미디엄 |

Udio Standard 1개월 $10 이 BGM 12트랙에 가장 효율적.
