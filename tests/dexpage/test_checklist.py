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


def test_rival_events_say_when_they_end(result):
    rival = next(e for e in entries(stage(result, "Route 2")) if e["t"].startswith("Rival:"))
    assert rival["until"] == "Until the Terrain Badge is obtained"
    spa = next(e for e in entries(stage(result, "Scalding Spa")) if e["t"].startswith("Rival:"))
    assert spa["until"] == "Until the Talent Badge is obtained"


def test_bosses_link_to_their_trainers(result, page):
    gym = next(e for e in entries(stage(result, "Heleo City")) if "Leader Raine" in e["t"])
    assert len(gym["tr"]) == 3  # one team per badge count
    assert all(page["trainers"][n]["name"] == "Raine" for n in gym["tr"])


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
