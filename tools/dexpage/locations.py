"""Encounter locations, from the Encounters tab of the "Pokémon Amethyst: Where to Find Every Pokémon" sheet.

encounters.csv is a hand-exported copy (File → Download → CSV on that tab); replace it when the sheet changes."""

import csv
import re
import unicodedata
from pathlib import Path

ENCOUNTERS_CSV = Path(__file__).with_name("encounters.csv")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _rate(value: str) -> str:
    try:
        pct = float(value) * 100
    except ValueError:
        return value
    return f"{pct:.0f}%" if pct >= 1 or pct == 0 else f"{pct:.1f}%"


def load_encounters(path: Path = ENCOUNTERS_CSV) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    result = []
    for r in rows:
        name = r["Pokémon"].replace("\\e", "é")  # the sheet keeps the game's \e escape for é
        m = re.fullmatch(r"(.*?)\s*\((.+)\)", name)
        result.append({
            "name": m.group(1) if m else name,
            "form": m.group(2) if m else None,
            "mode": r["Mode"],
            "method": r["Method"],
            "location": r["Location"],
            "sub": r["Sub-area"],
            "rate": _rate(r["Rate"]) if r["Rate"] else "",
            "levels": r["Levels"],
            "item": r["Held item"],
            # The sheet's other tabs don't exist on the page
            "notes": re.sub(r"\s*Details on the \w+ tab\.", "", r["Notes"]).strip(),
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
        # Held items describe the Pokémon, not the place, so they go on the profile instead
        row = {k: v for k, v in r.items() if k not in ("name", "form", "item") and v}
        for held in filter(None, (h.strip() for h in r["item"].split(","))):
            held_items.setdefault(key, [])
            if held not in held_items[key]:
                held_items[key].append(held)
        if variant:
            row["variant"] = variant
        by_key.setdefault(key, []).append(row)
    return by_key, held_items, unmatched
