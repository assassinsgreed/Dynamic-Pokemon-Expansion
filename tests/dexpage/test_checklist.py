import pytest

from tools.dexpage import checklist_data as H
from tools.dexpage.build import TEMPLATE, page_data
from tools.dexpage.checklist import checklist, hm_badges
from tools.dexpage.maps.export import place_maps


@pytest.fixture(scope="module")
def result(source_data, roster, evo_links, paths):
    dropped = []
    out = checklist(page_data(source_data, roster, evo_links), place_maps(paths), paths, dropped)
    return out, dropped


def stage(result, title):
    return next(st for st in result[0]["stages"] if st["title"] == title)


def texts(st, place=None):
    return [e["t"] for g in st["groups"] if place in (None, g["place"]) for e in g["entries"]]


def test_cut_needs_the_second_badge(paths):
    assert hm_badges(paths)["Cut"] == 2


def test_stages_follow_the_playthrough(result):
    titles = [st["title"] for st in result[0]["stages"]]
    places = [t for t in titles if t in H.ORDER]
    assert places == [p for p in H.ORDER if p in places]
    assert titles.index("After badge 2 (with Cut)") == titles.index("Ferrox Village") + 1


def test_ferrox_village(result):
    got = texts(stage(result, "Ferrox Village"))
    assert any(t.startswith("Daily Berry") for t in got)
    assert any("Chinchou (Eelektrik in Divergent)" in t for t in got)
    assert any("Patch Badge" in t for t in got)
    berry = next(e for g in stage(result, "Ferrox Village")["groups"] for e in g["entries"] if e["t"].startswith("Daily Berry"))
    assert berry["daily"] == 1


def test_cut_items_wait_for_badge_two(result):
    after = stage(result, "After badge 2 (with Cut)")
    assert "TM12 Taunt" in texts(after, "Route 3")
    assert "TM87 Swagger" in texts(after, "Olenic Town")
    assert "TM12 Taunt" not in texts(stage(result, "Route 3"))


def test_common_items_left_out(result):
    everything = [t for st in result[0]["stages"] for t in texts(st)]
    assert "Potion" not in everything and "Repel" not in everything and "Poké Ball" not in everything
    assert ("Route 3", "Potion") in result[1]
    assert "Star Piece" in everything


def test_ids_are_unique(result):
    ids = [e["id"] for st in result[0]["stages"] for g in st["groups"] for e in g["entries"]]
    assert len(ids) == len(set(ids))


def test_tab_sits_before_docs():
    html = TEMPLATE.read_text(encoding="utf-8")
    assert 0 < html.index('data-viewtab="check"') < html.index('data-viewtab="docs"')
    assert html.index('data-viewtab="places"') < html.index('data-viewtab="check"')
