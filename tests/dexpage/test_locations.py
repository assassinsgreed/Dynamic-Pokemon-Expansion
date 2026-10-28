from tools.dexpage.locations import load_encounters


def test_notes_drop_references_to_other_sheet_tabs():
    notes = [r["notes"] for r in load_encounters()]
    assert not any("tab." in n for n in notes)
    assert "Trade your Snom." in notes
