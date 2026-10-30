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
from .locations import FACTORY_OVERWORLD
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


# Where the game's grid says more than the place really covers, by grid square (column, row) (Collin, 2026-10-30)
NOT_PART_OF = {
    "Route 13": {(18, 6)},           # the upper square is only Carnelidge Volcano
    "Route 9": {(14, 3)},            # just the vertical bar; the square east of it is Daimyn Factory's overworld
    "Route 24": {(17, 4), (18, 4)},  # only the stretch north of Uteya Village
}
PLACED_AT = {
    "Hesson Pass": [(17, 4)],        # one square right of where the grid puts it
    "Heleo Ranch": [(14, 5)],        # one square up
    FACTORY_OVERWORLD: [(14, 3)],    # Route 9 to the game; the factory's square, east of Route 9's bar
}


REGION_LAYOUT = DPE_ROOT.parent / "PokemonShootingStars" / "designdocs" / "region" / "region-layout.md"
DOC_NAMES = {"Daimyn City Factory": "Daimyn Factory"}  # the design doc's name → the game's


def place_descriptions() -> dict[str, str]:
    """Place name → its one-paragraph description from the PSS design doc's Towns / Dungeons / Key Locations tables
    (| # | Name | Details |) and Routes table (| # | Details |, the number being the route's)."""
    about = {}
    for line in REGION_LAYOUT.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.startswith("|") else []
        if len(cells) >= 2 and cells[0].isdigit():
            name = cells[1] if len(cells) == 3 else f"Route {cells[0]}"
            about[DOC_NAMES.get(name, name)] = cells[-1]
    about[FACTORY_OVERWORLD] = about["Daimyn Factory"]
    return about


def town_map_png() -> bytes:
    out = io.BytesIO()
    Image.open(TOWN_MAP).crop(CROP).save(out, "PNG", optimize=True)
    return out.getvalue()


def town_map_squares(p: Paths) -> dict[str, list[list[int]]]:
    """In-game place name → top-left corners of its 8×8 squares, in pixels of the cropped Town Map."""
    rom, names = _rom_bytes(p.rom), map_section_names(p)
    cells: dict[str, list[tuple[int, int]]] = {}
    for layer in range(LAYERS):
        for row in range(ROWS):
            for col in range(COLS):
                section = rom[SECTIONS + (layer * ROWS + row) * COLS + col]
                name = names.get(section)
                if section != EMPTY and (col, row) not in NOT_PART_OF.get(name, ()) and (col, row) not in cells.setdefault(name, []):
                    cells[name].append((col, row))
    cells.update(PLACED_AT)
    squares = {name: [[ORIGIN + col * CELL - CROP[0], ORIGIN + row * CELL - CROP[1]] for col, row in c]
               for name, c in cells.items()}
    for name, (x, y) in SPOTS.items():
        squares[name] = [[x - CELL // 2 - CROP[0], y - CELL // 2 - CROP[1]]]
    return squares


def norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())
