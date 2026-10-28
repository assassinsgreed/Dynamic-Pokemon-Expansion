"""Packs front sprites into one sheet so the page can embed them as a single image."""

import io
import math
from pathlib import Path

from PIL import Image

CELL = 64
COLUMNS = 16


def load_sprite(path: Path) -> Image.Image:
    """First 64×64 frame, with palette index 0 (the GBA background colour) made transparent."""
    img = Image.open(path)
    if img.mode == "P":
        img.info["transparency"] = 0
    return img.crop((0, 0, CELL, CELL)).convert("RGBA")


def build_sheet(pngs: dict[str, Path]) -> tuple[bytes, dict[str, tuple[int, int]]]:
    cells: list[Image.Image] = []
    by_pixels: dict[bytes, int] = {}
    cell_of: dict[str, int] = {}
    for key, path in pngs.items():
        sprite = load_sprite(path)
        pixels = sprite.tobytes()
        if pixels not in by_pixels:
            by_pixels[pixels] = len(cells)
            cells.append(sprite)
        cell_of[key] = by_pixels[pixels]

    columns = min(COLUMNS, max(len(cells), 1))
    sheet = Image.new("RGBA", (columns * CELL, math.ceil(len(cells) / columns) * CELL))
    for i, sprite in enumerate(cells):
        sheet.paste(sprite, ((i % columns) * CELL, (i // columns) * CELL))

    out = io.BytesIO()
    sheet.save(out, "WEBP", lossless=True, quality=100, method=6)
    offsets = {key: ((i % columns) * CELL, (i // columns) * CELL) for key, i in cell_of.items()}
    return out.getvalue(), offsets
