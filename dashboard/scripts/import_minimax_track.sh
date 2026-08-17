#!/bin/bash
# MiniMax 에서 다운로드한 MP3 를 BGM 30초 + 풀 트랙 으로 분리 + 대시보드 통합
# Usage: ./import_minimax_track.sh <theme_name> <path/to/downloaded.mp3>
# 예:   ./import_minimax_track.sh chiba ~/Downloads/chiba.mp3

set -e

if [ $# -ne 2 ]; then
  echo "Usage: $0 <theme_name> <downloaded.mp3>"
  echo "예:  $0 chiba ~/Downloads/chiba.mp3"
  exit 1
fi

THEME="$1"
SRC="$2"
SND="/Users/emilio/projects/Projects/Game/wet_run/dashboard/sounds"
FULL_DIR="$SND/full"
BGM_FILE="$SND/theme_${THEME}.wav"
FULL_FILE="$FULL_DIR/theme_${THEME}.wav"

echo "=== [$THEME] MiniMax 트랙 처리 ==="

# 1. 풀 트랙 보관
mkdir -p "$FULL_DIR"
cp "$SRC" "$FULL_FILE"
DUR_FULL=$(afinfo "$FULL_FILE" 2>&1 | grep "estimated duration" | awk '{print $3}')
echo "  풀 트랙 → $FULL_FILE ($DUR_FULL 초)"

# 2. 백업 (기존 v1 또는 이전 BGM 보존)
[ -f "$BGM_FILE" ] && cp "$BGM_FILE" "$SND/theme_${THEME}.v1_backup.wav"

# 3. 30초 BGM trim + 정규화
ffmpeg -y -ss 5 -t 30 -i "$SRC" \
  -af "afade=t=in:st=0:d=0.5,afade=t=out:st=28.5:d=1.5,loudnorm=I=-16:TP=-1.5:LRA=11" \
  -ar 44100 -ac 2 -c:a pcm_s16le \
  "$BGM_FILE" 2>&1 | grep -E "size=|Output" | head -2
echo "  BGM 30초 → $BGM_FILE"

# 4. 검증
afinfo "$BGM_FILE" 2>&1 | grep "estimated duration"
python3 -c "
import wave, math, struct
with wave.open('$BGM_FILE', 'rb') as wf:
    n = wf.getnframes(); ch = wf.getnchannels()
    raw = wf.readframes(n)
samples = struct.unpack(f'<{n*ch}h', raw)
rms = math.sqrt(sum(s*s for s in samples) / len(samples))
print(f'  BGM RMS: {20*math.log10(rms/32768):+.1f} dBFS')
"

echo "  ✅ 완료 — 브라우저에서 즉시 재생 가능"
echo "    (전체 트랙 갤러리 갱신은 sound.html 직접 편집: pending → active + src 추가)"
