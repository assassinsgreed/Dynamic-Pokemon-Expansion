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
    assert [mons["SPECIES_ALAKAZAM"], "Use Linking Cord", next(i for i, it in enumerate(data["items"]) if it["name"] == "Linking Cord"), "Linking Cord"] in kadabra["evo"]


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
    assert "<title>Pokemon Amethyst Companion</title>" in html


def test_sw_only_caches_good_responses(site):
    assert "res.ok" in (site / "sw.js").read_text()


def test_wild_held_items_on_profile(data):
    by = {m["key"]: m for m in data["mons"]}
    assert "Oran Berry (50%)" in [h for h, _ in by["SPECIES_BIBAREL"]["held"]]
    assert all("item" not in l for m in data["mons"] for l in m["loc"])   # moved out of location rows


def test_header_icon_embedded(html):
    assert 'class="brand-icon"' in html and "data:image/png;base64," in html


def test_items_in_page(data):
    items = {i["name"]: i for i in data["items"]}
    stone = items["Fire Stone"]
    assert stone["icon"] is not None and any(w.startswith("Daimyn City Mall") for w in stone["where"])
    assert items["Venusaurite-G"]["icon"] is not None


def test_held_items_link_to_items(data):
    by = {m["key"]: m for m in data["mons"]}
    names = [data["items"][h[1]]["name"] for h in by["SPECIES_BIBAREL"]["held"] if h[1] is not None]
    assert "Oran Berry" in names


def test_tm_locations_on_moves(data):
    assert data["moves"]["MOVE_DRAGONCLAW"]["tm"] == {"label": "TM02", "where": ["Rubarr Desert B1F"], "requires": "Strength, Rock Smash"}


def test_ability_names_follow_cfru_overrides(data):
    by = {m["key"]: m for m in data["mons"]}
    names = lambda m: [a[0] for a in m["abilities"]] + ([m["hidden"][0]] if m["hidden"] else [])
    cinderace = by["SPECIES_CINDERACE"]
    assert "Libero" in names(cinderace) and "Protean" not in names(cinderace)
    assert "White Smoke" in names(by["SPECIES_TORKOAL"])


def test_ability_descriptions_from_the_game(data):
    by = {m["key"]: m for m in data["mons"]}
    cinderace = by["SPECIES_CINDERACE"]
    assert cinderace["hidden"] == ["Libero", "Changes type to match move.", 0]
    assert cinderace["abilities"][0][0] == "Blaze" and cinderace["abilities"][0][1]   # vanilla text read from the ROM


def test_evolution_items_link_to_item_cards(data):
    by = {m["key"]: (i, m) for i, m in enumerate(data["mons"])}
    arcanine = by["SPECIES_ARCANINE"][0]
    link = next(l for l in by["SPECIES_GROWLITHE"][1]["evo"] if l[0] == arcanine)
    assert data["items"][link[2]]["name"] == "Fire Stone"


def test_moves_searchable_by_tm_number(data):
    keys = data["moves"]["MOVE_DRAGONCLAW"]["s"]
    assert "tm02" in keys and "tm2" in keys


def test_item_name_fixes(data):
    items = {i["name"]: i for i in data["items"]}
    assert items["Banettite"]["icon"] is not None          # the doc spells it "Banetite"
    for colour in ("Red", "Yellow", "Pink", "Purple"):
        assert items[f"{colour} Nectar"]["icon"] is not None   # one doc row, four items


def test_shop_stock_merged_into_item_locations(data):
    items = {i["name"]: i for i in data["items"]}
    glasses = items["Black Glasses"]["where"]
    assert "Lake Laplaz" in glasses
    assert any(w.startswith("Daimyn City Mall · ") for w in glasses)
    assert any(w.startswith("Daimyn City Game Corner") for w in items["Life Orb"]["where"])


def test_item_list_is_only_items(data):
    names = {i["name"] for i in data["items"]}
    assert "Joltik" not in names and "Mudbray" not in names       # Game Corner Pokémon prizes
    assert "Poké Ball" in names and "Pok\e Ball" not in names
    assert "Blunder Policy" in names and "BlundrPolicy" not in names


def test_every_tm_and_hm_is_an_item(data):
    tms = {i["name"]: i for i in data["items"] if i["category"] in ("TMs", "HMs")}
    assert len([n for n in tms if n.startswith("TM")]) == 100 and len([n for n in tms if n.startswith("HM")]) == 6
    claw = tms["TM02 Dragon Claw"]
    assert claw["where"] == ["Rubarr Desert B1F"] and claw["move"] == "MOVE_DRAGONCLAW" and claw["icon"] is not None
    assert not any(i["name"] == "TM16" for i in data["items"])        # shop TMs merge into the full entry


def test_tutor_locations_on_moves(data):
    snore = data["moves"]["MOVE_SNORE"]["tutor"]
    assert {"where": "Ferrox Village", "note": "5 PokeChips", "kind": "Regular"} in snore
    burst = data["moves"]["MOVE_FLAMEBURST"]["tutor"]      # doc row "Fire Fang, or Flame Burst (v1.4+)"
    assert burst[0]["where"] == "Gym Trainee Ashley"
    assert "tutor" not in data["moves"]["MOVE_FIREFANG"] or all(t["where"] != "Gym Trainee Ashley" for t in data["moves"]["MOVE_FIREFANG"]["tutor"])


def test_tutors_assume_latest_version(data):
    by_move = {}
    for t in data["tutors"]:
        by_move.setdefault(t["move"], []).append(t["where"])
    assert "MOVE_VACUUMWAVE" in by_move and "MOVE_AURASPHERE" not in by_move or all(
        not w.startswith("Gym Trainee Gawain") for w in by_move.get("MOVE_AURASPHERE", []))
    assert "MOVE_PLUCK" in by_move                                  # "Dual Wingbeat, or Pluck (v1.4+)"
    assert not any("(v1." in t["where"] for t in data["tutors"])    # "Battle Frontier (v1.4)" → "Battle Frontier"


def test_gym_trainee_tutors_grouped(data):
    mason = [t for t in data["tutors"] if t["where"] == "Gym Trainee Mason"]
    assert {t["move"] for t in mason} == {"MOVE_AUTOTOMIZE", "MOVE_METALBURST", "MOVE_HEAVYSLAM"}
    assert len({t["note"] for t in mason}) == 1


def test_game_version_tag(html):
    assert re.search(r'class="version"[^>]*>v1.4.3<', html)


def test_docs_in_page(data):
    groups = {g["title"]: g for g in data["docs"]}
    mining = next(t for t in groups["Gameplay Features"]["topics"] if t["title"] == "Mining Minigame")
    assert "<table" in mining["html"] and "data:image/png;base64," in mining["html"]
    assert "hardstone" in mining["s"]


def test_abilities_list(data):
    abilities = {a["name"]: a for a in data["abilities"]}
    mons = {m["key"]: i for i, m in enumerate(data["mons"])}
    triage = abilities["Triage"]
    assert triage["desc"] and [mons["SPECIES_VENUSAUR_GIGA"], 0] in triage["mons"]
    assert [mons["SPECIES_CINDERACE"], 1] in abilities["Libero"]["mons"]                      # hidden, CFRU rename
    assert all(i != mons["SPECIES_CINDERACE"] for i, _ in abilities.get("Protean", {"mons": []})["mons"])


def test_ability_official_names(data, paths):
    abilities = {a["name"]: a for a in data["abilities"]}
    assert abilities["Odd Medicine"]["official"] == "Curious Medicine"
    assert abilities["Alchemic Power"]["official"] == "Power of Alchemy"                        # CFRU rename label
    assert abilities["Neutralize Gas"]["official"] == "Neutralizing Gas"
    assert abilities["Overgrow"]["official"] is None
    from tools.dexpage.load_cfru import ability_officials
    assert "As One" not in ability_officials(paths)                                 # Grim/Chilling variants


def test_docs_link_ability_cells(data):
    mega = next(t for g in data["docs"] for t in g["topics"] if t["title"] == "Mega Pokemon")
    assert 'data-ability="Triage"' in mega["html"]


def test_ability_chance_in_page(data):
    abilities = {a["name"]: a for a in data["abilities"]}
    assert abilities["Poison Touch"]["chance"] == 30


def test_swarm_entries(data):
    mons = {m["key"]: m for m in data["mons"]}
    assert mons["SPECIES_FARFETCHD"]["swarm"] == ["Standard"]     # Galarian Farfetch'd holds Standard #063
    assert mons["SPECIES_ZIGZAGOON"]["swarm"] == ["Divergent"]
    assert mons["SPECIES_FARFETCHD_G"]["swarm"] == []            # numbered
    assert "swarm" in mons["SPECIES_FARFETCHD"]["s"]
