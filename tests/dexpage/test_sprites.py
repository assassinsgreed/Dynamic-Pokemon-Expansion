import io

from PIL import Image

from tools.dexpage.sprites import CELL, build_sheet


def test_every_row_has_a_cell(roster, source_data):
    sheet, offsets = build_sheet({e.key: source_data.sprites[e.key] for e in roster})
    assert {e.key for e in roster} <= set(offsets)
    assert len(sheet) < 3_000_000


def test_background_is_transparent(source_data):
    sheet, offsets = build_sheet({"SPECIES_BULBASAUR": source_data.sprites["SPECIES_BULBASAUR"]})
    x, y = offsets["SPECIES_BULBASAUR"]
    assert Image.open(io.BytesIO(sheet)).convert("RGBA").getpixel((x, y))[3] == 0


def test_tall_source_is_cropped_to_first_frame(tmp_path):
    tall = Image.new("P", (64, 128))
    tall.putpalette([0, 0, 0, 255, 0, 0] + [0] * 762)
    tall.paste(1, (0, 64, 64, 128))  # second frame is red, first frame is all background
    path = tmp_path / "tall.png"
    tall.save(path)
    sheet, offsets = build_sheet({"X": path})
    img = Image.open(io.BytesIO(sheet)).convert("RGBA")
    assert img.size[1] == CELL
    assert all(img.getpixel((i, j))[3] == 0 for i in range(CELL) for j in range(CELL))


def test_identical_sprites_share_a_cell(source_data):
    p = source_data.sprites["SPECIES_BULBASAUR"]
    _, offsets = build_sheet({"A": p, "B": p})
    assert offsets["A"] == offsets["B"]
