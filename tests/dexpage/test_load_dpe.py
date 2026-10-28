from tools.dexpage.load_dpe import (
    base_stats,
    dex_lists,
    egg_moves,
    evolutions,
    front_pic,
    habitat_forms,
    levelup,
    machine_compat,
    species_ids,
    species_names,
)


def test_dex_lists(paths):
    std, div = dex_lists(paths)
    assert len(std) == 390 and len(div) == 390
    assert std[0] == "SPECIES_BIDOOF" and div[0] == "SPECIES_ZIGZAGOON_G"
    assert len(set(std) & set(div)) == 94


def test_habitat_forms(paths):
    hf = habitat_forms(paths)
    assert hf["SPECIES_LYCANROC_DUSK"] == {"standard"}
    assert hf["SPECIES_VULPIX_A"] == {"divergent"}
    assert "SPECIES_ROTOM_HEAT" not in hf          # commented out


def test_bulbasaur(paths):
    b = base_stats(paths)["SPECIES_BULBASAUR"]
    assert (b["hp"], b["atk"], b["spe"]) == (45, 49, 45)
    assert b["types"] == ["GRASS", "POISON"]
    assert b["hidden_ability"] == "ABILITY_CHLOROPHYLL"
    assert b["gender"] == 12.5
    assert levelup(paths)["SPECIES_BULBASAUR"][2] == (3, "MOVE_VINEWHIP")
    assert "MOVE_SKULLBASH" in egg_moves(paths)["SPECIES_BULBASAUR"]


def test_machines(paths):
    mc = {(m["kind"], m["num"]): m for m in machine_compat(paths)}
    assert mc[("HM", 1)]["move"] == "MOVE_CUT"
    assert "SPECIES_BULBASAUR" in mc[("TM", 1)]["species"]
    assert mc[("Tutor", 1)]["move"] == "MOVE_FIREPUNCH"


def test_evolutions_raw(paths):
    evo = evolutions(paths)
    assert ("EVO_ITEM", "ITEM_LINK_STONE", "SPECIES_ALAKAZAM", "0") in evo["SPECIES_KADABRA"]


def test_front_pic(paths):
    assert front_pic(paths)["SPECIES_LYCANROC_N"].name == "gFrontSprite1046LycanrocN.png"


def test_species_names(paths):
    names = species_names(paths)
    ids = species_ids(paths)
    assert ids["SPECIES_KANGASKHAN"] == 0x73
    assert names["SPECIES_FARFETCHD"] == "Farfetch'd"
    assert names["SPECIES_NIDORAN_F"] == "Nidoran♀"


def test_tm_number_comes_from_filename(paths):
    # "77 - Psych Up.txt" has the header "TM55: Psych Up"; the game uses the filename number
    mc = {(m["kind"], m["num"]): m for m in machine_compat(paths)}
    assert mc[("TM", 77)]["move"] == "MOVE_PSYCHUP"
    assert mc[("TM", 55)]["move"] != "MOVE_PSYCHUP"


def test_duplicate_egg_entries_first_wins(paths):
    # GetEggMoves stops at the first matching entry; Cufant's second copy adds Double-Edge
    assert "MOVE_DOUBLEEDGE" not in egg_moves(paths)["SPECIES_CUFANT"]
