from tools.dexpage.items import load_items, load_machine_locations


def test_items_loaded_with_categories():
    items = {i["name"]: i for i in load_items()}
    assert items["Lax Incense"]["category"] == "Breeding"
    assert "Route 2" in items["Lax Incense"]["where"]
    assert items["Cheri Berry"]["category"] == "Berries"
    assert items["Venusaurite-G"]["category"] == "Mega Stones"


def test_machine_locations():
    tms = load_machine_locations()
    assert tms[("TM", 2)] == {"move": "Dragon Claw", "where": ["Rubarr Desert B1F"], "requires": "Strength, Rock Smash"}
    assert tms[("HM", 1)]["move"] == "Cut"
