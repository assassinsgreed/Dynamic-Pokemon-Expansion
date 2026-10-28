import re

import pytest

from tools.dexpage.build import page_data, render, search_keys
from tools.dexpage.roster import evolution_links
from tools.dexpage.sprites import build_sheet


@pytest.fixture(scope="module")
def data(source_data, roster, evo_links):
    return page_data(source_data, roster, evo_links)


@pytest.fixture(scope="module")
def html(data, source_data, roster):
    sheet, offsets = build_sheet({e.key: source_data.sprites[e.key] for e in roster})
    return render(data, sheet, offsets)


def test_search_keys():
    assert "ceaselessedge" in search_keys("Endless Edge", "Ceaseless Edge")
    assert "endlessedge" in search_keys("Endless Edge", "Ceaseless Edge")
    assert search_keys("Farfetch'd", None) == ["farfetchd"]


def test_level_zero_is_evo(data):
    learners = data["moves"]["MOVE_CEASELESSEDGE"]["learners"]
    samurott_h = next(i for i, m in enumerate(data["mons"]) if m["key"] == "SPECIES_SAMUROTT_H")
    assert [samurott_h, "Evo"] in learners


def test_move_with_no_learners_is_listed(data):
    unlearned = [k for k, m in data["moves"].items() if m["learners"] == []]
    assert unlearned                    # such moves are kept in the data, not dropped


def test_learner_labels(data):
    mons = {m["key"]: i for i, m in enumerate(data["mons"])}
    cut = data["moves"]["MOVE_CUT"]["learners"]
    assert [mons["SPECIES_BULBASAUR"], "HM01"] in cut
    flame = data["moves"]["MOVE_FLAMEBURST"]["learners"]
    assert [mons["SPECIES_CHARMANDER"], "Special: Fire types"] in flame


def test_evolution_links_use_indices(data):
    mons = {m["key"]: i for i, m in enumerate(data["mons"])}
    kadabra = data["mons"][mons["SPECIES_KADABRA"]]
    assert [mons["SPECIES_ALAKAZAM"], "Use Linking Cord"] in kadabra["evo"]


def test_page_is_self_contained(html):
    assert not re.search(r'(src|href)=["\']https?://', html)
    assert "@import" not in html and "fonts.googleapis" not in html


def test_page_size(html):
    assert len(html.encode()) < 8_000_000


def test_battle_forms_point_to_base_moves(data):
    mons = {m["key"]: i for i, m in enumerate(data["mons"])}
    mega = data["mons"][mons["SPECIES_VENUSAUR_MEGA"]]
    assert mega["movesOf"] == mons["SPECIES_VENUSAUR"]
    learner_ids = {i for i, _ in data["moves"]["MOVE_VINEWHIP"]["learners"]}
    assert mons["SPECIES_VENUSAUR"] in learner_ids and mons["SPECIES_VENUSAUR_MEGA"] not in learner_ids


@pytest.fixture(scope="module")
def site(tmp_path_factory, paths):
    from tools.dexpage.build import build
    out = tmp_path_factory.mktemp("site")
    build(paths, out)
    return out


def test_sw_cache_name_tracks_content(site):
    import hashlib
    sw = (site / "sw.js").read_text()
    h = hashlib.sha256((site / "index.html").read_bytes()).hexdigest()[:12]
    assert f"dex-{h}" in sw


def test_site_files(site):
    for f in ["index.html", "dex.html", "manifest.webmanifest", "sw.js", "icon-192.png", "icon-512.png"]:
        assert (site / f).exists()
    assert (site / "dex.html").read_bytes() == (site / "index.html").read_bytes()
    import json
    manifest = json.loads((site / "manifest.webmanifest").read_text())
    assert manifest["display"] == "standalone" and manifest["start_url"] == "./"
