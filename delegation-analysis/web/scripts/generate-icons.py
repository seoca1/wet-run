#!/usr/bin/env python3
"""Generate placeholder PWA icons for wet_run."""

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

def create_icon(size: int, output_path: Path) -> None:
    """Create a placeholder icon with the game title."""
    img = Image.new("RGB", (size, size), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    border_width = max(2, size // 50)
    draw.rectangle(
        [border_width, border_width, size - border_width - 1, size - border_width - 1],
        outline=(0, 255, 65),
        width=border_width
    )
    
    try:
        font_size = size // 8
        font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", font_size)
    except OSError:
        font = ImageFont.load_default()
    
    text = "WR"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    draw.text((x, y), text, fill=(0, 255, 65), font=font)
    
    img.save(output_path, "PNG")
    print(f"Created: {output_path} ({size}x{size})")

if __name__ == "__main__":
    script_dir = Path(__file__).parent
    icons_dir = script_dir.parent / "public" / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)
    
    create_icon(192, icons_dir / "icon-192.png")
    create_icon(512, icons_dir / "icon-512.png")
    
    print("Icons generated!")
