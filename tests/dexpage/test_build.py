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


def test_moves_searchable_by_full_name(data):
    # The name-table label is itself truncated for these, so the constant supplies the full name
    assert "poweruppunch" in data["moves"]["MOVE_POWERUPPUNCH"]["s"]
    assert "dazzlinggleam" in data["moves"]["MOVE_DAZZLINGGLEAM"]["s"]


def test_z_and_max_moves_left_out(data):
    assert "MOVE_BREAKNECK_BLITZ_P" not in data["moves"]


def test_form_names_are_searchable(data):
    meowth_g = next(m for m in data["mons"] if m["key"] == "SPECIES_MEOWTH_G")
    assert any("galarian" in s for s in meowth_g["s"])


def test_locations_attached(data):
    by = {m["key"]: m for m in data["mons"]}
    bidoof = by["SPECIES_BIDOOF"]["loc"]
    assert any(l["location"] == "Route 1" and l["levels"] == "2-4" and "Grass" in l["method"] for l in bidoof)
    assert any(l["location"] == "Route 10" for l in by["SPECIES_LYCANROC_N"]["loc"])
    assert data["unmatchedEncounters"] == []


def test_title(html):
    assert "<title>Pokemon Amethyst Pokedex</title>" in html


def test_sw_only_caches_good_responses(site):
    assert "res.ok" in (site / "sw.js").read_text()


def test_wild_held_items_on_profile(data):
    by = {m["key"]: m for m in data["mons"]}
    assert "Oran Berry (50%)" in by["SPECIES_BIBAREL"]["held"]
    assert all("item" not in l for m in data["mons"] for l in m["loc"])   # moved out of location rows


def test_header_icon_embedded(html):
    assert 'class="brand-icon"' in html and "data:image/png;base64," in html
