import pytest

from tools.dexpage import checklist_data as H
from tools.dexpage.build import TEMPLATE, game_item_names, page_data
from tools.dexpage.checklist import checklist, hm_badges
from tools.dexpage.maps.export import place_maps


@pytest.fixture(scope="module")
def page(source_data, roster, evo_links):
    return page_data(source_data, roster, evo_links)


@pytest.fixture(scope="module")
def result(page, source_data, paths):
    dropped = []
    out = checklist(page, place_maps(paths), paths, game_item_names(source_data), dropped)
    return out, dropped


def stage(result, title):
    return next(st for st in result[0]["stages"] if st["title"] == title)


def entries(st, place=None):
    return [e for g in st["groups"] if place in (None, g["place"]) for e in g["entries"]]


def texts(st, place=None):
    return [e["t"] for e in entries(st, place)]


def everything(result):
    return [e for st in result[0]["stages"] for e in entries(st)]


def test_cut_needs_the_second_badge(paths):
    assert hm_badges(paths)["Cut"] == 2


def test_stages_follow_the_playthrough(result):
    titles = [st["title"] for st in result[0]["stages"]]
    stops = [s if isinstance(s, str) else s[0] for s in H.ORDER]
    assert [t for t in titles if t in stops] == [s for s in stops if s in titles]
    assert titles.index("After badge 2 (with Cut)") == titles.index("Ferrox Village") + 1
    # Surf's badge is Bruccie Village's, but the HM comes at Pluto HQ
    assert titles.index("After Pluto HQ (with Surf)") == titles.index("Pluto HQ") + 1
    assert titles[-1] == "Postgame"


def test_ferrox_village(result):
    got = entries(stage(result, "Ferrox Village"))
    berry = next(e for e in got if e["t"].startswith("Daily Berry"))
    assert berry["daily"] == 1
    assert any(e["t"] == "Trade your Snom for a Chinchou (Vanillite for an Eelektrik in Divergent)" for e in got)
    # Cut comes with the library puzzle, not as an errand of its own
    assert not any(e["t"].startswith("Alistair") for e in got)
    assert any("HM01 Cut" in e["t"] and e["k"] == "story" for e in got)


def test_cut_items_wait_for_badge_two(result):
    after = stage(result, "After badge 2 (with Cut)")
    assert "TM12 Taunt" in texts(after, "Route 3")
    assert "TM87 Swagger" in texts(after, "Olenic Town")
    assert "TM12 Taunt" not in texts(stage(result, "Route 3"))
    # a place reached after Cut keeps its Cut items, tagged
    endure = next(e for e in entries(stage(result, "Route 5")) if e["t"] == "TM58 Endure")
    assert endure["need"] == "Cut"


def test_common_items_left_out(result):
    names = [e["t"] for e in everything(result)]
    assert "Potion" not in names and "Repel" not in names and "Poké Ball" not in names
    assert ("Route 3", "Potion") in result[1]
    assert "Star Piece" in names


def test_shortened_item_names_link_to_their_item(result, page):
    by_text = {e["t"]: e for e in everything(result)}
    assert page["items"][by_text["HvyDutyBoots"]["item"]]["name"] == "Heavy Duty Boots"
    assert page["items"][by_text["NeverMeltIce"]["item"]]["name"] == "Never Melt Ice"


def test_pokemon_link_to_their_entries(result, page):
    sandygast = next(e for e in entries(stage(result, "Route 1")) if e["k"] == "wild")
    linked = [(sandygast["t"][a:b], page["mons"][i]["name"]) for a, b, i in sandygast["p"]]
    assert linked == [("Sandygast", "Sandygast"), ("Alolan Diglett", "Diglett")]
    trade = next(e for e in entries(stage(result, "Tsarvosa City")) if e["t"].startswith("Trade your Slowbro"))
    named = [(trade["t"][a:b], page["mons"][i]["form"]) for a, b, i in trade["p"]]
    assert ("Galarian Slowbro", "Galarian") in named and ("Slowbro", None) in named


def test_gift_lists_are_written_out(result):
    assert not any(" +" in e["t"] for e in everything(result) if e["k"] == "npc")
    assert "Receive the Town Map and Running Shoes from Mom" in texts(stage(result, "Anthra Town"))
    assert not any(e["t"].startswith("Mom") for e in everything(result))


def test_rival_events_say_when_they_end(result):
    rival = next(e for e in entries(stage(result, "Route 2")) if e["t"].startswith("Rival:"))
    assert rival["until"] == "Until the Terrain Badge is obtained"
    spa = next(e for e in entries(stage(result, "Scalding Spa")) if e["t"].startswith("Rival:"))
    assert spa["until"] == "Until the Talent Badge is obtained"


def test_bosses_link_to_their_trainers(result, page):
    gym = next(e for e in entries(stage(result, "Heleo City")) if "Leader Raine" in e["t"])
    assert len(gym["tr"]) == 3  # one team per badge count
    assert all(page["trainers"][n]["name"] == "Raine" for n in gym["tr"])


def test_regional_forms_are_named(result, page):
    sandygast = next(e for e in entries(stage(result, "Route 1")) if e["k"] == "wild")
    assert sandygast["t"] == "Sandygast (Alolan Diglett in Divergent)"
    assert [page["mons"][i]["form"] for _, _, i in sandygast["p"]] == [None, "Alolan"]
    assert "Ampharos (Pidgeot in Divergent)" in texts(stage(result, "Heleo Ranch"))


def test_one_mode_items_are_tagged(result):
    by_text = {e["t"]: e for e in everything(result)}
    assert by_text["Beedrillite"]["only"] == "Divergent"
    assert by_text["Cameruptite"]["only"] == "Divergent"
    assert "only" not in by_text["TM12 Taunt"]


def test_hand_placed_entries(result):
    f2 = texts(stage(result, "Hesson Pass F2"))
    assert "Charizite X" in f2 and "Light Clay" in f2 and "TM67 Smart Strike" in f2
    assert "Star Piece" in texts(stage(result, "Hesson Pass"))
    titles = [st["title"] for st in result[0]["stages"]]
    assert titles.index("Hesson Pass F2") > titles.index("Carnelidge Volcano")
    assert any(t.startswith("Gentleman: gives Decoder") for t in texts(stage(result, "Uteyan Ruins"), "Laplaz Town"))
    assert any(t.startswith("Stella and Iris") for t in texts(stage(result, "After badge 7 (with Strength)"), "Daimyn City"))
    assert "Psychic Sister: IV Grading Unlock" in texts(stage(result, "Laplaz Town"))
    revive = next(e for e in entries(stage(result, "Route 12 West")) if e["t"] == "Revive")
    assert revive["need"] == "Rock Smash"  # mart stock, but listed: it sits behind a rock
    assert not any(e["k"] == "npc" for e in entries(stage(result, "Pluto HQ")))  # the keys come with the story beats
    assert "Trainer House: win the grand prize, the Mach Bike" in texts(stage(result, "Heleo City"))


def test_every_map_place_has_a_stage(result, paths):
    listed = {g["place"] for st in result[0]["stages"] for g in st["groups"]}
    assert {"Victory Road", "Battle Frontier", "Seppire Cove"} <= listed


def test_ids_are_unique(result):
    ids = [e["id"] for e in everything(result)]
    assert len(ids) == len(set(ids))


def test_tab_sits_before_docs():
    html = TEMPLATE.read_text(encoding="utf-8")
    assert 0 < html.index('data-viewtab="check"') < html.index('data-viewtab="docs"')
    assert html.index('data-viewtab="places"') < html.index('data-viewtab="check"')
