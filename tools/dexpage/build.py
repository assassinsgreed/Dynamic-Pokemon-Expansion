"""Turns the roster into the page: one JSON blob + sprite sheet embedded in template.html."""

import base64
import hashlib
import io
import json
import re
import sys
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw

from .locations import attach_encounters, load_encounters
from .paths import Paths
from .roster import Entry, SourceData, build_roster, evolution_links, load_source_data
from .sprites import build_sheet

TEMPLATE = Path(__file__).with_name("template.html")
SW_TEMPLATE = Path(__file__).with_name("sw.js")
STAT_KEYS = ("hp", "atk", "def", "spa", "spd", "spe")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())


def search_keys(name: str, *aliases: str | None) -> list[str]:
    """Normalised strings a search should match: the in-game name plus any distinct aliases."""
    keys = [_norm(name)]
    for alias in aliases:
        if alias and _norm(alias) not in keys:
            keys.append(_norm(alias))
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


def _mon(data: SourceData, e: Entry, index: dict, links: list[dict], locations: list[dict], held: list[str]) -> dict:
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
        "s": search_keys(e.name, official, f"{e.form} {e.name}" if e.form else None),
        "movesOf": index.get(e.base) if e.battle_form else None,
        "loc": locations,
        "held": held,
    }


def page_data(data: SourceData, roster: list[Entry], evo_links: dict) -> dict:
    index = {e.key: i for i, e in enumerate(roster)}
    moves = {}
    for k, m in data.moves.items():
        # Name-table labels are truncated too (NAME_POWER_UP_HIT), so the constant supplies the full name
        keys = search_keys(m["name"], m["official"], k.removeprefix("MOVE_"))
        moves[k] = {"name": m["name"], "official": m["official"] if _norm(m["official"]) != _norm(m["name"]) else None,
                    "type": m["type"], "split": m["split"], "power": m["power"],
                    "acc": m["accuracy"], "pp": m["pp"], "s": keys, "learners": []}
    for i, e in enumerate(roster):
        if e.battle_form:
            continue  # listed under its base species instead
        for method in ("level", "egg", "tm", "tutor", "special"):
            for item in e.moves.get(method, []):
                move = _move_of(method, item)
                if move in moves:
                    moves[move]["learners"].append([i, _how(method, item)])
    locations, held, unmatched = attach_encounters(load_encounters(), roster)
    return {
        "mons": [_mon(data, e, index, evo_links.get(e.key, []), locations.get(e.key, []), held.get(e.key, []))
                 for e in roster],
        "moves": moves,
        "unmatchedEncounters": unmatched,
    }


def _icon(size: int) -> bytes:
    """App icon: the Trozei Jirachi head on Amethyst purple."""
    img = Image.new("RGBA", (size, size), (50, 0, 119, 255))
    head = Image.open(BRAND_ICON).convert("RGBA").resize((int(size * 0.72),) * 2, Image.LANCZOS)
    offset = (size - head.size[0]) // 2
    img.alpha_composite(head, (offset, offset))
    out = io.BytesIO()
    img.save(out, "PNG")
    return out.getvalue()


MANIFEST = {
    "name": "Pokemon Amethyst Pokedex",
    "short_name": "Amethyst Dex",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "background_color": "#1a1226",
    "theme_color": "#5b2a9e",
    "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
              {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}],
}


def build(paths: Paths, out: Path) -> None:
    data = load_source_data(paths)
    roster = build_roster(data)
    links = evolution_links(data, {e.key for e in roster})
    sheet, offsets = build_sheet({e.key: data.sprites[e.key] for e in roster})
    page = page_data(data, roster, links)
    for name in page["unmatchedEncounters"]:
        print(f"warning: encounters.csv row for {name!r} matches no Pokémon on the page", file=sys.stderr)
    html = render(page, sheet, offsets).encode("utf-8")

    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_bytes(html)
    (out / "dex.html").write_bytes(html)  # "Download for offline use" target
    (out / "manifest.webmanifest").write_text(json.dumps(MANIFEST, indent=2), encoding="utf-8")
    (out / "icon-192.png").write_bytes(_icon(192))
    (out / "icon-512.png").write_bytes(_icon(512))
    cache = "dex-" + hashlib.sha256(html).hexdigest()[:12]
    (out / "sw.js").write_text(SW_TEMPLATE.read_text(encoding="utf-8").replace("__CACHE__", cache), encoding="utf-8")


BRAND_ICON = Path(__file__).with_name("jirachi-trozei.png")  # Jirachi's Pokémon Trozei head (Bulbapedia BT385.png)


def _brand_icon() -> str:
    return "data:image/png;base64," + base64.b64encode(BRAND_ICON.read_bytes()).decode()


def render(data: dict, sheet: bytes, offsets: dict) -> str:
    data = dict(data, mons=[dict(m, sp=offsets[m["key"]]) for m in data["mons"]])
    # Keys keep the move table compact and stable; the page only needs them as ids.
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    sprites = "data:image/webp;base64," + base64.b64encode(sheet).decode()
    return (TEMPLATE.read_text(encoding="utf-8")
            .replace("__DEX_DATA__", blob)
            .replace("__SPRITE_SHEET__", sprites)
            .replace("__BRAND_ICON__", _brand_icon()))
