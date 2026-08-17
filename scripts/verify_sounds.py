#!/usr/bin/env python3
"""터미널에서 BGM WAV 파일 검증/재생 도구.

Usage:
  python3 verify_sounds.py                  # 12개 WAV 검증 + 오디오 디바이스 정보
  python3 verify_sounds.py --play N         # N번 (0~11) WAV를 직접 재생 (3초)
  python3 verify_sounds.py --play-all       # 12개 모두 순차 재생 (각 3초)
"""
from __future__ import annotations
import argparse
import sys
import wave
import subprocess
import os
import struct
import math
from pathlib import Path

SOUNDS_DIR = Path(__file__).resolve().parent.parent / "dashboard" / "sounds"
if not SOUNDS_DIR.exists():
    # Fallback: workspace root
    SOUNDS_DIR = Path("/Users/emilio/projects/Projects/Game/wet_run/dashboard/sounds")


def analyze(wav_path: Path) -> dict:
    """WAV 분석: duration, sample rate, channels, RMS, peak, silent 여부."""
    with wave.open(str(wav_path), "rb") as wf:
        nframes = wf.getnframes()
        framerate = wf.getframerate()
        nchannels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        duration = nframes / framerate
        raw = wf.readframes(nframes)

    # RMS / peak over full file
    if sampwidth == 2:
        samples = struct.unpack(f"<{nframes * nchannels}h", raw)
    elif sampwidth == 1:
        samples = struct.unpack(f"<{nframes * nchannels}b", raw)
    elif sampwidth == 4:
        samples = struct.unpack(f"<{nframes * nchannels}i", raw)
    else:
        return {"error": f"unsupported sampwidth {sampwidth}"}

    if not samples:
        return {"error": "empty file"}
    sum_sq = sum(s * s for s in samples)
    rms = math.sqrt(sum_sq / len(samples))
    peak = max(abs(s) for s in samples)
    # 16-bit max = 32768. RMS > 50 → audible. RMS < 5 → silent.
    is_silent = rms < 5
    return {
        "duration": duration,
        "sample_rate": framerate,
        "channels": nchannels,
        "sampwidth": sampwidth,
        "rms": rms,
        "peak": peak,
        "silent": is_silent,
        "size": len(raw),
        "audible": not is_silent
    }


def list_audio_outputs() -> str:
    """macOS 의 현재 출력 디바이스."""
    r = subprocess.run(["system_profiler", "SPAudioDataType"], capture_output=True, text=True)
    lines = [l.strip() for l in r.stdout.split("\n") if "Default Output Device: Yes" in l or "Manufacturer:" in l]
    return "\n".join(lines[:6]) if lines else "(no audio info)"


def verify_all():
    wavs = sorted(SOUNDS_DIR.glob("theme_*.wav"))
    if not wavs:
        print(f"No WAV files in {SOUNDS_DIR}", file=sys.stderr)
        sys.exit(1)

    print(f"=== 출력 디바이스 ===\n{list_audio_outputs()}\n")
    print(f"=== WAV 검증 ({len(wavs)}개) ===")
    print(f"{'#':>3}  {'파일':<32}  {'길이':<6}  {'SR':<7}  {'ch':<2}  {'RMS':<8}  {'Peak':<7}  {'상태'}")
    print("-" * 95)
    fails = 0
    for i, w in enumerate(wavs):
        try:
            info = analyze(w)
            status = "🔇 silent" if info["silent"] else "✅ audible"
            if info["silent"]:
                fails += 1
            print(f"{i:>3}  {w.name:<32}  {info['duration']:<6.2f}  {info['sample_rate']:<7}  {info['channels']:<2}  {info['rms']:<8.1f}  {info['peak']:<7}  {status}")
        except Exception as e:
            print(f"{i:>3}  {w.name:<32}  ERROR: {e}")
            fails += 1
    print("-" * 95)
    print(f"결과: {len(wavs) - fails}개 audible, {fails}개 silent")
    sys.exit(0 if fails == 0 else 1)


def play(idx: int):
    wavs = sorted(SOUNDS_DIR.glob("theme_*.wav"))
    if idx < 0 or idx >= len(wavs):
        print(f"Index {idx} out of range (0~{len(wavs)-1})", file=sys.stderr)
        sys.exit(1)
    w = wavs[idx]
    info = analyze(w)
    print(f"재생: {w.name}  ({info['duration']:.1f}s, RMS={info['rms']:.0f})")
    if info["silent"]:
        print(f"  ⚠️  이 파일은 silent 입니다 (RMS={info['rms']:.1f}). 출력 디바이스 / 볼륨 점검 필요.")
    sys.stdout.flush()
    subprocess.run(["afplay", str(w)])


def play_all():
    wavs = sorted(SOUNDS_DIR.glob("theme_*.wav"))
    print(f"순차 재생: {len(wavs)}개 (각 {analyze(wavs[0])['duration']:.1f}s)\n")
    for i, w in enumerate(wavs):
        info = analyze(w)
        print(f"[{i+1}/{len(wavs)}] {w.name}  RMS={info['rms']:.0f}", flush=True)
        if info["silent"]:
            print(f"  ⚠️  silent (출력 안 됨)")
        subprocess.run(["afplay", str(w)])


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--play", type=int, default=None, help="Play WAV at index N (0-based)")
    p.add_argument("--play-all", action="store_true")
    args = p.parse_args()

    if args.play is not None:
        play(args.play)
    elif args.play_all:
        play_all()
    else:
        verify_all()
