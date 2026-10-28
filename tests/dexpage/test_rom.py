import pytest

from tools.dexpage.load_cfru import item_ids as load_item_ids
from tools.dexpage.rom import RomError, item_names


@pytest.fixture(scope="module")
def item_ids(paths):
    return load_item_ids(paths)


@pytest.fixture(scope="module")
def names(paths, item_ids):
    if not paths.rom.exists():
        pytest.skip(f"built ROM not found at {paths.rom}")
    return item_names(paths.rom, item_ids)


def test_link_stone_is_linking_cord(names):
    assert names["ITEM_LINK_STONE"] == "Linking Cord"
    assert names["ITEM_FIRE_STONE"] == "Fire Stone"


def test_mega_stone_names(names):
    assert names["ITEM_VENUSAURITE_G"] == "VenusauriteG"  # exact in-game spelling


def test_missing_rom_raises(tmp_path, item_ids):
    with pytest.raises(RomError):
        item_names(tmp_path / "nope.gba", item_ids)
