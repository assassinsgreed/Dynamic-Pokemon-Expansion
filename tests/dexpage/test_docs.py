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


from tools.dexpage.docs import clean_versions, type_chips  # noqa: E402


def test_version_references_removed():
    assert clean_versions("Sand Spit (v1.3) or Aeriliate (v1.4+)") == "Aeriliate"
    assert clean_versions("In v1.3 it can also evolve by getting 3+ crits") == "It can also evolve by getting 3+ crits"
    assert clean_versions("Starting in v1.4, the player can upgrade") == "The player can upgrade"
    assert clean_versions("Relic seller (v1.4+)") == "Relic seller"
    assert clean_versions("Pokemon are randomized.<br>Note: this is fully supported as of v1.4. Some items") == "Pokemon are randomized.<br>Some items"
    assert clean_versions("Introduced in v1.4") == ""
    assert clean_versions("Land in v1.3.<br>Surf or good/super rod in v1.4.") == "Surf or good/super rod"
    assert clean_versions("Extra Hard (v1.3), where all trainers") == "Extra Hard, where all trainers"


def test_no_version_text_left_in_rendered_docs():
    import re
    from tools.dexpage.docs import load_docs, render_topic
    for g in load_docs():
        for t in g["topics"]:
            html = render_topic(t, images={})
            assert not re.search(r"\bv1\.\d", html), (t["title"], re.search(r".{0,60}\bv1\.\d.{0,40}", html).group(0))


def test_rows_removed_from_pool_are_dropped():
    from tools.dexpage.docs import load_docs, render_topic
    swarms = next(t for g in load_docs() for t in g["topics"] if t["title"] == "Swarms")
    assert "Removed from pool" not in render_topic(swarms, images={})


def test_type_chips():
    assert type_chips("Water/<br>Steel", whole_cell=True) == '<span class="type t-WATER">Water</span>/<span class="type t-STEEL">Steel</span>'
    assert 'class="type t-FIRE"' in type_chips("Any fire type Pokemon")
    assert type_chips("Fire Stone and Rock Smash") == "Fire Stone and Rock Smash"


def test_bold_cells_keep_bold_unless_they_are_types():
    assert type_chips("<b>Grass</b>", whole_cell=True) == '<span class="type t-GRASS">Grass</span>'
    assert type_chips("<b>Venusaur</b>", whole_cell=True) == "<b>Venusaur</b>"


def test_numeric_table_columns_right_aligned():
    from tools.dexpage.docs import render_topic
    topic = {"blocks": [{"t": "table", "rows": [["<b>Pokemon</b>", "<b>HP</b>", "<b>Info</b>"],
                                                ["<b>Venusaur</b>", "80", "Even Bulkier"], ["Lapras", "130", "Less speed"]]}]}
    html = render_topic(topic, images={})
    assert '<th class="n"><b>HP</b></th>' in html and '<td class="n">80</td>' in html
    assert "<td>Even Bulkier</td>" in html
