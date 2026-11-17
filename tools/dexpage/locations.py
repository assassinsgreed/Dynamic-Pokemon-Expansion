"""Encounter locations, from the Encounters tab of the "Pokémon Amethyst: Where to Find Every Pokémon" sheet.

encounters.csv is a hand-exported copy (File → Download → CSV on that tab); replace it when the sheet changes.
trades.csv is the same for the Trades tab, which says what each trader wants (the Encounters tab's notes often don't)."""

import csv
import re
import unicodedata
from pathlib import Path

ENCOUNTERS_CSV = Path(__file__).with_name("encounters.csv")
TRADES_CSV = Path(__file__).with_name("trades.csv")
# Methods where the Pokémon is an ordinary wild one; held items from other rows (events, legendaries) aren't wild items
WILD_METHODS = ("Grass", "Cave", "Indoors", "Surfing", "Rod", "Rock Smash", "Swarm")
# Map 1.30, outside Daimyn Factory, is Route 9 to the game (its map section) and to the sheet (sub-area
# "Daimyn City Factory"), but it has its own encounter table, so the page lists it as its own place (Collin)
FACTORY_OVERWORLD = "Daimyn Factory Overworld"
# (location, sub-area) → the (place, sub-area) the page files it under. The tunnel is map 1.8, the Forgotten Manse map's
# Underground floor; the sheet lists it under Route 8, whose map section it shares (Collin: it's Forgotten Manse)
OWN_PLACES = {("Route 9", "Daimyn City Factory"): (FACTORY_OVERWORLD, ""),
              ("Route 8", "Forgotten Manse Tunnel"): ("Forgotten Manse", "Underground")}
# Sub-area names the page shows differently from the sheet (the sheet stays as Collin keeps it)
SUB_AREA_NAMES = {"Volcanion Room": "Hidden Chamber"}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _rate(value: str) -> str:
    try:
        pct = float(value) * 100
    except ValueError:
        return value
    return f"{pct:.0f}%" if pct >= 1 or pct == 0 else f"{pct:.1f}%"


def _by_time(rate: str, notes: str) -> tuple[str, str, dict[str, str]]:
    """Rows that differ by time of day show both rates in the rate cell ("☀️ 10% 🌙 15%") instead of a note.

    Also returns the rate per time of day ({"day": "20%"} for a Morning/Day-only row), so a place can list each
    time's encounters apart: the sheet's rates add up to 100% per time, not across both."""
    m = re.fullmatch(r"By time: Morning/Day (\d+%) · Evening/Night (\d+%)\.?", notes)
    if m:
        return f"☀️ {m.group(1)} 🌙 {m.group(2)}", "", {"day": m.group(1), "night": m.group(2)}
    m = re.fullmatch(r"(\d+%) during evening/night", notes)
    if m and rate:
        return f"☀️ {rate} 🌙 {m.group(1)}", "", {"day": rate, "night": m.group(1)}
    times = {"day": rate} if "Morning/Day only" in notes else {"night": rate} if "Evening/Night only" in notes else {}
    return rate, notes.replace("Morning/Day only", "☀️ Morning/Day only").replace("Evening/Night only", "🌙 Evening/Night only"), times


def _trade_asks(path: Path = TRADES_CSV) -> dict[tuple[str, str, str], str]:
    """(Pokémon, mode, location) → what the trader wants, from the Trades tab ("Lillipup", "Any Egg")."""
    with path.open(encoding="utf-8-sig", newline="") as f:
        return {(r["Pokémon"].removesuffix(" (Egg)"), r["Mode"], r["Location"]): r["You give"].strip()
                for r in csv.DictReader(f)}


def _with_ask(notes: str, ask: str | None) -> str:
    """Trade House notes only say which starter unlocks the trade; add what to send unless the note already says."""
    if not ask or re.search(r"\b(send|trade) any\b", notes, re.I) or ask.lower() in notes.lower():
        return notes
    ask = re.sub(r"(.+?) \((.+)\)", r"\2 \1", ask)  # "Rotom (Heat)" → "Heat Rotom"
    give = f"Trade any {ask[4:]}." if ask.lower().startswith("any ") else f"Trade your {ask}."
    return f"{give} {notes}".strip()


def load_encounters(path: Path = ENCOUNTERS_CSV) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    asks = _trade_asks()
    result = []
    for r in rows:
        notes = r["Notes"].strip()
        give = ""
        if "trade" in r["Method"] or "Egg" in r["Method"]:
            ask = asks.get((r["Pokémon"], r["Mode"], r["Location"]))
            notes = _with_ask(notes, ask)
            if ask and "trade" in r["Method"]:  # place cards say what to send ("Give Lillipup", "Give any Egg")
                ask = re.sub(r"(.+?) \((.+)\)", r"\2 \1", ask)  # "Rotom (Heat)" → "Heat Rotom"
                give = f"any {ask[4:]}" if ask.lower().startswith("any ") else ask
        rate, notes, times = _by_time(_rate(r["Rate"]) if r["Rate"] else "", notes)
        name = r["Pokémon"].replace("\\e", "é")  # the sheet keeps the game's \e escape for é
        m = re.fullmatch(r"(.*?)\s*\((.+)\)", name)
        own = OWN_PLACES.get((r["Location"], r["Sub-area"]))
        result.append({
            "name": m.group(1) if m else name,
            "form": m.group(2) if m else None,
            "mode": r["Mode"],
            "method": r["Method"],
            "location": own[0] if own else r["Location"],
            "sub": own[1] if own else ", ".join(SUB_AREA_NAMES.get(s, s) for s in r["Sub-area"].split(", ")) if r["Sub-area"] else "",
            "rate": rate,
            "levels": r["Levels"],
            "times": times,
            "item": r["Held item"],
            "give": give,
            # The sheet's other tabs don't exist on the page
            "notes": re.sub(r"\s*Details on the \w+ tab\.", "", notes).strip().replace("Swarm days only", "When swarming"),
        })
    return result


def attach_encounters(rows: list[dict], entries: list) -> tuple[dict[str, list[dict]], dict[str, list[str]], list[str]]:
    """Encounter rows per roster key, wild held items per key, and sheet names that matched no entry.

    "Name (Form)" matches the entry with that form label; a form the page has no row for (e.g. Pikachu's caps)
    falls back to the formless entry and keeps the form text as the row's variant."""
    by_name_form = {(_norm(e.name), _norm(e.form or "")): e.key for e in entries}
    by_key: dict[str, list[dict]] = {}
    held_items: dict[str, list[str]] = {}
    unmatched: list[str] = []
    for r in rows:
        name, form = _norm(r["name"]), _norm(r["form"] or "")
        key = by_name_form.get((name, form))
        variant = None
        if key is None and form:
            key, variant = by_name_form.get((name, "")), r["form"]
        if key is None:
            label = f"{r['name']} ({r['form']})" if r["form"] else r["name"]
            if label not in unmatched:
                unmatched.append(label)
            continue
        # Held items describe the Pokémon, not the place, so they go on the profile instead; only wild ones count
        # (the Heleo Ranch Ampharos's Sitrus Berry isn't one wild Ampharos carry)
        row = {k: v for k, v in r.items() if k not in ("name", "form", "item") and v}
        wild = any(m in r["method"] for m in WILD_METHODS)
        for held in filter(None, (h.strip() for h in r["item"].split(",") if wild)):
            held_items.setdefault(key, [])
            if held not in held_items[key]:
                held_items[key].append(held)
        if variant:
            row["variant"] = variant
        by_key.setdefault(key, []).append(row)
    return by_key, held_items, unmatched
