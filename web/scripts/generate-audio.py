#!/usr/bin/env python3
"""Generate placeholder audio files for wet_run web game.

Creates silent WAV files for all required BGM tracks and SFX.
These serve as placeholders until real audio is added.
"""

import struct
import wave
from pathlib import Path


def create_silent_wav(filepath: Path, duration_seconds: float, sample_rate: int = 44100) -> None:
    """Create a minimal silent WAV file.
    
    Args:
        filepath: Output file path
        duration_seconds: Duration of audio in seconds
        sample_rate: Sample rate in Hz (default 44100)
    """
    num_samples = int(sample_rate * duration_seconds)
    num_channels = 1
    sample_width = 2  # 16-bit
    
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with wave.open(str(filepath), 'w') as wav_file:
        wav_file.setnchannels(num_channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        # Write silence (zeros)
        wav_file.writeframes(b'\x00\x00' * num_samples)
    
    print(f"Created: {filepath}")


def main() -> None:
    """Generate all audio files."""
    base_dir = Path(__file__).parent.parent / "public" / "sounds"
    bgm_dir = base_dir / "bgm"
    sfx_dir = base_dir / "sfx"
    
    # BGM tracks (30 seconds each for looping music)
    bgm_tracks = [
        ("title", 30),
        ("menu", 30),
        ("exploration", 30),
        ("combat_normal", 30),
        ("combat_boss", 30),
        ("combat_multi", 30),
        ("shop", 30),
        ("ending_good", 30),
        ("ending_bad", 30),
        ("ending_neutral", 30),
        ("death", 10),
        ("victory", 10),
        ("event_special", 20),
        ("ambient_low", 30),
        ("ambient_high", 30),
    ]
    
    # SFX (short sounds, 0.5 seconds each)
    sfx_sounds = [
        "click",
        "confirm",
        "back",
        "equip",
        "heal",
        "damage",
        "attack",
        "ice_break",
        "loot_drop",
        "credit_gain",
        "credit_spend",
        "death",
        "victory",
        "boss_intro",
        "phase_change",
    ]
    
    print(f"Generating BGM tracks in {bgm_dir}...")
    for name, duration in bgm_tracks:
        create_silent_wav(bgm_dir / f"{name}.wav", duration)
    
    print(f"\nGenerating SFX in {sfx_dir}...")
    for name in sfx_sounds:
        create_silent_wav(sfx_dir / f"{name}.wav", 0.5)
    
    print(f"\nAudio generation complete!")
    print(f"BGM: {len(bgm_tracks)} files")
    print(f"SFX: {len(sfx_sounds)} files")
    print(f"\nTotal: {len(bgm_tracks) + len(sfx_sounds)} audio files created")


if __name__ == "__main__":
    main()
