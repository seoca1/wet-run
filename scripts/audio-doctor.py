#!/usr/bin/env python3
"""macOS 오디오 진단·전환·검증 CLI.

Subcommands (기본: status):
  python3 audio-doctor.py status           # 디바이스 + 기본 출력 표시
  python3 audio-doctor.py list             # 모든 출력 디바이스 나열
  python3 audio-doctor.py switch NAME      # 출력 디바이스 전환
  python3 audio-doctor.py test [N]         # 현재 디바이스로 1초 사운드 (또는 N초)
  python3 audio-doctor.py cycle            # 모든 디바이스 순회하며 각 1초 재생
  python3 audio-doctor.py doctor           # 한눈에 진단 + 권장 다음 액션
"""
from __future__ import annotations
import argparse
import subprocess
import sys
import re
import shutil
from pathlib import Path

SOUND_DIR = Path("/Users/emilio/projects/Projects/Game/wet_run/dashboard/sounds")
SAS = shutil.which("SwitchAudioSource") or "/opt/homebrew/bin/SwitchAudioSource"


def run(cmd: list[str], check=True) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def list_devices() -> list[str]:
    """SwitchAudioSource -a 출력."""
    out = run([SAS, "-a"])
    return [d.strip() for d in out.split("\n") if d.strip()]


def current_device() -> str:
    return run([SAS, "-c"])


def switch_device(name: str):
    run([SAS, "-s", name])


def play_test(seconds: int = 1):
    """현재 디바이스로 1초 사운드 재생. 짧은 hammer_alert 우선 사용."""
    test_file = SOUND_DIR / "theme_hammer_alert.wav"
    if not test_file.exists():
        sys.exit(f"Test file not found: {test_file}")
    subprocess.run(["afplay", "-v", "0.6", "-t", str(seconds), str(test_file)])


def status():
    devs = list_devices()
    cur = current_device()
    print(f"=== 현재 출력 디바이스 ===\n  ★ {cur}\n")
    print("=== 모든 출력 디바이스 ===")
    for i, d in enumerate(devs):
        marker = "★" if d == cur else " "
        print(f"  {marker} [{i}] {d}")


def cycle():
    devs = list_devices()
    cur = current_device()
    print(f"=== {len(devs)}개 디바이스 순회 테스트 (각 1초) ===\n원래 디바이스로 복귀합니다.\n")
    for i, d in enumerate(devs):
        print(f"[{i+1}/{len(devs)}] {d} 로 전환 + 1초 재생...", flush=True)
        switch_device(d)
        play_test(1)
    print(f"\n[복귀] {cur} 로 다시 전환")
    switch_device(cur)
    print("완료.")


def doctor():
    """한눈에 진단."""
    print("=== Audio Doctor ===\n")
    cur = current_device()
    devs = list_devices()
    print(f"현재 출력: ★ {cur}")
    print(f"전체 디바이스: {len(devs)} 개")
    for d in devs:
        marker = "★" if d == cur else " "
        print(f"  {marker} {d}")

    print("\n=== 출력 디바이스 활동 확인 ===")
    r = subprocess.run(["system_profiler", "SPAudioDataType"], capture_output=True, text=True)
    lines = r.stdout.split("\n")
    seen_dev = None
    active_devs = set()
    for ln in lines:
        m = re.match(r"^\s*([\w\s]+):\s*$", ln)
        if m and len(m.group(1).strip()) > 3 and ":" not in m.group(1):
            # 새로운 디바이스 시작 (transport 직전 라인)
            pass
        if "Transport:" in ln:
            t = ln.split(":", 1)[1].strip()
            print(f"  Transport: {t}")

    print("\n=== 권장 진단 ===")
    print(f"  1. HDMI 모니터 자체 OSD 점검 — 볼륨/Mute/입력소스")
    print(f"  2. 모니터 전원 OFF → 5초 → ON (HDMI 핸드셰이크 리셋)")
    print(f"  3. 격리 테스트:")
    print(f"     python3 {Path(__file__).name} switch \"Mac mini 스피커\"")
    print(f"     python3 {Path(__file__).name} test 1")
    print(f"     → 들리면 = HDMI 디바이스 모니터 자체 문제")
    print(f"     → 안 들리면 = 시스템 전체 음소거 가능성 (시스템 설정 점검)")
    print(f"  4. 순회 테스트 (모든 디바이스 자동 확인):")
    print(f"     python3 {Path(__file__).name} cycle")


def main():
    p = argparse.ArgumentParser(description="macOS Audio Doctor")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("status", help="Show current + all devices")
    sub.add_parser("list", help="Just list devices")
    sub.add_parser("doctor", help="Full diagnostic report")
    sub.add_parser("cycle", help="Cycle through every device playing 1s each")

    sw = sub.add_parser("switch", help="Switch to device by name (or partial)")
    sw.add_argument("name")

    t = sub.add_parser("test", help="Play test sound on current device")
    t.add_argument("seconds", nargs="?", type=int, default=1)

    args = p.parse_args()

    try:
        if args.cmd == "status" or args.cmd is None:
            status()
        elif args.cmd == "list":
            for d in list_devices():
                print(d)
        elif args.cmd == "doctor":
            doctor()
        elif args.cmd == "cycle":
            cycle()
        elif args.cmd == "switch":
            target = args.name
            # 부분 일치 지원
            matches = [d for d in list_devices() if target.lower() in d.lower()]
            if not matches:
                print(f"'{target}' 매칭 디바이스 없음.")
                print("사용 가능:", list_devices())
                sys.exit(1)
            if len(matches) > 1:
                print(f"'{target}' 매칭이 여러 개:")
                for d in matches:
                    print(f"  - {d}")
                sys.exit(1)
            print(f"전환: {matches[0]}")
            switch_device(matches[0])
            print(f"현재 디바이스: {current_device()}")
        elif args.cmd == "test":
            print(f"재생: {args.seconds}초 (현재 디바이스: {current_device()})")
            play_test(args.seconds)
            print("완료.")
        else:
            p.print_help()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
