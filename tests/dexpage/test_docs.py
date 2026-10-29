from tools.dexpage.docs import load_docs, render_topic


def test_docs_grouped_by_heading_one():
    groups = {g["title"]: g for g in load_docs()}
    assert "Battle Changes" in groups and "Postgame Content" in groups
    topics = {t["title"] for t in groups["Battle Changes"]["topics"]}
    assert {"Critical Captures", "Frostbite", "Mega Pokemon"} <= topics


def test_overlapping_topics_skipped():
    groups = {g["title"]: g for g in load_docs()}
    assert "Locations" not in groups and "Dungeon Maps" not in groups
    titles = {t["title"] for g in groups.values() for t in g["topics"]}
    for overlap in ("TMs and HMs", "Move Tutors", "Trades", "Gifts", "Secondary Shops", "Pokedex and Wild Encounters"):
        assert overlap not in titles


def test_topic_blocks_render():
    groups = {g["title"]: g for g in load_docs()}
    gameplay = {t["title"]: t for t in groups["Gameplay Features"]["topics"]}
    html = render_topic(gameplay["Game Modifiers"], images={})
    assert "<table" in html and "<td" in html
    frontier = render_topic({t["title"]: t for t in groups["Postgame Content"]["topics"]}["Battle Frontier"], images={})
    assert "<h4" in frontier and "<li" in frontier
