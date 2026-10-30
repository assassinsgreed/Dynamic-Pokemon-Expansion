import io

import pytest
from PIL import Image

from tools.dexpage.town_map import place_descriptions, town_map_png, town_map_squares

TOWNS = ["Anthra Town", "Olenic Town", "Rhodanzi City", "Ferrox Village", "Heleo City", "Daimyn City", "Laplaz Town",
         "Bruccie Village", "Emraldin Quay", "Tsarvosa City", "Uteya Village"]


@pytest.fixture(scope="module")
def squares(paths):
    return town_map_squares(paths)


def test_town_squares_sit_on_town_markers(squares):
    art = Image.open(io.BytesIO(town_map_png())).convert("RGB")
    assert art.size == (208, 144)
    for town in TOWNS:
        [(x, y)] = squares[town]
        pixels = [art.getpixel((x + i, y + j)) for i in range(8) for j in range(8)]
        assert any(r > 200 and g < 90 and b < 90 for r, g, b in pixels), town   # the red town marker


def test_routes_cover_several_squares(squares):
    assert len(squares["Route 14"]) >= 5
    assert len(squares["Route 12 West"]) == 2 and len(squares["Route 12 East"]) >= 2


def test_collins_corrections(squares):
    assert squares["Route 13"] == [[152, 80], [160, 80]]                 # not the volcano's square
    assert [160, 64] in squares["Carnelidge Volcano"]
    assert squares["Route 9"] == [[120, 32], [120, 40]]                  # the 2×1 bar only
    assert [128, 40] in squares["Daimyn Factory"]
    assert squares["Route 24"] == [[168, 32], [168, 40]]                 # north of Uteya Village
    assert squares["Hesson Pass"] == [[152, 48]]


def test_place_descriptions():
    about = place_descriptions()
    assert about["Hesson Pass"].startswith("The player can enter this cave")         # Dungeons table
    assert about["Route 12"].endswith("Separated by Scalding Spa.")                  # Routes table: number → route
    assert "Meltan" in about["Daimyn Factory"]                                       # doc says Daimyn City Factory


def test_hand_placed_spots(squares):
    [(x, y)] = squares["Scalding Spa"]                      # where Route 12 West meets Route 12 East
    assert [x - 4, y] in squares["Route 12 West"] and [x + 4, y] in squares["Route 12 East"]
    [(x, y)] = squares["Pluto HQ"]                          # southwest corner of Daimyn City
    [(dx, dy)] = squares["Daimyn City"]
    assert (x, y) == (dx - 4, dy + 4)
