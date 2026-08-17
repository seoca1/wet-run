"""MiniMax Music API client for cyberpunk BGM generation.

Requires MINIMAX_API_KEY environment variable.
Sign up: https://platform.minimaxi.com/

Usage:
    from wet_run.audio.minimax_music import generate_theme_bgm
    audio_bytes = generate_theme_bgm("matrix_rain")
    (Path("sounds") / "theme_matrix_rain.wav").write_bytes(audio_bytes)
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, cast

import requests

MINIMAX_API_URL = "https://api.minimaxi.com/v1/music_generation"
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")


THEME_PROMPTS: dict[str, str] = {
    "matrix_rain": (
        "Cyberpunk ambient synthwave, matrix rain, digital rain, rain on circuitry, "
        "low drone bass, subtle data streams, futuristic Tokyo night, cold electronic textures, "
        "Neuromancer atmosphere, slow pulsing arpeggios, 80s retro-futurism, minimal beats, "
        "cinematic tension, rain against neon, dark synthetic pad, lo-fi VHS aesthetic"
    ),
    "cyberspace": (
        "Deep cyberspace, corporate data fortress, neural network, cold digital void, "
        "Tessier-Ashpool ice, abstract geometric space, scanning frequencies, "
        "high-pitched sine waves, cold precision, corporate artificial intelligence, "
        "slow evolving ambient, glitch micro-textures, deep space digital, menacing undertones"
    ),
    "chiba": (
        "Chiba City neon streets, cyberpunk urban night, Japanese neon rain, wet pavement reflections, "
        "street-level hustle, console cowboy territory, colorful holographic signs, "
        "drum machine bass, jazzy hip-hop groove, street noise ambience, heavy reverb, "
        "bustling market, neon pink and blue, 80s synth, gritty urban atmosphere"
    ),
    "sense_net": (
        "Tessier-Ashpool corporate fortress, Sense/Net corporate data haven, royal ice palace, "
        "L00 header fanfare, classical-futuristic fusion, cold corporate power, "
        "organ and synthesizer blend, regal yet artificial, digital aristocracy, "
        "smooth jazz fusion, elegant danger, blue and gold neon, corporate throne room"
    ),
    "finn_office": (
        "The Finn's underground office, jazz club basement, smoky bar, noir atmosphere, "
        "smooth jazz piano, upright bass, saxophone blues, dim amber lighting, "
        "whispered deals, rain outside window, warm analog textures, retro 1940s noir meets cyberpunk, "
        "confidential conversations, easy listening with edge, analog warmth"
    ),
    "industrial": (
        "Cyberpunk combat music, intense industrial, factory floor, mechanical warfare, "
        "distorted synth, aggressive percussion, metal clanging, alarms, "
        "high tension combat, rapid fire drum machine, heavy bass drop, "
        "digital warfare, ICE breach, aggressive electronic, dark mechanical energy"
    ),
    "broadcast": (
        "Broadcast transmission, radio static, news feed, corporate announcement, "
        "smooth talk jazz, mid-tempo groove, professional delivery, polished corporate, "
        "AM radio crackle, news jingle, elevator jazz, calm professional tone, "
        "corporate message, background music for text, subtle urgency, clear signal"
    ),
    "loa_drum": (
        "Voodoo Loa drum ceremony, Baron Samedi, Haitian ritual, Afro-Caribbean percussion, "
        "hand drums, syncopated rhythms, spirit possession, graveyard celebrations, "
        "metallic shakers, call and response, raw organic drums, ceremonial intensity, "
        "West African diaspora, zombie realm, festive yet macabre, living dead music"
    ),
    "loa_drum_fade": (
        "Voodoo Loa ceremony fading, spirits departing, ritual ending, soft hand drums, "
        "echoing voices, candles dimming, peaceful departure, soul transitioning, "
        "gentle fade, ambient resonance, quiet aftermath, spirit world retreat, "
        "soft piano, dying embers, peaceful rest, gentle release"
    ),
    "loa_channel": (
        "Voodoo Loa channeling, spirit world connection, summoning ritual, electronic Obeah, "
        "digital spiritualism, distorted drums, haunting reverb, channeling otherworldly entities, "
        "spectral frequencies, Haitian Vodou meets cyberspace, mediumistic transmission, "
        "mysterious whispers, glowing sigils, dimensional rift, ancestral spirits online"
    ),
    "manarase_drone": (
        "Kumiko Manarase atmosphere, Japanese corporate elegance, cold beauty, Tokyo penthouse, "
        "long sustained notes, ambient pad, melancholic beauty, corporate twilight, "
        "soft synthesizer, peaceful yet distant, lonely high-rise, evening corporate Japan, "
        "contemplative, slow breathing pad, elegant desolation, corporate Zen"
    ),
    "hammer_alert": (
        "Flatline death music, clinical death, brain flatline beep, emergency alarm, "
        "cold hospital monitor, flat electronic tone, digital death, clinical finality, "
        "monotone beep, oppressive silence after, heart monitor flatline, technological death, "
        "no escape, corporate morgue, clinical冷酷, digital obituary"
    ),
}


def is_configured() -> bool:
    """Return True if MINIMAX_API_KEY is set."""
    return bool(MINIMAX_API_KEY and len(MINIMAX_API_KEY) > 5)


def generate_music(prompt: str, duration_seconds: int = 30) -> bytes | None:
    """Generate music via MiniMax API.

    Args:
        prompt: Music generation prompt describing the desired sound
        duration_seconds: Length of the generated audio (30-60 typical)

    Returns:
        Raw audio bytes (MP3 format) or None on failure
    """
    if not is_configured():
        print("[minimax_music] ERROR: MINIMAX_API_KEY not set")
        print("  Run: export MINIMAX_API_KEY=your_key_here")
        return None

    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "music-01",
        "prompt": prompt,
        "duration": duration_seconds,
        "response_format": "mp3",
    }

    try:
        print(f"[minimax_music] Generating {duration_seconds}s track...")
        response = requests.post(
            MINIMAX_API_URL,
            headers=headers,
            json=cast(Any, payload),
            timeout=120,
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("data", {}).get("audio_url"):
                audio_url = result["data"]["audio_url"]
                audio_resp = requests.get(audio_url, timeout=60)
                if audio_resp.status_code == 200:
                    print(f"[minimax_music] Downloaded {len(audio_resp.content)} bytes")
                    return bytes(audio_resp.content)
            elif result.get("data", {}).get("audio_base64"):
                import base64

                return base64.b64decode(result["data"]["audio_base64"])
            else:
                print(f"[minimax_music] Unexpected response: {result}")
                return None
        else:
            print(f"[minimax_music] API error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"[minimax_music] Exception: {e}")
        return None
    return None


def generate_theme_bgm(theme_id: str, output_path: Path, duration_seconds: int = 30) -> bool:
    """Generate a BGM theme file from its theme ID.

    Args:
        theme_id: One of the THEME_PROMPTS keys (e.g. "matrix_rain")
        output_path: Where to save the generated file
        duration_seconds: Track length

    Returns:
        True if file was saved successfully
    """
    prompt = THEME_PROMPTS.get(theme_id)
    if not prompt:
        print(f"[minimax_music] Unknown theme: {theme_id}")
        return False

    audio_bytes = generate_music(prompt, duration_seconds)
    if audio_bytes is None:
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(audio_bytes)
    print(f"[minimax_music] Saved: {output_path} ({len(audio_bytes):,} bytes)")
    return True


def generate_all_themes(
    output_dir: Path = Path("sounds"), duration_seconds: int = 30
) -> dict[str, bool]:
    """Generate all 12 BGM themes.

    Args:
        output_dir: Directory to save generated files
        duration_seconds: Length per track

    Returns:
        Dict of theme_id -> success boolean
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for theme_id in THEME_PROMPTS:
        filename = f"theme_{theme_id}.wav"
        output_path = output_dir / filename
        success = generate_theme_bgm(theme_id, output_path, duration_seconds)
        results[theme_id] = success
        if success:
            time.sleep(1)
    return results


if __name__ == "__main__":
    import sys

    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("sounds")
    results = generate_all_themes(output_dir=output)
    print("\n--- Summary ---")
    for theme_id, ok in results.items():
        print(f"  {'✓' if ok else '✗'} {theme_id}")
