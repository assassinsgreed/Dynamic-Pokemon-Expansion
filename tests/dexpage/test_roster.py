from tools.dexpage.load_dpe import dex_lists, egg_moves, levelup
from tools.dexpage.roster import all_moves, special_tutor_moves


def test_modes(roster, paths):
    by = {e.key: e for e in roster}
    assert by["SPECIES_BIDOOF"].modes == ["Standard"]
    assert by["SPECIES_ZIGZAGOON_G"].modes == ["Divergent"]
    std, div = dex_lists(paths)
    both = next(s for s in std if s in div)
    assert by[both].modes == ["Standard", "Divergent"]
    assert by["SPECIES_VENUSAUR_MEGA"].modes == by["SPECIES_VENUSAUR"].modes
    assert "SPECIES_LYCANROC_DUSK" in by and "SPECIES_ROTOM_HEAT" not in by


def test_form_labels(roster):
    by = {e.key: e for e in roster}
    assert by["SPECIES_RAICHU_A"].form == "Alolan"
    assert by["SPECIES_LYCANROC_N"].form == "Midnight"
    assert by["SPECIES_VENUSAUR_MEGA"].form == "Mega"
    assert by["SPECIES_VENUSAUR_GIGA"].form == "Mega G"
    assert by["SPECIES_BIDOOF"].form is None


def test_no_trade_or_gigantamax(evo_links):
    texts = [l["text"] for ls in evo_links.values() for l in ls]
    assert not any("trade" in t.lower() or "gigantamax" in t.lower() for t in texts)


def test_evolution_text(evo_links):
    assert {"to": "SPECIES_ALAKAZAM", "text": "Use Linking Cord"} in evo_links["SPECIES_KADABRA"]
    assert {"to": "SPECIES_VENUSAUR_GIGA", "text": "Mega Evolve holding VenusauriteG"} in evo_links["SPECIES_VENUSAUR"]
    dusk = [l["text"] for l in evo_links["SPECIES_ROCKRUFF"] if l["to"] == "SPECIES_LYCANROC_DUSK"]
    assert dusk == ["Lv. 25, 5 PM–7:59 PM"]
    # reversion rows (Mega → base with ITEM_NONE) are not evolutions
    assert "SPECIES_VENUSAUR_MEGA" not in evo_links or not evo_links["SPECIES_VENUSAUR_MEGA"]


def test_special_tutor_blocklist():
    assert special_tutor_moves("SPECIES_ROTOM", ["ELECTRIC", "GHOST"], "NATIONAL_DEX_ROTOM") == []
    assert special_tutor_moves("SPECIES_DITTO", ["NORMAL"], "NATIONAL_DEX_DITTO") == []


def test_special_tutor_rules():
    fire = [m for m, _ in special_tutor_moves("SPECIES_CHARMANDER", ["FIRE"], "NATIONAL_DEX_CHARMANDER")]
    assert set(fire) == {"MOVE_FLAMEBURST", "MOVE_MYSTICALFIRE", "MOVE_INCINERATE"}
    pika = dict(special_tutor_moves("SPECIES_PIKACHU", ["ELECTRIC"], "NATIONAL_DEX_PIKACHU"))
    assert "MOVE_VOLTTACKLE" in pika
    dragon = dict(special_tutor_moves("SPECIES_DRATINI", ["DRAGON"], "NATIONAL_DEX_DRATINI"))
    assert "friendship" in dragon["MOVE_DRACOMETEOR"].lower()
    assert "MOVE_SECRETSWORD" not in dict(special_tutor_moves("SPECIES_KELDEO", ["WATER", "FIGHTING"], "NATIONAL_DEX_KELDEO"))


def test_collapse_rule(roster):
    keys = [e.key for e in roster]
    assert {"SPECIES_LYCANROC", "SPECIES_LYCANROC_N", "SPECIES_LYCANROC_DUSK"} <= set(keys)
    assert len(keys) == len(set(keys))


def test_kangaskhan_power_up_punch_matches_source(roster, paths):
    k = next(e for e in roster if e.key == "SPECIES_KANGASKHAN")
    src = {m for _, m in levelup(paths)["SPECIES_KANGASKHAN"]} | set(egg_moves(paths).get("SPECIES_KANGASKHAN", []))
    # Power-Up Punch is not a TM/tutor in this game, so only level-up/egg can grant it
    assert ("MOVE_POWERUPPUNCH" in all_moves(k)) == ("MOVE_POWERUPPUNCH" in src)


def _egg(roster, key):
    return set(next(e for e in roster if e.key == key).moves["egg"])


def test_regional_forms_use_their_own_egg_family(roster, paths):
    src = egg_moves(paths)
    assert _egg(roster, "SPECIES_NINETALES_A") == set(src["SPECIES_VULPIX_A"])


def test_incense_babies_include_the_second_stage_list(roster, paths):
    src = egg_moves(paths)
    assert "MOVE_BELLYDRUM" in _egg(roster, "SPECIES_AZUMARILL")
    assert _egg(roster, "SPECIES_AZUMARILL") == set(src.get("SPECIES_AZURILL", [])) | set(src["SPECIES_MARILL"])


def test_form_labels_for_dex_forms(roster):
    by = {e.key: e for e in roster}
    assert by["SPECIES_ZIGZAGOON_G"].form == "Galarian"
    assert by["SPECIES_PORYGON_Z"].form is None          # its own species, not a Porygon form
    assert by["SPECIES_WISHIWASHI_S"].form == "School"
    assert by["SPECIES_TOXTRICITY_LOW_KEY_GIGA"].form == "Low Key Mega G"


def test_dusk_time_range_is_exact(evo_links):
    dusk = [l["text"] for l in evo_links["SPECIES_ROCKRUFF"] if l["to"] == "SPECIES_LYCANROC_DUSK"]
    assert dusk == ["Lv. 25, 5 PM–7:59 PM"]


def test_item_names_are_never_guessed(evo_links):
    texts = [l["text"] for ls in evo_links.values() for l in ls]
    assert not any("?" in t for t in texts)
    garb = [l["text"] for l in evo_links["SPECIES_GARBODOR"]]
    assert garb and all(t.startswith("Mega Evolve holding ") for t in garb)


def test_unknown_item_raises(source_data):
    import pytest
    from tools.dexpage.roster import evolution_text
    with pytest.raises(ValueError):
        evolution_text(source_data, "EVO_ITEM", "ITEM_DOES_NOT_EXIST", "SPECIES_BULBASAUR", "0")
