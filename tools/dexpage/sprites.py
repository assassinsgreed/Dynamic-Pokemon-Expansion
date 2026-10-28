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
    return pack({key: load_sprite(path) for key, path in pngs.items()}, CELL)


def pack(images: dict[str, Image.Image], cell: int) -> tuple[bytes, dict[str, tuple[int, int]]]:
    """Lossless WebP sheet of cell×cell images, plus each key's cell origin; identical images share a cell."""
    cells: list[Image.Image] = []
    by_pixels: dict[bytes, int] = {}
    cell_of: dict[str, int] = {}
    for key, sprite in images.items():
        pixels = sprite.tobytes()
        if pixels not in by_pixels:
            by_pixels[pixels] = len(cells)
            cells.append(sprite)
        cell_of[key] = by_pixels[pixels]

    columns = min(COLUMNS, max(len(cells), 1))
    sheet = Image.new("RGBA", (columns * cell, max(1, math.ceil(len(cells) / columns)) * cell))
    for i, sprite in enumerate(cells):
        sheet.paste(sprite, ((i % columns) * cell, (i // columns) * cell))

    out = io.BytesIO()
    sheet.save(out, "WEBP", lossless=True, quality=100, method=6)
    offsets = {key: ((i % columns) * cell, (i // columns) * cell) for key, i in cell_of.items()}
    return out.getvalue(), offsets
