"""Where each place sits on the game's Town Map, for the Locations tab's place cards.

FireRed keeps the Town Map as a grid of region map sections, [layer][15 rows][22 columns] at sRegionMapSections:
layer 0 holds towns and routes, layer 1 the single squares of dungeons drawn over them. Each square is 8×8 px on
the 240×160 map art (graphics/Maps/TownMap.png in the PokemonShootingStars repo), the grid's top-left square at
(32, 32): the eleven town squares land on the eleven town markers there. The page shows the art without the GBA
screen's black border, so squares are given in that cropped image's pixels."""

import io
import re

from PIL import Image

from .field_items import map_section_names
from .paths import DPE_ROOT, Paths
from .rom import _rom_bytes

TOWN_MAP = DPE_ROOT.parent / "PokemonShootingStars" / "graphics" / "Maps" / "TownMap.png"
SECTIONS = 0x3F2490          # sRegionMapSections_Kanto (vanilla FireRed address; Amethyst redrew the grid in place)
LAYERS, ROWS, COLS = 2, 15, 22
EMPTY = 0xC5                 # MAPSEC_NONE
CELL, ORIGIN = 8, 32
CROP = (16, 16, 224, 160)    # the map inside the black border
# Places inside another place's square, by the centre of their spot on the map art (Collin, 2026-10-30)
SPOTS = {
    "Pluto HQ": (136, 72),       # the southwest part of Daimyn City
    "Scalding Spa": (120, 44),   # on Route 12, where its West and East halves meet
}


def town_map_png() -> bytes:
    out = io.BytesIO()
    Image.open(TOWN_MAP).crop(CROP).save(out, "PNG", optimize=True)
    return out.getvalue()


def town_map_squares(p: Paths) -> dict[str, list[list[int]]]:
    """In-game place name → top-left corners of its 8×8 squares, in pixels of the cropped Town Map."""
    rom, names = _rom_bytes(p.rom), map_section_names(p)
    squares: dict[str, list[list[int]]] = {}
    for layer in range(LAYERS):
        for row in range(ROWS):
            for col in range(COLS):
                section = rom[SECTIONS + (layer * ROWS + row) * COLS + col]
                if section == EMPTY:
                    continue
                square = [ORIGIN + col * CELL - CROP[0], ORIGIN + row * CELL - CROP[1]]
                if square not in squares.setdefault(names[section], []):
                    squares[names[section]].append(square)
    for name, (x, y) in SPOTS.items():
        squares[name] = [[x - CELL // 2 - CROP[0], y - CELL // 2 - CROP[1]]]
    return squares


def norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())
