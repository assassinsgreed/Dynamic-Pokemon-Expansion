from tools.dexpage.locations import load_encounters


def test_notes_drop_references_to_other_sheet_tabs():
    notes = [r["notes"] for r in load_encounters()]
    assert not any("tab." in n for n in notes)
    assert "Trade your Snom." in notes


def test_trade_notes_say_what_to_send():
    rows = {(r["name"], r["mode"], r["method"]): r["notes"] for r in load_encounters()}
    assert rows["Noibat", "Standard", "🔄 In-game trade"].startswith("Trade your Lillipup. Offered only if")
    assert rows["Scraggy", "Standard", "🥚 Egg"] == "Trade any Egg. Rival Egg swap."
    assert rows["Chinchou", "Standard", "🔄 In-game trade"] == "Trade your Snom."   # not said twice
    # "at any Battle Frontier facility" isn't an "any Pokémon" trade; forms read the way the page names them
    assert rows["Ditto", "Both", "🔄 In-game trade"].startswith("Trade your Heat Rotom. Needs a 5-win streak")
    assert rows["Boldore", "Standard", "🔄 In-game trade"].startswith("Rival event: send any Pokémon")


def test_swarm_notes_say_when_swarming():
    notes = [r["notes"] for r in load_encounters()]
    assert not any("Swarm days only" in n for n in notes)
    assert "When swarming (one random swarm per day)." in notes


def test_time_of_day_rates_are_split_out():
    rows = {(r["name"], r["mode"]): r for r in load_encounters() if r["location"] == "Varisi Forest" and "Grass" in r["method"]}
    assert rows["Pikipek", "Standard"]["times"] == {"day": "20%"}
    assert rows["Hoothoot", "Standard"]["times"] == {"night": "20%"}
    assert not rows["Blipbug", "Standard"]["times"]
    # Each time of day's grass rates add up to 100%, like the game's tables
    for mode in ("Standard", "Divergent"):
        for time in ("day", "night"):
            total = sum(float((r["times"] or {time: r["rate"]}).get(time, "0%").rstrip("%"))
                        for (_, m), r in rows.items() if m == mode)
            assert round(total) == 100, (mode, time, total)
    both = [r["times"] for r in load_encounters() if len(r.get("times", {})) == 2]
    assert {"day": "10%", "night": "15%"} in both
