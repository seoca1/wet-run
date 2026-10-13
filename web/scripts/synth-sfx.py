#!/usr/bin/env python3
"""Procedurally generate the 7 missing wet_run web SFX files.

Targets (paths must match src/audio/manager.ts SFX_IDS):

  sounds/sfx/combat_block.wav          — low metallic thunk (decaying square+sine mix)
  sounds/sfx/combat_skill_strike.wav   — sharp down-chirp
  sounds/sfx/combat_skill_burst.wav    — noise burst with fast decay
  sounds/sfx/combat_skill_guard.wav    — soft up-chirp (shield shimmer)
  sounds/sfx/combat_skill_support.wav  — gentle two-tone blip
  sounds/sfx/movement_step.wav         — short filtered click
  sounds/sfx/movement_node.wav         — deep soft thump

Format: 44.1 kHz, 16-bit, mono, WAV PCM. Peak-normalized to ~ -6 dBFS
(amplitude 0.501). Each clip is wrapped in a 10 ms linear fade in/out so
Howler.js playback doesn't click at boundaries. No external deps.

This script is idempotent — re-running overwrites the 7 outputs and
prints duration + size for each so the operator (or a vitest file)
can sanity-check the bytes without a decoder.

Existing `scripts/generate-audio.py` only writes silent placeholders.
This module is the source of truth for the Tier 5 SFX set.
"""

from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path
from typing import Iterable

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

SAMPLE_RATE = 44100          # Hz
SAMPLE_WIDTH_BYTES = 2       # 16-bit PCM
CHANNELS = 1
PEAK_AMP = 0.501             # ~ -6 dBFS  (20 * log10(0.501) ≈ -6.0 dB)
FADE_MS = 10                 # boundary fade in/out
TWO_PI = 2.0 * math.pi

# Repo-relative paths — resolved from script location so the script can be
# run from anywhere via `python3 scripts/synth-sfx.py`.
SCRIPT_DIR = Path(__file__).resolve().parent
WEB_DIR = SCRIPT_DIR.parent
PUBLIC_DIR = WEB_DIR / "public"
SFX_DIR = PUBLIC_DIR / "sounds" / "sfx"


# --------------------------------------------------------------------------- #
# WAV writer
# --------------------------------------------------------------------------- #

def _write_wav(path: Path, samples_f32: Iterable[float]) -> tuple[float, int]:
    """Write a 16-bit mono PCM WAV from an iterable of normalized floats in
    [-1, 1]. Returns (duration_seconds, file_size_bytes)."""
    samples = list(samples_f32)
    n = len(samples)
    duration = n / SAMPLE_RATE
    # Convert float32 -> int16 with hard clip + peak normalize target.
    peak = max((abs(s) for s in samples), default=1.0) or 1.0
    # Scale to PEAK_AMP, then convert.
    scale = PEAK_AMP / peak if peak > 0 else 0.0
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH_BYTES)
        wf.setframerate(SAMPLE_RATE)
        # Pack in chunks to avoid building one massive bytes object.
        frames = bytearray()
        for s in samples:
            v = s * scale
            if v > 1.0:
                v = 1.0
            elif v < -1.0:
                v = -1.0
            frames.extend(struct.pack("<h", int(v * 32767)))
        wf.writeframes(bytes(frames))
    size = path.stat().st_size
    return duration, size


def _fade_in_out(samples: list[float], fade_seconds: float = FADE_MS / 1000.0) -> list[float]:
    """Apply linear fade-in / fade-out to remove boundary clicks."""
    fade_n = max(1, int(fade_seconds * SAMPLE_RATE))
    if fade_n * 2 >= len(samples):
        return samples
    for i in range(fade_n):
        g = i / fade_n
        samples[i] *= g
        samples[-(i + 1)] *= g
    return samples


# --------------------------------------------------------------------------- #
# DSP primitives
# --------------------------------------------------------------------------- #

def _exp_decay(t: float, half_life_s: float) -> float:
    """Exponential amplitude decay envelope. Returns 1.0 at t=0, halving every half_life_s."""
    return math.pow(0.5, t / half_life_s) if half_life_s > 0 else 0.0


def _noise(n: int, rng: random.Random) -> list[float]:
    return [rng.uniform(-1.0, 1.0) for _ in range(n)]


def _normalize(samples: list[float], peak_target: float = 1.0) -> list[float]:
    peak = max((abs(s) for s in samples), default=1.0) or 1.0
    if peak == 0:
        return samples
    g = peak_target / peak
    return [s * g for s in samples]


# --------------------------------------------------------------------------- #
# SFX synth recipes
# --------------------------------------------------------------------------- #

def sfx_combat_block(duration_s: float = 0.30) -> list[float]:
    """Low metallic thunk: decaying square+sine mix with a quick pitch drop."""
    n = int(duration_s * SAMPLE_RATE)
    rng = random.Random(0xB10C)
    samples: list[float] = [0.0] * n
    # Pitch sweep: starts high (160 Hz) and drops to ~95 Hz in the first 80 ms
    for i in range(n):
        t = i / SAMPLE_RATE
        # Exponential amplitude decay (half-life 60 ms)
        env = _exp_decay(t, 0.060)
        if env < 1e-4:
            break
        # Pitch sweep using closed-form phase integral of an exponential.
        # We approximate f(t) = f0 * exp(-k*t); phase phi(t) = integral f0*exp(-k*s) ds.
        f0 = 165.0
        k = math.log(165.0 / 92.0) / 0.080   # ~160 Hz -> 92 Hz over 80 ms
        if t < 0.080:
            phase = (f0 / k) * (1.0 - math.exp(-k * t))
        else:
            # After 80 ms: phase at 80 ms + (t - 0.080) * 92 Hz
            phi_80 = (f0 / k) * (1.0 - math.exp(-k * 0.080))
            phase = phi_80 + 92.0 * (t - 0.080)
        sine = math.sin(TWO_PI * phase)
        # Square at the current pitch (clipped), gives the metallic edge.
        sq = 1.0 if math.sin(TWO_PI * phase) >= 0 else -1.0
        # Tiny bit of jitter (random harmonic) for metallic feel.
        jitter = rng.uniform(-0.05, 0.05) * math.sin(TWO_PI * 1500 * t)
        samples[i] = env * (0.55 * sine + 0.35 * sq + jitter)
    return samples


def sfx_combat_skill_strike(duration_s: float = 0.18) -> list[float]:
    """Sharp down-chirp: pitch sweeps from ~900 Hz down to ~120 Hz in 120 ms,
    hard amplitude envelope with quick attack."""
    n = int(duration_s * SAMPLE_RATE)
    samples: list[float] = [0.0] * n
    # Phase via closed-form exponential sweep: f(t) = f0 * exp(-k*t)
    f0 = 900.0
    f1 = 120.0
    sweep_dur = 0.120
    k = math.log(f0 / f1) / sweep_dur
    phi_sweep_end = (f0 / k) * (1.0 - math.exp(-k * sweep_dur))
    for i in range(n):
        t = i / SAMPLE_RATE
        if t < sweep_dur:
            phase = (f0 / k) * (1.0 - math.exp(-k * t))
        else:
            phase = phi_sweep_end + f1 * (t - sweep_dur)
        # AM envelope: 3 ms attack, exponential release.
        attack = min(1.0, t / 0.003)
        release = _exp_decay(max(0.0, t - sweep_dur), 0.025)
        samples[i] = 0.85 * attack * release * math.sin(TWO_PI * phase)
    return samples


def sfx_combat_skill_burst(duration_s: float = 0.35) -> list[float]:
    """Noise burst with fast decay + band-pass-ish character via one-pole
    high-pass at 1kHz. Exp half-life 70 ms."""
    n = int(duration_s * SAMPLE_RATE)
    rng = random.Random(0xB57)
    raw = _noise(n, rng)
    # 1-pole high-pass: y[n] = x[n] - x[n-1] + R * y[n-1], R = 0.95
    R = 0.95
    prev_x = 0.0
    prev_y = 0.0
    hp: list[float] = []
    for x in raw:
        y = x - prev_x + R * prev_y
        prev_x = x
        prev_y = y
        hp.append(y)
    # Normalize + apply decay envelope.
    hp = _normalize(hp, peak_target=0.9)
    out: list[float] = [0.0] * n
    for i, v in enumerate(hp):
        t = i / SAMPLE_RATE
        env = _exp_decay(t, 0.070)
        out[i] = v * env
    return out


def sfx_combat_skill_guard(duration_s: float = 0.32) -> list[float]:
    """Soft up-chirp shield shimmer: 200 Hz -> 1200 Hz in 200 ms,
    gentle sine + soft 5th harmonic, slow release."""
    n = int(duration_s * SAMPLE_RATE)
    samples: list[float] = [0.0] * n
    f0 = 200.0
    f1 = 1200.0
    sweep_dur = 0.200
    k = math.log(f1 / f0) / sweep_dur
    for i in range(n):
        t = i / SAMPLE_RATE
        # Exponential pitch sweep
        freq = f0 * math.exp(k * t) if t < sweep_dur else f1
        # Closed-form phase for exponential freq
        phase = (f0 / k) * (math.exp(k * min(t, sweep_dur)) - 1.0)
        # Gentle envelope: 20 ms attack, exp release with 250 ms half-life.
        attack = min(1.0, t / 0.020)
        release = _exp_decay(max(0.0, t - 0.020), 0.250)
        # Mix fundamental + light harmonic
        sig = 0.75 * math.sin(TWO_PI * phase) + 0.18 * math.sin(TWO_PI * 3 * phase)
        samples[i] = attack * release * sig
    return samples


def sfx_combat_skill_support(duration_s: float = 0.25) -> list[float]:
    """Gentle two-tone blip: 660 Hz then 990 Hz, 50 ms each, soft envelope."""
    n = int(duration_s * SAMPLE_RATE)
    samples: list[float] = [0.0] * n
    seg = 0.060
    for i in range(n):
        t = i / SAMPLE_RATE
        if t < seg:
            freq = 660.0
            env_local = math.sin(math.pi * (t / seg))  # half-sine window
        elif t < seg * 2:
            freq = 990.0
            u = (t - seg) / seg
            env_local = math.sin(math.pi * u)
        else:
            freq = 990.0
            env_local = math.sin(math.pi) * _exp_decay(t - 2 * seg, 0.050)
        # Phase resets on samples (continuous) — use mod.
        # We track phase incrementally.
        samples[i] = 0.0  # placeholder; filled below
    # Re-render with proper continuous phase.
    phase = 0.0
    freq = 660.0
    seg_n = int(seg * SAMPLE_RATE)
    for i in range(n):
        t = i / SAMPLE_RATE
        if t < seg:
            freq = 660.0
            env_local = math.sin(math.pi * (t / seg))
        elif t < seg * 2:
            freq = 990.0
            env_local = math.sin(math.pi * ((t - seg) / seg))
        else:
            freq = 990.0
            env_local = 0.0  # window zero past 2*seg
        phase += TWO_PI * freq / SAMPLE_RATE
        if phase > TWO_PI:
            phase -= TWO_PI
        samples[i] = 0.6 * env_local * math.sin(phase)
    return samples


def sfx_movement_step(duration_s: float = 0.15) -> list[float]:
    """Short filtered click: brief band-limited noise burst with high-shelf
    tilt — sounds like a single step on concrete."""
    n = int(duration_s * SAMPLE_RATE)
    rng = random.Random(0x573)
    raw = _noise(n, rng)
    # 1-pole low-pass (smooth): y[n] = x[n] + R*(y[n-1] - x[n])
    # Here we use a leaky integrator: y[n] = (1-a) * x[n] + a * y[n-1]
    a = 0.55  # higher = more lowpass
    lp: list[float] = []
    prev = 0.0
    for x in raw:
        prev = (1 - a) * x + a * prev
        lp.append(prev)
    # Envelope: 4 ms attack, exp half-life 22 ms.
    out: list[float] = [0.0] * n
    for i, v in enumerate(lp):
        t = i / SAMPLE_RATE
        env = min(1.0, t / 0.004) * _exp_decay(max(0.0, t - 0.004), 0.022)
        out[i] = v * env
    return out


def sfx_movement_node(duration_s: float = 0.45) -> list[float]:
    """Deep soft thump: 90 Hz sine with 25 Hz sub layer, exponential decay
    half-life 110 ms. Long enough for 'node entered' feedback."""
    n = int(duration_s * SAMPLE_RATE)
    samples: list[float] = [0.0] * n
    phase_a = 0.0
    phase_b = 0.0
    f1 = 90.0
    f2 = 25.0
    for i in range(n):
        t = i / SAMPLE_RATE
        env = _exp_decay(t, 0.110)
        phase_a += TWO_PI * f1 / SAMPLE_RATE
        phase_b += TWO_PI * f2 / SAMPLE_RATE
        if phase_a > TWO_PI:
            phase_a -= TWO_PI
        if phase_b > TWO_PI:
            phase_b -= TWO_PI
        sig = 0.55 * math.sin(phase_a) + 0.45 * math.sin(phase_b)
        # Touch of saturation for warmth
        if sig > 0.9:
            sig = 0.9 + (sig - 0.9) * 0.3
        elif sig < -0.9:
            sig = -0.9 + (sig + 0.9) * 0.3
        samples[i] = env * sig
    return samples


# --------------------------------------------------------------------------- #
# Spec table — output name -> (relpath from public/, duration_s, synth fn)
# --------------------------------------------------------------------------- #

SPEC: list[tuple[str, float]] = [
    ("combat_block.wav",          0.30, sfx_combat_block),
    ("combat_skill_strike.wav",   0.18, sfx_combat_skill_strike),
    ("combat_skill_burst.wav",    0.35, sfx_combat_skill_burst),
    ("combat_skill_guard.wav",    0.32, sfx_combat_skill_guard),
    ("combat_skill_support.wav",  0.25, sfx_combat_skill_support),
    ("movement_step.wav",         0.15, sfx_movement_step),
    ("movement_node.wav",         0.45, sfx_movement_node),
]


def synth_all() -> list[dict]:
    """Render every entry in SPEC and write to public/sounds/sfx/<name>.
    Returns a list of dicts describing each produced file (for tests)."""
    results: list[dict] = []
    for name, dur, fn in SPEC:
        raw = fn(dur)
        raw = _fade_in_out(raw, FADE_MS / 1000.0)
        out_path = SFX_DIR / name
        actual_dur, size = _write_wav(out_path, raw)
        # The on-disk filename in SFX_IDS uses prefix `sounds/sfx/`.
        rel = f"sounds/sfx/{name}"
        results.append({
            "name": name,
            "path": rel,
            "abs_path": str(out_path),
            "duration_s": actual_dur,
            "size_bytes": size,
            "sample_rate": SAMPLE_RATE,
            "channels": CHANNELS,
            "bit_depth": 16,
        })
    return results


def _format_report(results: list[dict]) -> str:
    lines = ["# synth-sfx.py — generated SFX report", ""]
    total_bytes = 0
    for r in results:
        total_bytes += r["size_bytes"]
        lines.append(
            f"- `{r['path']}` — {r['duration_s']:.3f}s, "
            f"{r['size_bytes']:,} bytes, "
            f"{r['sample_rate']}Hz / {r['channels']}ch / {r['bit_depth']}-bit"
        )
    lines.append("")
    lines.append(f"**Total: {len(results)} files, {total_bytes:,} bytes**")
    return "\n".join(lines) + "\n"


def main() -> None:
    print(f"Output dir: {SFX_DIR}")
    results = synth_all()
    print(_format_report(results))


if __name__ == "__main__":
    main()