# ADR-0043: 12개 씬 사운드 큐 연결

**상태**: Accepted
**날짜**: 2026-06-20
**결정자**: 사용자
**우선순위**: P2

## 컨텍스트 (Context)

12개 씬 dialogue에 **15개 sound cue** 가 정의되어 있지만, 실제 재생이 거의 동작하지 않음.

분석 결과 두 가지 결함:

1. **`graphic_novel.py`의 path 버그**:
   ```python
   sounds_dir=data_dir / ".." / "sounds_test"  # → Game/wet_run/prototype/sounds_test (X)
   ```
   data 부모 디렉토리를 가리켜서 **sound 파일을 못 찾음**.

2. **`shibuya_traffic` cue 누락**: SCENE_SOUND_MAP에 매핑 없음 → 15개 중 1개 unmapped.
   - 나머지 14개는 `graphic_novel_audio.SCENE_SOUND_MAP`을 통해 DEFAULT_SOUNDS에 정상 매핑됨.
   - `SoundManager._ensure_sounds()`는 누락 WAV를 자동 생성하므로 file 자체는 항상 존재.

## 고려한 옵션

### Option 1: path 버그 수정 + shibuya_traffic 추가 ✓ 선택

- **설명**: 
  1. `graphic_novel.py`의 `sounds_dir`를 `data_dir / "sounds_test"`로 수정
  2. `SCENE_SOUND_MAP`에 `"shibuya_traffic": "theme/sense_net"` 추가 (Shibuya cyberpunk → sense_net ambient)
  3. Cue → file 매핑 검증 테스트 추가
- **장점**:
  - 5분 작업으로 100% cue 동작
  - 매핑 누락 검증으로 회귀 방지
- **단점**: 없음

### Option 2: cue 이름 변경 (shibuya_traffic → 다른 매핑 가능한 이름)

- **설명**: 씬 JSON을 수정
- **장점**: 매핑 추가 불필요
- **단점**: 씬 데이터 수정 → 다른 테스트 영향

### Option 3: 모든 cue 자동 생성

- **설명**: DEFAULT_SOUNDS에 매핑되지 않은 cue도 자동 합성
- **장점**: 매핑 누락 자동 처리
- **단점**: 이미 자동 생성되므로 효과 없음

## 추천 (Recommendation)

**Option 1** — 가장 직접적이고 검증 가능한 해결.

## 사용자 결정 (Decision)

[x] Option 1 — path fix + cue mapping 추가

## 결과 (Consequences)

### 긍정적
- **15/15 scene cue가 실제 file로 매핑**되어 재생됨
- `SoundManager._ensure_sounds()`로 누락 WAV 자동 생성 → file 존재 보장
- 자동 재생 (--with-sound 옵션) 동작 확인
- 매핑 누락 즉시 검출 (regression test)

### 부정적 / 위험
- macOS / Windows / Linux audio backend 의존성 (`afplay` / `aplay` / `winsound`)
  - 자동 fallback 처리됨 (silent no-op)

## 영향 받는 항목
- `prototype/scripts/graphic_novel.py` — `sounds_dir` path fix
- `prototype/src/wet_run/engine/graphic_novel_audio.py` — `shibuya_traffic` 매핑 추가
- `prototype/tests/unit/test_graphic_novel_audio.py` — 신규 테스트 23개

## 매핑 테이블 (15개 cue)

| Scene cue | DEFAULT_SOUNDS key | WAV 파일 |
|---|---|---|
| `chiba_rain_loop` | `theme/chiba` | `theme_chiba.wav` |
| `matrix_rain` | `theme/matrix_rain` | `theme_matrix_rain.wav` |
| `finn_office` | `theme/finn_office` | `theme_finn_office.wav` |
| `loa_drum` | `theme/loa_drum` | `theme_loa_drum.wav` |
| `loa_drum_fade` | `theme/loa_drum_fade` | `theme_loa_drum_fade.wav` |
| `manarase_drone` | `theme/manarase_drone` | `theme_manarase_drone.wav` |
| `neon_hum` | `movement/neon_hum` | `movement_neon_hum.wav` |
| `jack_in_zap` | `movement/jack_in_zap` | `movement_jack_in_zap.wav` |
| `jack_out_buzz` | `movement/jack_out_buzz` | `movement_jack_out_buzz.wav` |
| `data_extract` | `movement/data_extract` | `movement_data_extract.wav` |
| `black_ice_roar` | `movement/black_ice_roar` | `movement_black_ice_roar.wav` |
| `broadcast_static` | `movement/broadcast_static` | `movement_broadcast_static.wav` |
| `broadcast_out` | `movement/broadcast_out` | `movement_broadcast_out.wav` |
| `hammer_alert` | `theme/hammer_alert` | `theme_hammer_alert.wav` |
| `shibuya_traffic` | `theme/sense_net` | `theme_sense_net.wav` |

## 관련 결정
- ADR-0032 (그래픽 노블 모드) — 기반

## 변경 이력

- 2026-06-20: Draft 작성 (Option 1 채택)
- 2026-06-20: Accepted — path fix + shibuya_traffic 매핑 추가 완료
  - 테스트 23개 추가 (`test_graphic_novel_audio.py`)
  - **Total tests**: 2233 → 2256 (+23)