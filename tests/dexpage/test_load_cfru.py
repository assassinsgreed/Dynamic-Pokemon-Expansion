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
