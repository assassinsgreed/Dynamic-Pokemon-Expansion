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


def load_with_palette(path: Path, palette: Path) -> Image.Image:
    """A sprite drawn with another PNG's palette (same pixel indices, other colours): front sprites with their shiny
    palette, back sprites (stored in shiny colours) with the normal one."""
    img = Image.open(path).copy()
    img.putpalette(Image.open(palette).getpalette())
    img.info["transparency"] = 0
    return img.crop((0, 0, CELL, CELL)).convert("RGBA")


def recolor_map(src: Image.Image, dst: Image.Image) -> str | None:
    """The colour swaps that turn src into dst, as "RRGGBBrrggbb" pairs for the colours that change ("" when none do),
    or None when no swap can: a colour that must become two colours, or transparency that differs."""
    a, b = src.convert("RGBA").tobytes(), dst.convert("RGBA").tobytes()
    swap: dict[bytes, bytes] = {}
    for i in range(0, len(a), 4):
        if a[i + 3] != b[i + 3] or a[i + 3] not in (0, 255):
            return None
        if a[i + 3] and swap.setdefault(a[i:i + 3], b[i:i + 3]) != b[i:i + 3]:
            return None
    return "".join(p.hex() + q.hex() for p, q in sorted(swap.items()) if p != q)


def apply_recolor(img: Image.Image, swaps: str) -> Image.Image:
    """img with recolor_map's swaps applied, as app.js does it on a canvas (opaque pixels only)."""
    swap = {bytes.fromhex(swaps[k:k + 6]): bytes.fromhex(swaps[k + 6:k + 12]) for k in range(0, len(swaps), 12)}
    px = bytearray(img.convert("RGBA").tobytes())
    for i in range(0, len(px), 4):
        if px[i + 3] and (to := swap.get(bytes(px[i:i + 3]))):
            px[i:i + 3] = to
    return Image.frombytes("RGBA", img.size, bytes(px))


def _seen(img: Image.Image) -> bytes:
    """RGBA bytes with every transparent pixel zeroed: its colour can't be seen."""
    px = bytearray(img.convert("RGBA").tobytes())
    for i in range(0, len(px), 4):
        if not px[i + 3]:
            px[i:i + 3] = b"\0\0\0"
    return bytes(px)


def same_pixels(a: Image.Image, b: Image.Image) -> bool:
    """Equal as seen: the colour of a transparent pixel doesn't count."""
    return a.size == b.size and _seen(a) == _seen(b)


def build_sheet(pngs: dict[str, Path], shiny: dict[str, tuple[Path, Path]] = {},
                backs: dict[str, tuple[Path, Path]] = {}) -> tuple[bytes, dict[str, tuple], list[str]]:
    """Front sprites keyed as given, each shiny one keyed "shiny:<key>" (front, shiny palette PNG), and each back
    (back PNG, front PNG) as "back:<key>" in the front's normal palette and "shinyback:<key>" as the PNG is.

    Only fronts and shiny backs get cells of their own: a shiny front is its front's cell recoloured, and a regular
    back its shiny back's, so the offset of a "shiny:" or "back:" key is (x, y, n): the cell at x, y with swap list n
    of the returned recolors (or just (x, y) when nothing changes). Every swap is checked to give exactly the sprite's
    pixels; one no swap can give (a colour that would have to become two) keeps a cell of its own."""
    images = {key: load_sprite(path) for key, path in pngs.items()}
    derived: dict[str, tuple[str, str]] = {}  # key → (key of the cell it's drawn from, swaps)

    def add(key: str, img: Image.Image, source: str | None) -> None:
        swaps = recolor_map(images[source], img) if source in images else None
        if swaps is not None and same_pixels(apply_recolor(images[source], swaps), img):
            derived[key] = (source, swaps)
        else:
            images[key] = img

    for key, (path, palette) in shiny.items():
        add(f"shiny:{key}", load_with_palette(path, palette), key)
    for key, (back, front) in backs.items():
        images[f"shinyback:{key}"] = load_sprite(back)
        add(f"back:{key}", load_with_palette(back, front), f"shinyback:{key}")
    sheet, offsets = pack(images, CELL)
    recolors = list(dict.fromkeys(swaps for _, swaps in derived.values() if swaps))
    number = {swaps: n for n, swaps in enumerate(recolors)}
    for key, (source, swaps) in derived.items():
        offsets[key] = (*offsets[source], number[swaps]) if swaps else offsets[source]
    return sheet, offsets, recolors


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
