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
    return (checklist(page, place_maps(paths), paths, game_item_names(source_data)),)


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
    assert titles[-2:] == ["Postgame", "Ultra Episode"]
    # Secret Trail can't be explored before Strength
    assert titles.index("Secret Trail") > titles.index("After badge 7 (with Strength)")


def test_ferrox_village(result):
    got = entries(stage(result, "Ferrox Village"))
    assert not any(e["t"].startswith("Daily Berry") for e in got)  # once-a-day things aren't completion
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


def test_every_pickup_is_listed(result):
    # Collin: a map's item is on the list even when marts sell it
    assert "Honey" in texts(stage(result, "Orichelle Garden"))
    assert "Potion" in texts(stage(result, "Route 3")) and "Max Potion" in texts(stage(result, "Secret Trail"))
    assert "TM77 Psych Up" in texts(stage(result, "Secret Trail"))


def test_collins_hm_corrections(result):
    surf = stage(result, "After Pluto HQ (with Surf)")
    assert "Nugget" in texts(surf, "Route 2") and "Calcium" in texts(surf, "Torma Cave")
    assert "Max Elixir" in texts(surf, "Peradon Forest") and "Rare Candy" in texts(surf, "Forgotten Manse")
    assert "Rare Candy" not in texts(surf, "Route 8")
    zinc = next(e for e in entries(stage(result, "Route 19")) if e["t"] == "Zinc")
    assert zinc["need"] == "Cut"
    # Routes 14-16 are only reached by Surf, so nothing there is tagged with it
    for place in ("Route 14", "Route 15 North", "Route 15 South", "Route 16"):
        assert not any("Surf" in e.get("need", "") for e in entries(stage(result, place)))
    volcano = entries(stage(result, "Carnelidge Volcano"))
    assert next(e for e in volcano if e["t"] == "Charizite Y")["need"] == "Lava Surf"
    assert not any(e.get("need") == "Surf" for e in volcano)


def test_ultra_episode_has_its_own_section(result):
    ultra = texts(stage(result, "Ultra Episode"))
    assert "Ultra Wormhole (Kartana)" in ultra and "Necrozma" in ultra and "Cosmog" in ultra
    assert any(t.startswith("Ultra Episode: start it") for t in ultra)
    assert not any("Ultra Wormhole" in t for t in texts(stage(result, "Postgame")))
    assert not any("Alistair after the credits" in t for t in texts(stage(result, "Postgame")))


def test_collins_review_round(result):
    shaymin = next(e for e in entries(stage(result, "Route 18")) if e["t"].startswith("Shaymin Form Change Girl"))
    assert shaymin["only"] == "Standard"
    assert not any(e["k"] == "story" and "rival" in e["t"] for e in entries(stage(result, "Emraldin Quay")))
    assert not any("shop" in e["t"].lower().split(": ")[-1] for e in everything(result) if e["k"] == "npc")
    zeraora = next(e for e in entries(stage(result, "Mimmett Jungle")) if e["t"].startswith("Zeraora"))
    assert zeraora["fl"] == "Marsh Cave" and zeraora["id"] == "mimmett-jungle/wild/zeraora-room/4-2"


def test_shortened_item_names_link_to_their_item(result, page):
    by_text = {e["t"]: e for e in everything(result)}
    assert page["items"][by_text["HvyDutyBoots"]["item"]]["name"] == "Heavy Duty Boots"
    assert page["items"][by_text["NeverMeltIce"]["item"]]["name"] == "Never Melt Ice"


def test_pokemon_link_to_their_entries(result, page):
    ampharos = next(e for e in entries(stage(result, "Heleo Ranch")) if e["k"] == "wild")
    linked = [(ampharos["t"][a:b], page["mons"][i]["name"]) for a, b, i in ampharos["p"]]
    assert linked == [("Ampharos", "Ampharos"), ("Pidgeot", "Pidgeot")]
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


def test_regional_forms_are_named(result, paths):
    route_1 = next(m for m in place_maps(paths) if m["name"] == "Route 1")
    assert "Sandygast (Alolan Diglett in Divergent)" in [m["t"] for m in route_1["markers"] if m["k"] == "wild"]
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


def test_daily_things_are_left_out(result, page, source_data, paths):
    daily = []
    checklist(page, place_maps(paths), paths, game_item_names(source_data), daily)
    left_out = [t for _, t in daily]
    assert "Gym Leader rematch: Stella" in left_out and "Sandygast (Alolan Diglett in Divergent)" in left_out
    # people whose script sets a flag the game clears each day count too, whatever their text says
    assert any(t.startswith("Lucky Draw Lady") for t in left_out) and "Wonder Pick" in left_out
    shown = [e["t"] for e in everything(result)]
    assert not set(left_out) & set(shown)
    assert "Ultra Wormhole (Kartana)" in shown  # in a daily-trap forest, but a one-off
    assert not any("daily" in e for e in everything(result))


# ---- ticking the list from a save file (save_flags.py; the page's own reader is checked against it in Chrome)

def test_most_entries_can_be_read_from_a_save(result):
    every = everything(result)
    blind = [e["t"] for e in every if "sv" not in e]
    assert len(blind) < 25 and all(e["sv"] for e in every if "sv" in e)
    assert all("sv" in e for e in every if e["k"] == "item")
    by_id = {e["id"]: e for e in every}
    assert by_id["route-2/hidden/area-1/29-72"]["sv"] == [1000 + 2]             # FLAG_HIDDEN_ITEMS_START + its id
    assert by_id["route-2/npc/area-1/24-10"]["sv"] == [0x2C0]                   # the flag the rival's script checks and sets
    assert by_id["ultra-space/npc/ultra-space/38-49"]["sv"] == [0x276]          # received Poipole, not "Poipole explained"
    assert by_id["rhodanzi-city/story/gym"]["sv"] and all(0x500 <= f < 0x800 for f in by_id["rhodanzi-city/story/gym"]["sv"])
    assert by_id["route-9/story/pluto"]["sv"] == by_id["route-11-south/story/ronald"]["sv"]
    assert by_id["ferrox-village/story/library"]["sv"] == [["i", 0x1B5]]        # HM01 in the bag
    assert by_id["forgotten-manse/wild/bf/19-2"]["sv"] == [["&", 0x6D, ["v", 0x4073, 5]]]


def _saves(paths):
    folder = paths.dpe.parent / "PokemonShootingStars" / "saves"
    if not folder.is_dir():
        pytest.skip("no saves folder beside the repos")
    return folder


def test_saves_tick_the_list(result, paths):
    from tools.dexpage import save_flags
    folder = _saves(paths)
    read = lambda name: save_flags.read_save((folder / name).read_bytes())
    texts_of = lambda save: {e["t"] for e in everything(result) if e["id"] in save_flags.ticked(result[0], save)}
    assert save_flags.read_save(b"\x00" * 0x20000) is None and save_flags.read_save(b"junk") is None
    fresh = texts_of(read("PreGym1_HardMode.sav"))
    assert fresh == {"Follow the story to choose your starter", "Receive the Town Map and Running Shoes from Mom",
                     "Battle your rival for the first time", "Meet Professor Hawthorne and receive the Pokédex and Poké Balls"}
    # a run that picked up nothing: story only, plus the two keys Pluto HQ can't be finished without
    bare = read("PreE4_SkippedCutscenes_PickedUpNothing.sav")
    picked = {e["t"] for e in everything(result) if e["id"] in save_flags.ticked(result[0], bare) and e["k"] in ("item", "hidden")}
    assert picked == {"Cypress Key", "Owl Key"}
    assert "Defeat Leaders Dennis & Dee for the Double Badge" in texts_of(bare)
    done = texts_of(read("CompletedSave.sav"))
    assert len(save_flags.ticked(result[0], read("CompletedSave.sav"))) > 400 and "Defeat Champion Selene and enter the Hall of Fame" in done and "Necrozma" in done
    assert "Necrozma" not in texts_of(read("UltraEpisode_PreNecrozma.sav"))
    assert len(texts_of(read("SteamDeckSave.srm"))) > 200            # RetroArch's .srm is the same file
    assert read("Divergent_AlmostAllPokemonCaught.sav") is not None  # 16 bytes of clock data after the save
