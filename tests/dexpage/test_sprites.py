import functools
import io

import pytest
from PIL import Image

from tools.dexpage.sprites import CELL, apply_recolor, build_sheet, load_sprite, load_with_palette, same_pixels


@pytest.fixture(scope="module")
def full_sheet(roster, source_data):
    """The whole roster's sheet, built once for the tests that need it (encoding it takes a while)."""
    return build_sheet(
        {e.key: source_data.sprites[e.key] for e in roster},
        {e.key: (source_data.sprites[e.key], source_data.shiny[e.key]) for e in roster if e.key in source_data.shiny},
        {e.key: (source_data.backs[e.key], source_data.sprites[e.key]) for e in roster if e.key in source_data.backs})


@functools.lru_cache(maxsize=4)
def _decoded(sheet: bytes) -> Image.Image:
    return Image.open(io.BytesIO(sheet)).convert("RGBA")


def _cell(sheet: bytes, offsets: dict, recolors: list[str], key: str) -> Image.Image:
    """A sprite as the page shows it: its cell, recoloured when its offset names a swap list (as app.js does)."""
    img = _decoded(sheet)
    x, y, *n = offsets[key]
    cell = img.crop((x, y, x + CELL, y + CELL))
    return apply_recolor(cell, recolors[n[0]]) if n else cell


def test_every_row_has_a_cell(roster, full_sheet):
    sheet, offsets, _ = full_sheet
    assert {e.key for e in roster} <= set(offsets)
    assert "back:SPECIES_CASTFORM" in offsets and "shinyback:SPECIES_CASTFORM" in offsets
    assert len(sheet) < 1_500_000  # shiny fronts and regular backs are recoloured cells, not cells of their own


def test_recoloured_sprites_are_exact(roster, source_data, full_sheet):
    """Every shiny front and regular back, decoded from the real sheet and recoloured, is pixel for pixel the image
    it stands for (the front in its shiny palette; the back PNG in the front's normal palette)."""
    sheet, offsets, recolors = full_sheet
    for e in roster:
        if e.key in source_data.shiny:
            want = load_with_palette(source_data.sprites[e.key], source_data.shiny[e.key])
            assert same_pixels(_cell(sheet, offsets, recolors, f"shiny:{e.key}"), want), e.key
        if e.key in source_data.backs:
            want = load_with_palette(source_data.backs[e.key], source_data.sprites[e.key])
            assert same_pixels(_cell(sheet, offsets, recolors, f"back:{e.key}"), want), e.key
            assert same_pixels(_cell(sheet, offsets, recolors, f"shinyback:{e.key}"), load_sprite(source_data.backs[e.key])), e.key


def test_background_is_transparent(source_data):
    sheet, offsets, _ = build_sheet({"SPECIES_BULBASAUR": source_data.sprites["SPECIES_BULBASAUR"]})
    x, y = offsets["SPECIES_BULBASAUR"]
    assert Image.open(io.BytesIO(sheet)).convert("RGBA").getpixel((x, y))[3] == 0


def test_tall_source_is_cropped_to_first_frame(tmp_path):
    tall = Image.new("P", (64, 128))
    tall.putpalette([0, 0, 0, 255, 0, 0] + [0] * 762)
    tall.paste(1, (0, 64, 64, 128))  # second frame is red, first frame is all background
    path = tmp_path / "tall.png"
    tall.save(path)
    sheet, offsets, _ = build_sheet({"X": path})
    img = Image.open(io.BytesIO(sheet)).convert("RGBA")
    assert img.size[1] == CELL
    assert all(img.getpixel((i, j))[3] == 0 for i in range(CELL) for j in range(CELL))


def test_identical_sprites_share_a_cell(source_data):
    p = source_data.sprites["SPECIES_BULBASAUR"]
    _, offsets, _ = build_sheet({"A": p, "B": p})
    assert offsets["A"] == offsets["B"]


def test_back_sprites_regular_and_shiny(source_data):
    """Back regular is the back picture in the normal palette, back shiny is the PNG as is: they must differ."""
    key = "SPECIES_FARFETCHD_G"
    sheet, offsets, recolors = build_sheet({}, backs={key: (source_data.backs[key], source_data.sprites[key])})
    assert not same_pixels(_cell(sheet, offsets, recolors, f"back:{key}"), _cell(sheet, offsets, recolors, f"shinyback:{key}"))


def test_a_colour_that_must_split_keeps_its_own_cell(tmp_path):
    """Two pixels of one colour that become two colours can't be a swap: that sprite is stored as it is."""
    def png(name, colors):
        img = Image.new("P", (64, 64))
        img.putpalette([0, 0, 0] + [c for rgb in colors for c in rgb] + [0] * (768 - 3 - 3 * len(colors)))
        img.paste(1, (0, 0, 8, 8))
        img.paste(2, (8, 0, 16, 8))
        img.save(tmp_path / name)
        return tmp_path / name
    front = png("front.png", [(10, 10, 10), (10, 10, 10)])  # indices 1 and 2 are the same colour...
    shiny = png("shiny.png", [(200, 0, 0), (0, 200, 0)])    # ...and different shiny colours
    sheet, offsets, recolors = build_sheet({"X": front}, {"X": (front, shiny)})
    assert len(offsets["shiny:X"]) == 2 and offsets["shiny:X"] != offsets["X"] and not recolors
    assert same_pixels(_cell(sheet, offsets, recolors, "shiny:X"), load_with_palette(front, shiny))
