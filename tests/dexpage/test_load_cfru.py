from tools.dexpage.load_cfru import ability_names, item_ids, moves


def test_move_aliases(paths):
    m = moves(paths)["MOVE_CEASELESSEDGE"]
    assert m["name"] == "Endless Edge" and m["official"] == "Ceaseless Edge"
    assert (m["type"], m["split"], m["accuracy"]) == ("DARK", "physical", 90)
    # ACTUAL_PLA_MOVE_POWERS is not defined in CFRU config, so the #else branch applies
    assert m["power"] == 80


def test_status_move(paths):
    m = moves(paths)["MOVE_GROWL"]
    assert m["split"] == "status" and m["power"] == 0


def test_ability_and_item_tables(paths):
    assert ability_names(paths)["ABILITY_OVERGROW"] == "Overgrow"
    assert item_ids(paths)["ITEM_LINK_STONE"] == 0x5B


def test_move_descriptions_and_effect_chance(paths):
    m = moves(paths)
    assert m["MOVE_SCALD"]["desc"] == "Boiling water is shot at the foe. It may also cause a burn."
    assert m["MOVE_SCALD"]["chance"] == 30
    assert m["MOVE_POUND"]["desc"].startswith("A physical attack delivered")   # vanilla text read from the ROM
    assert m["MOVE_POUND"]["chance"] == 0


def test_abilities_resolve_through_dpe_ids(paths):
    # DPE assigns the id; CFRU supplies the name, description and per-species renames at that id
    from tools.dexpage.load_cfru import ability_display
    assert ability_display(paths, "ABILITY_GULPMISSLE", "SPECIES_CRAMORANT", None, ["FLYING"])[0] == "Gulp Missile"
    assert ability_display(paths, "ABILITY_STEELY_SPIRIT", "SPECIES_PERRSERKER", None, ["STEEL"])[0] == "Steely Spirit"
    assert ability_display(paths, "ABILITY_TANGLINGHAIR", "SPECIES_DIGLETT", None, ["GROUND"])[0] == "Full Metal Body"   # 0xAF in CFRU
    assert ability_display(paths, "ABILITY_PROTEAN", "SPECIES_CINDERACE", "NATIONAL_DEX_CINDERACE", ["FIRE"])[0] == "Libero"


def test_no_raw_ability_constants_on_page(paths):
    from tools.dexpage.load_cfru import ability_display
    from tools.dexpage.load_dpe import base_stats
    for species, s in base_stats(paths).items():
        for a in s["abilities"] + ([s["hidden_ability"]] if s["hidden_ability"] else []):
            assert not ability_display(paths, a, species, None, s["types"])[0].startswith("ABILITY_"), (species, a)


def test_ability_effect_chances(paths):
    from tools.dexpage.load_cfru import ability_chances, ability_ids
    chances = ability_chances(paths)
    ids = ability_ids(paths)
    assert chances[ids["ABILITY_POISONTOUCH"]] == 30
    assert chances[ids["ABILITY_STATIC"]] == 33        # umodsi(Random(), 3) == 0
    assert chances[ids["ABILITY_STENCH"]] == 10
    assert ids["ABILITY_LEVITATE"] not in chances
