"""Turns the roster into the page: one JSON blob + sprite sheet embedded in template.html."""

import base64
import json
import re
import unicodedata
from pathlib import Path

from .roster import Entry, SourceData

TEMPLATE = Path(__file__).with_name("template.html")
STAT_KEYS = ("hp", "atk", "def", "spa", "spd", "spe")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())


def search_keys(name: str, official: str | None) -> list[str]:
    """Normalised strings a search should match: the in-game name and, if different, the official one."""
    keys = [_norm(name)]
    if official and _norm(official) not in keys:
        keys.append(_norm(official))
    return keys


def _how(method: str, item: tuple | str) -> str:
    if method == "level":
        return "Evo" if item[0] == 0 else f"Lv {item[0]}"
    if method == "egg":
        return "Egg"
    if method in ("tm", "tutor"):
        return item[0]
    return f"Special: {item[1]}"


def _move_of(method: str, item: tuple | str) -> str:
    if method == "egg":
        return item
    return item[0] if method == "special" else item[1]


def _mon(data: SourceData, e: Entry, index: dict, links: list[dict]) -> dict:
    s = e.stats
    official = e.key.removeprefix("SPECIES_").replace("_", " ").title()
    return {
        "key": e.key,
        "name": e.name,
        "form": e.form,
        "modes": e.modes,
        "dex": e.dex,
        "types": s["types"],
        "stats": [s[k] for k in STAT_KEYS],
        "abilities": [data.abilities.get(a, a) for a in s["abilities"]],
        "hidden": data.abilities.get(s["hidden_ability"]) if s["hidden_ability"] else None,
        "gender": s["gender"],
        "eggGroups": [g.replace("_", " ").title() for g in s["egg_groups"]],
        "catchRate": s["catch_rate"],
        "growth": s["growth"].replace("_", " ").title(),
        "evs": [s["ev_yield"][k] for k in STAT_KEYS],
        "family": e.family,
        "evo": [[index[l["to"]], l["text"]] for l in links],
        "s": search_keys(e.name, official),
        "movesOf": index.get(e.base) if e.battle_form else None,
    }


def page_data(data: SourceData, roster: list[Entry], evo_links: dict) -> dict:
    index = {e.key: i for i, e in enumerate(roster)}
    moves = {k: {"name": m["name"], "official": m["official"] if _norm(m["official"]) != _norm(m["name"]) else None,
                 "type": m["type"], "split": m["split"], "power": m["power"],
                 "acc": m["accuracy"], "pp": m["pp"], "learners": []}
             for k, m in data.moves.items()}
    for i, e in enumerate(roster):
        if e.battle_form:
            continue  # listed under its base species instead
        for method in ("level", "egg", "tm", "tutor", "special"):
            for item in e.moves.get(method, []):
                move = _move_of(method, item)
                if move in moves:
                    moves[move]["learners"].append([i, _how(method, item)])
    return {
        "mons": [_mon(data, e, index, evo_links.get(e.key, [])) for e in roster],
        "moves": moves,
    }


def render(data: dict, sheet: bytes, offsets: dict) -> str:
    data = dict(data, mons=[dict(m, sp=offsets[m["key"]]) for m in data["mons"]])
    # Keys keep the move table compact and stable; the page only needs them as ids.
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    sprites = "data:image/webp;base64," + base64.b64encode(sheet).decode()
    return (TEMPLATE.read_text(encoding="utf-8")
            .replace("__DEX_DATA__", blob)
            .replace("__SPRITE_SHEET__", sprites))
