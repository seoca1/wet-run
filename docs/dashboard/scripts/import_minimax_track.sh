#!/bin/bash
# MiniMax 에서 다운로드한 트랙을 풀 트랙(MP3) + 30초 BGM(WAV) 으로 분리 + 대시보드/게임 통합
#
# Usage: ./import_minimax_track.sh <theme_name> <path/to/downloaded.mp3>
# 예:   ./import_minimax_track.sh chiba ~/Downloads/chiba.mp3
#
# 산출물 (ADR-0253 정본 규약):
#   docs/dashboard/sounds/full/theme_<theme>.mp3   풀 트랙 — tracked 정본.
#                                                대시보드 갤러리 + web/public/sounds/ 심볼릭 링크가 여기서 읽는다.
#   docs/dashboard/sounds/theme_<theme>.wav        30초 BGM — 로컬 전용 (gitignore).
#                                                트랜스코딩 원본 보관용이며 런타임 소비자는 없다.
#   web/public/sounds/theme_<theme>.mp3            게임 심볼릭 링크 (없으면 생성).
#
# 주의: 풀 트랙이 이미 있으면 덮어쓴다. 이전 세대의 `.v1_backup.wav` 규약은
# ADR-0253 에서 폐기되었다(백업 파일 13개 삭제, tracked 오디오 263MB -> 117.5MB).

set -e

if [ $# -ne 2 ]; then
  echo "Usage: $0 <theme_name> <downloaded.mp3>"
  echo "예:  $0 chiba ~/Downloads/chiba.mp3"
  exit 1
fi

THEME="$1"
SRC="$2"

if [ ! -f "$SRC" ]; then
  echo "❌ 입력 파일 없음: $SRC"
  exit 1
fi

# 스크립트 위치 기준 경로 (하드코딩 절대경로 금지 — 2026-10-20 구조 개편 후 3회 drift)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

SND="$REPO_ROOT/docs/dashboard/sounds"
FULL_DIR="$SND/full"
BGM_FILE="$SND/theme_${THEME}.wav"
FULL_FILE="$FULL_DIR/theme_${THEME}.mp3"
GAME_LINK="$REPO_ROOT/web/public/sounds/theme_${THEME}.mp3"

echo "=== [$THEME] MiniMax 트랙 처리 ==="
echo "  repo root : $REPO_ROOT"

# 1. 풀 트랙 (MP3, 256 kbps) — tracked 정본
mkdir -p "$FULL_DIR"
ffmpeg -y -i "$SRC" -c:a libmp3lame -b:a 256k "$FULL_FILE" 2>&1 | grep -E "Output" | head -1
DUR_FULL=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$FULL_FILE" 2>/dev/null | cut -d. -f1)
echo "  풀 트랙 → $FULL_FILE (${DUR_FULL}초)"

# 2. 30초 BGM (WAV) — 로컬 전용, 트랜스코딩 원본 보관용
ffmpeg -y -ss 5 -t 30 -i "$SRC" \
  -af "afade=t=in:st=0:d=0.5,afade=t=out:st=28.5:d=1.5,loudnorm=I=-16:TP=-1.5:LRA=11" \
  -ar 44100 -ac 2 -c:a pcm_s16le \
  "$BGM_FILE" 2>&1 | grep -E "size=|Output" | head -1
echo "  BGM 30초 → $BGM_FILE (로컬 전용)"

# 3. 게임 심볼릭 링크 (web/public/sounds/ → docs/dashboard/sounds/full/)
mkdir -p "$(dirname "$GAME_LINK")"
if [ ! -e "$GAME_LINK" ]; then
  ln -s "../../../docs/dashboard/sounds/full/theme_${THEME}.mp3" "$GAME_LINK"
  echo "  게임 링크 → $GAME_LINK"
else
  echo "  게임 링크 이미 존재 (건너뜀): $GAME_LINK"
fi

# 4. 검증
echo "  풀 트랙 길이: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$FULL_FILE" 2>/dev/null | cut -d. -f1)초"
python3 -c "
import wave, math, struct
with wave.open('$BGM_FILE', 'rb') as wf:
    n = wf.getnframes(); ch = wf.getnchannels()
    raw = wf.readframes(n)
samples = struct.unpack(f'<{n*ch}h', raw)
rms = math.sqrt(sum(s*s for s in samples) / len(samples))
print(f'  BGM RMS: {20*math.log10(rms/32768):+.1f} dBFS')
"

echo "  ✅ 완료 — 대시보드에서 즉시 재생 가능"
echo "    (갤러리 노출은 docs/dashboard/sound.html 에 <audio src> 항목 추가 필요 — 정본은 sounds/full/)"
