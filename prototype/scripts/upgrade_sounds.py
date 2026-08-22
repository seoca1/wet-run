#!/usr/bin/env python3
"""Generate cyberpunk-style sound effects using ffmpeg.

This script replaces the synthesized placeholder WAV files with
higher-quality ffmpeg-generated sounds that have a Gibson-inspired
cyberpunk aesthetic: electronic, synthetic, slightly distorted.
"""

import subprocess
from pathlib import Path

SOUNDS_DIR = Path(__file__).parent.parent / "data" / "sounds_test"
FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"


def run(cmd: list[str], cwd: Path | None = None) -> bool:
    """Run a command, return True if successful."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def generate(
    output: Path,
    duration: float,
    *ffmpeg_args: str,
    sample_rate: int = 44100,
) -> bool:
    """Generate a sound file using ffmpeg."""
    cmd = [
        FFMPEG,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r={sample_rate}:cl=stereo",
        "-t",
        str(duration),
        *ffmpeg_args,
        "-ar",
        str(sample_rate),
        "-ac",
        "2",
        str(output),
    ]
    return run(cmd)


def generate_sine(
    output: Path,
    freq: float,
    duration: float,
    volume: float = 0.5,
    fade: float = 0.0,
) -> bool:
    """Generate a sine wave with optional fade."""
    fade_in = min(0.05, duration * 0.1)
    fade_out = min(0.05, duration * 0.1)
    cmd = [
        FFMPEG,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency={freq}:duration={duration}",
        "-af",
        f"volume={volume},afade=t=in:st=0:d={fade_in},afade=t=out:st={duration - fade_out}:d={fade_out}",
        "-ar",
        "44100",
        str(output),
    ]
    return run(cmd)


def generate_combat_hit(output: Path, crit: bool = False) -> bool:
    """Generate a combat hit sound - punchy impact with distortion."""
    duration = 0.15 if not crit else 0.25
    pitch = 180 if not crit else 220
    vol = 0.6 if not crit else 0.8

    cmd = [
        FFMPEG,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency={pitch}:duration={duration}",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency={pitch * 0.5}:duration={duration}",
        "-f",
        "lavfi",
        "-i",
        f"anoisesrc=d={duration}:a=0.1",
        "-filter_complex",
        "[0:a][1:a]amix=weights=0.6 0.4[a];[a][2:a]volume=1:eval=frame[c];[c]afftfilt=real='hypot(re,im)*2':imag='hypot(re,im)*2'[out]",
        "-map",
        "[out]",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-af",
        f"volume={vol}",
        str(output),
    ]
    return run(cmd)


def generate_combat_block(output: Path) -> bool:
    """Metallic clang for blocking."""
    duration = 0.12
    cmd = [
        FFMPEG,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=800:duration={duration}",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=1200:duration={duration}",
        "-f",
        "lavfi",
        "-i",
        f"anoisesrc=d={duration}:a=0.15",
        "-filter_complex",
        "[0:a][1:a]amix=weights=0.5 0.3[a];[a][2:a]bandpass=f=900:t=w:w=0.3[c];[c]volume=0.7[out]",
        "-map",
        "[out]",
        "-ar",
        "44100",
        "-ac",
        "2",
        str(output),
    ]
    return run(cmd)


def generate_combat_victory(output: Path) -> bool:
    """Triumphant rising tone - synthetic fanfare."""
    duration = 0.7
    cmd = [
        FFMPEG,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=330:duration={duration}",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=440:duration={duration}",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=550:duration={duration}",
        "-filter_complex",
        "[0:a]volume=0.3[a];[1:a]volume=0.3[b];[2:a]volume=0.3[c];"
        "[a]aformat=sample_fmts=fltp:sample_rates=44100,tremolo=f=4:d=0.4[aa];"
        "[b]aformat=sample_fmts=fltp:sample_rates=44100,tremolo=f=5:d=0.3[bb];"
        "[c]aformat=sample_fmts=fltp:sample_rates=44100,tremolo=f=6:d=0.5[cc];"
        "[aa][bb][cc]amix=weights=1 1 1,afade=t=in:st=0:d=0.1,afade=t=out:st={duration-0.15}:d=0.15[out]",
        "-map",
        "[out]",
        "-ar",
        "44100",
        "-ac",
        "2",
        str(output),
    ]
    return run(cmd)


def generate_combat_defeat(output: Path) -> bool:
    """Low ominous descending tone."""
    duration = 0.9
    cmd = [
        FFMPEG,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=200:duration={duration}",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=100:duration={duration}",
        "-f",
        "lavfi",
        "-i",
        f"anoisesrc=d={duration}:a=0.2",
        "-filter_complex",
        "[0:a][1:a]amix=weights=0.4 0.6[a];[a][2:a]volume=0.5,afade=t=in:st=0:d=0.1,afade=t=out:st={duration-0.3}:d=0.3[out]",
        "-map",
        "[out]",
        "-ar",
        "44100",
        "-ac",
        "2",
        str(output),
    ]
    return run(cmd)


def generate_skill_sound(output: Path, skill_type: str) -> bool:
    """Generate skill sounds: physical, magic, heal, buff, debuff."""
    configs = {
        "physical": (0.2, 250, 0.6, "distortion"),
        "magic": (0.3, 440, 0.5, "vibrato"),
        "heal": (0.4, 528, 0.4, "tremolo"),
        "buff": (0.25, 660, 0.5, "tremolo"),
        "debuff": (0.35, 150, 0.55, "distortion"),
    }
    duration, freq, vol, effect = configs.get(skill_type, (0.2, 300, 0.5, ""))

    effect_filter = {
        "distortion": f"afftfilt=real='hypot(re,im)*1.5':imag='hypot(re,im)*0.5',volume={vol}",
        "vibrato": f"vibrato=f=6:d=0.3,volume={vol}",
        "tremolo": f"tremolo=f=8:d=0.4,volume={vol}",
    }.get(effect, f"volume={vol}")

    cmd = [
        FFMPEG,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency={freq}:duration={duration}",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency={freq * 1.5}:duration={duration}",
        "-filter_complex",
        f"[0:a][1:a]amix=weights=0.6 0.4[a];[a]{effect_filter}[out]",
        "-map",
        "[out]",
        "-ar",
        "44100",
        "-ac",
        "2",
        str(output),
    ]
    return run(cmd)


def generate_stun(output: Path) -> bool:
    """Stun sound - sharp high ping."""
    duration = 0.28
    cmd = [
        FFMPEG,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=1200:duration={duration}",
        "-f",
        "lavfi",
        "-i",
        f"anoisesrc=d={duration}:a=0.05",
        "-filter_complex",
        "[0:a][1:a]amix=weights=0.8 0.2[a];[a]highpass=f=500,volume=0.6,afade=t=in:st=0:d=0.02,afade=t=out:st={duration-0.08}:d=0.08[out]",
        "-map",
        "[out]",
        "-ar",
        "44100",
        "-ac",
        "2",
        str(output),
    ]
    return run(cmd)


def generate_ui_beep(output: Path, beep_type: str = "select") -> bool:
    """UI beeps - clean with slight digital character."""
    configs = {
        "select": (0.05, 880, 0.3),
        "confirm": (0.1, 1100, 0.4),
        "cancel": (0.12, 660, 0.35),
        "error": (0.2, 220, 0.5),
        "notification": (0.15, 1320, 0.4),
    }
    duration, freq, vol = configs.get(beep_type, (0.1, 800, 0.3))

    cmd = [
        FFMPEG,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency={freq}:duration={duration}",
        "-af",
        f"afade=t=in:st=0:d=0.005,afade=t=out:st={duration - 0.01}:d=0.01,volume={vol}",
        "-ar",
        "44100",
        "-ac",
        "2",
        str(output),
    ]
    return run(cmd)


def generate_movement_step(output: Path) -> bool:
    """Electronic footstep - soft digital tap."""
    duration = 0.06
    cmd = [
        FFMPEG,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"anoisesrc=d={duration}:a=0.15",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=200:duration={duration}",
        "-filter_complex",
        "[0:a][1:a]amix=weights=0.6 0.4[a];[a]highpass=f=300,lowpass=f=2000,volume=0.5[out]",
        "-map",
        "[out]",
        "-ar",
        "44100",
        "-ac",
        "2",
        str(output),
    ]
    return run(cmd)


def generate_jack_in(output: Path) -> bool:
    """Jack-in sound - electronic zap with rising tone."""
    duration = 0.55
    cmd = [
        FFMPEG,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=100:duration={duration}",
        "-f",
        "lavfi",
        "-i",
        f"anoisesrc=d={duration}:a=0.1",
        "-filter_complex",
        f"[0:a]volume=0.4,tremolo=f=20:d=0.1[a];[a][1:a]amix=weights=0.7 0.3,asetrate=44100*1.5,afade=t=in:st=0:d=0.05,afade=t=out:st={duration - 0.1}:d=0.1[out]",
        "-map",
        "[out]",
        "-ar",
        "44100",
        "-ac",
        "2",
        str(output),
    ]
    return run(cmd)


def generate_jack_out(output: Path) -> bool:
    """Jack-out sound - descending electronic buzz."""
    duration = 0.55
    cmd = [
        FFMPEG,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=800:duration={duration}",
        "-f",
        "lavfi",
        "-i",
        f"anoisesrc=d={duration}:a=0.08",
        "-filter_complex",
        f"[0:a]volume=0.35,tremolo=f=15:d=0.15[a];[a][1:a]amix=weights=0.6 0.4,asetrate=44100*0.8,afade=t=in:st=0:d=0.05,afade=t=out:st={duration - 0.1}:d=0.1[out]",
        "-map",
        "[out]",
        "-ar",
        "44100",
        "-ac",
        "2",
        str(output),
    ]
    return run(cmd)


def generate_data_extract(output: Path) -> bool:
    """Data extraction - ascending digital chimes."""
    duration = 0.3
    cmd = [
        FFMPEG,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=440:duration={duration}",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=660:duration={duration}",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=880:duration={duration}",
        "-filter_complex",
        "[0:a]volume=0.25,afade=t=in:st=0:d=0.05[a];[1:a]volume=0.25,afade=t=in:st=0.1:d=0.05[b];[2:a]volume=0.25,afade=t=in:st=0.2:d=0.05[c];[a][b][c]amix=weights=1 1 1[out]",
        "-map",
        "[out]",
        "-ar",
        "44100",
        "-ac",
        "2",
        str(output),
    ]
    return run(cmd)


def generate_static(output: Path, duration: float = 0.5) -> bool:
    """Radio static - filtered noise burst."""
    cmd = [
        FFMPEG,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"anoisesrc=d={duration}:a=0.4",
        "-af",
        f"bandpass=f=2000:t=w:w=0.5,volume=0.4,afade=t=in:st=0:d=0.02,afade=t=out:st={duration - 0.05}:d=0.05",
        "-ar",
        "44100",
        "-ac",
        "2",
        str(output),
    ]
    return run(cmd)


def generate_black_ice_roar(output: Path) -> bool:
    """Black ICE roar - ominous low rumble with distortion."""
    duration = 0.7
    cmd = [
        FFMPEG,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=55:duration={duration}",
        "-f",
        "lavfi",
        "-i",
        f"anoisesrc=d={duration}:a=0.3",
        "-filter_complex",
        f"[0:a]volume=0.5[a];[1:a]lowpass=f=300,volume=0.4[b];[a][b]amix=weights=0.6 0.4,afftfilt=real='hypot(re,im)*1.3':imag='hypot(re,im)*0.7,afade=t=in:st=0:d=0.1,afade=t=out:st={duration - 0.15}:d=0.15[out]",
        "-map",
        "[out]",
        "-ar",
        "44100",
        "-ac",
        "2",
        str(output),
    ]
    return run(cmd)


def generate_theme_ambient(output: Path, theme_type: str = "chiba") -> bool:
    """Theme ambient sounds - longer atmospheric drones."""
    duration = 3.0
    configs = {
        "chiba": (80, 120, 0.3),
        "matrix_rain": (60, 90, 0.25),
        "finn_office": (100, 150, 0.25),
        "loa_drum": (80, 0.15),
        "industrial": (50, 80, 0.3),
        "broadcast": (1000, 1500, 0.15),
        "hammer_alert": (200, 300, 0.35),
        "neon_hum": (60, 0.2),
    }
    config = configs.get(theme_type, (100, 150, 0.3))
    if theme_type in ("loa_drum", "neon_hum"):
        freq1, vol = config
        freq2 = freq1 * 1.5
    else:
        freq1, freq2, vol = config

    if theme_type == "loa_drum":
        cmd = [
            FFMPEG,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={freq1}:duration={duration}",
            "-af",
            f"tremolo=f=2:d=0.8,volume={vol},afade=t=in:st=0:d=0.2,afade=t=out:st={duration - 0.5}:d=0.5",
            "-ar",
            "44100",
            "-ac",
            "2",
            str(output),
        ]
    elif theme_type == "neon_hum":
        cmd = [
            FFMPEG,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={freq1}:duration={duration}",
            "-af",
            f"tremolo=f=0.5:d=1,volume={vol},afade=t=in:st=0:d=0.3,afade=t=out:st={duration - 0.5}:d=0.5",
            "-ar",
            "44100",
            "-ac",
            "2",
            str(output),
        ]
    else:
        cmd = [
            FFMPEG,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={freq1}:duration={duration}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={freq2}:duration={duration}",
            "-filter_complex",
            f"[0:a][1:a]amix=weights=0.5 0.5,volume={vol},tremolo=f=0.3:d=0.5,afade=t=in:st=0:d=0.3,afade=t=out:st={duration - 0.5}:d=0.5[out]",
            "-map",
            "[out]",
            "-ar",
            "44100",
            "-ac",
            "2",
            str(output),
        ]
    return run(cmd)


def generate_story_sound(output: Path, story_type: str = "typing") -> bool:
    """Story-related sounds - subtle and non-intrusive."""
    if story_type == "typing":
        duration = 0.04
        cmd = [
            FFMPEG,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anoisesrc=d={duration}:a=0.08",
            "-af",
            "highpass=f=1000,lowpass=f=3000,volume=0.4",
            "-ar",
            "44100",
            "-ac",
            "2",
            str(output),
        ]
    elif story_type == "dialogue_advance":
        duration = 0.1
        cmd = [
            FFMPEG,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=660:duration={duration}",
            "-af",
            f"afade=t=in:st=0:d=0.01,afade=t=out:st={duration - 0.02}:d=0.02,volume=0.2",
            "-ar",
            "44100",
            "-ac",
            "2",
            str(output),
        ]
    else:  # event_trigger
        duration = 0.25
        cmd = [
            FFMPEG,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=880:duration={duration}",
            "-f",
            "lavfi",
            "-i",
            f"anoisesrc=d={duration}:a=0.05",
            "-filter_complex",
            f"[0:a][1:a]amix=weights=0.7 0.3,tremolo=f=10:d=0.2,volume=0.3,afade=t=in:st=0:d=0.03,afade=t=out:st={duration - 0.05}:d=0.05[out]",
            "-map",
            "[out]",
            "-ar",
            "44100",
            "-ac",
            "2",
            str(output),
        ]
    return run(cmd)


def generate_item_sound(output: Path, item_type: str = "pickup") -> bool:
    """Item sounds - satisfying digital feedback."""
    configs = {
        "pickup": (0.1, 1200, 0.35),
        "equip": (0.12, 800, 0.3),
        "cant": (0.2, 200, 0.4),
    }
    duration, freq, vol = configs.get(item_type, (0.1, 800, 0.3))

    cmd = [
        FFMPEG,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency={freq}:duration={duration}",
        "-af",
        f"afade=t=in:st=0:d=0.01,afade=t=out:st={duration - 0.02}:d=0.02,volume={vol}",
        "-ar",
        "44100",
        "-ac",
        "2",
        str(output),
    ]
    return run(cmd)


def main():
    """Generate all improved sound files."""
    sounds_dir = Path(__file__).parent.parent / "data" / "sounds_test"
    sounds_dir.mkdir(exist_ok=True)

    print("Generating improved cyberpunk sounds using ffmpeg...")

    # Combat sounds
    print("  Combat sounds...")
    generate_combat_hit(sounds_dir / "combat_hit_normal.wav")
    generate_combat_hit(sounds_dir / "combat_hit_crit.wav", crit=True)
    generate_sine(sounds_dir / "combat_hit_miss.wav", 150, 0.08, 0.3)
    generate_combat_block(sounds_dir / "combat_block.wav")
    generate_combat_victory(sounds_dir / "combat_victory.wav")
    generate_combat_defeat(sounds_dir / "combat_defeat.wav")
    generate_skill_sound(sounds_dir / "combat_skill_physical.wav", "physical")
    generate_skill_sound(sounds_dir / "combat_skill_magic.wav", "magic")
    generate_skill_sound(sounds_dir / "combat_skill_heal.wav", "heal")
    generate_skill_sound(sounds_dir / "combat_skill_buff.wav", "buff")
    generate_skill_sound(sounds_dir / "combat_skill_debuff.wav", "debuff")
    generate_stun(sounds_dir / "combat_stun.wav")

    # UI sounds
    print("  UI sounds...")
    generate_ui_beep(sounds_dir / "ui_menu_select.wav", "select")
    generate_ui_beep(sounds_dir / "ui_menu_confirm.wav", "confirm")
    generate_ui_beep(sounds_dir / "ui_menu_cancel.wav", "cancel")
    generate_ui_beep(sounds_dir / "ui_error.wav", "error")
    generate_ui_beep(sounds_dir / "ui_notification.wav", "notification")

    # Movement sounds
    print("  Movement sounds...")
    generate_movement_step(sounds_dir / "movement_nav_step.wav")
    generate_movement_step(sounds_dir / "movement_nav_block.wav")
    generate_jack_in(sounds_dir / "movement_jack_in.wav")
    generate_jack_in(sounds_dir / "movement_jack_in_zap.wav")
    generate_jack_out(sounds_dir / "movement_jack_out.wav")
    generate_jack_out(sounds_dir / "movement_jack_out_buzz.wav")
    generate_data_extract(sounds_dir / "movement_data_extract.wav")
    generate_static(sounds_dir / "movement_broadcast_static.wav", 0.5)
    generate_static(sounds_dir / "movement_broadcast_out.wav", 0.8)
    generate_black_ice_roar(sounds_dir / "movement_black_ice_roar.wav")

    # Story sounds
    print("  Story sounds...")
    generate_story_sound(sounds_dir / "story_text_typing.wav", "typing")
    generate_story_sound(sounds_dir / "story_dialogue_advance.wav", "dialogue_advance")
    generate_story_sound(sounds_dir / "story_event_trigger.wav", "event_trigger")

    # Item sounds
    print("  Item sounds...")
    generate_item_sound(sounds_dir / "items_pickup.wav", "pickup")
    generate_item_sound(sounds_dir / "items_equip.wav", "equip")
    generate_item_sound(sounds_dir / "items_cant.wav", "cant")

    # Theme ambients
    print("  Theme ambients...")
    generate_theme_ambient(sounds_dir / "theme_chiba.wav", "chiba")
    generate_theme_ambient(sounds_dir / "theme_matrix_rain.wav", "matrix_rain")
    generate_theme_ambient(sounds_dir / "theme_finn_office.wav", "finn_office")
    generate_theme_ambient(sounds_dir / "theme_loa_drum.wav", "loa_drum")
    generate_theme_ambient(sounds_dir / "theme_loa_drum_fade.wav", "loa_drum")
    generate_theme_ambient(sounds_dir / "theme_loa_channel.wav", "loa_drum")
    generate_theme_ambient(sounds_dir / "theme_industrial.wav", "industrial")
    generate_theme_ambient(sounds_dir / "theme_broadcast.wav", "broadcast")
    generate_theme_ambient(sounds_dir / "theme_hammer_alert.wav", "hammer_alert")
    generate_theme_ambient(sounds_dir / "theme_sense_net.wav", "chiba")
    generate_theme_ambient(sounds_dir / "theme_cyberspace.wav", "matrix_rain")
    generate_theme_ambient(sounds_dir / "theme_manarase_drone.wav", "loa_drum")

    print("Done! All sounds generated.")


if __name__ == "__main__":
    main()
