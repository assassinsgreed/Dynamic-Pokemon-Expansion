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

from .docs import DOC_IMAGES, load_docs, render_topic, topic_text
from .items import load_items, load_machine_locations, load_tutors
import difflib

from .load_cfru import ability_chances, ability_display, ability_ids, ability_officials, marts
from .locations import attach_encounters, load_encounters
from .paths import DPE_ROOT, Paths
from .roster import Entry, SourceData, build_roster, evolution_links, load_source_data
from .rom import item_icons
from .sprites import build_sheet, pack

TEMPLATE = Path(__file__).with_name("template.html")
SW_TEMPLATE = Path(__file__).with_name("sw.js")
APP_SCRIPT = Path(__file__).with_name("app.js")  # the page's script, inlined so the page stays one file
ABILITY_DETAILS = Path(__file__).with_name("ability_details.json")  # hand-written, checked against CFRU's code
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


def _mon(data: SourceData, e: Entry, index: dict, links: list[dict], locations: list[dict], held: list[str],
         item_index: dict, item_by_const: dict) -> dict:
    s = e.stats
    national = data.national.get(e.key) or data.national.get(e.base)
    # CFRU shows some abilities under another name for particular species (Protean is Libero on Cinderace)
    # [name, description, % chance its effect triggers or 0]
    ability = lambda a: [*ability_display(data.paths, a, e.key, national, s["types"]),
                         ability_chances(data.paths).get(ability_ids(data.paths).get(a), 0)]
    official = e.key.removeprefix("SPECIES_").replace("_", " ").title()
    # Modes where it has no dex number but turns up in swarms; the page lists these after every numbered entry
    swarm = [mode for mode, field in (("Standard", "std"), ("Divergent", "div")) if mode in e.modes and not e.dex.get(field)
             and any("Swarm" in l["method"] and l["mode"] in (mode, "Both") for l in locations)]
    return {
        "key": e.key,
        "name": e.name,
        "form": e.form,
        "modes": e.modes,
        "dex": e.dex,
        "types": s["types"],
        "stats": [s[k] for k in STAT_KEYS],
        "abilities": [ability(a) for a in s["abilities"]],
        "hidden": ability(s["hidden_ability"]) if s["hidden_ability"] else None,
        "gender": s["gender"],
        "eggGroups": [g.replace("_", " ").title() for g in s["egg_groups"]],
        "catchRate": s["catch_rate"],
        "growth": s["growth"].replace("_", " ").title(),
        "evs": [s["ev_yield"][k] for k in STAT_KEYS],
        "family": e.family,
        # [target, method text, item index, the item's name as written in that text]
        "evo": [[index[l["to"]], l["text"], item_by_const.get(l.get("item")), data.items.get(l.get("item"))] for l in links],
        "swarm": swarm,
        "s": search_keys(e.name, official, f"{e.form} {e.name}" if e.form else None, "Swarm" if swarm else None),
        "movesOf": index.get(e.base) if e.battle_form else None,
        "loc": locations,
        "held": [[h, item_index.get(_norm(h.split(" (")[0]))] for h in held],
    }


def page_data(data: SourceData, roster: list[Entry], evo_links: dict) -> dict:
    index = {e.key: i for i, e in enumerate(roster)}
    moves = {}
    for k, m in data.moves.items():
        # Name-table labels are truncated too (NAME_POWER_UP_HIT), so the constant supplies the full name
        keys = search_keys(m["name"], m["official"], k.removeprefix("MOVE_"))
        moves[k] = {"name": m["name"], "official": m["official"] if _norm(m["official"]) != _norm(m["name"]) else None,
                    "type": m["type"], "split": m["split"], "power": m["power"],
                    "acc": m["accuracy"], "pp": m["pp"], "desc": m["desc"], "chance": m["chance"], "s": keys, "learners": []}
    for i, e in enumerate(roster):
        if e.battle_form:
            continue  # listed under its base species instead
        for method in ("level", "egg", "tm", "tutor", "special"):
            for item in e.moves.get(method, []):
                move = _move_of(method, item)
                if move in moves:
                    moves[move]["learners"].append([i, _how(method, item)])
    locations, held, unmatched = attach_encounters(load_encounters(), roster)
    items, item_index, item_by_const, icon_sheet = _items(data, held, evo_links)
    _attach_machine_locations(data, moves)
    tutors = _attach_tutor_locations(moves)
    mons = [_mon(data, e, index, evo_links.get(e.key, []), locations.get(e.key, []), held.get(e.key, []),
                 item_index, item_by_const) for e in roster]
    abilities = _abilities(mons, ability_officials(data.paths))
    _attach_ability_details(data.paths, abilities, moves)
    return {
        "docs": _docs({a["name"] for a in abilities}),
        "abilities": abilities,
        "tutors": tutors,
        "mons": mons,
        "items": items,
        "itemSheet": icon_sheet,
        "moves": moves,
        "unmatchedEncounters": unmatched,
    }


def _items(data: SourceData, held: dict[str, list[str]], evo_links: dict) -> tuple[list[dict], dict[str, int], dict[str, int], str]:
    """Feature-list items (plus wild held items and evolution items it doesn't list), each matched to its ROM icon."""
    const_for: dict[str, str] = {}
    for const, name in data.items.items():
        const_for.setdefault(_norm(name), const)
    for const in data.item_ids:
        const_for.setdefault(_norm(const.removeprefix("ITEM_")), const)  # full names the 12-char ROM name truncates

    items: list[dict] = []
    index: dict[str, int] = {}

    def add(name: str, category: str, where: list[str], use: str) -> None:
        const = const_for.get(_norm(name))
        if const is None and not category:
            return  # prize-table rows that aren't items (the Game Corner also trades Pokémon)
        if const is None:
            # Small spelling slips in the doc ("Banetite") resolve to the game's own spelling
            close = difflib.get_close_matches(_norm(name), list(const_for), n=1, cutoff=0.88)
            if close:
                const = const_for[close[0]]
                fixed = data.items.get(const, name)
                print(f"note: item {name!r} matched to the game's {fixed!r}", file=sys.stderr)
                name = fixed
        same = index.get(_norm(name))
        if same is None and const:
            same = next((k for k, it in enumerate(items) if it["key"] == const), None)
        if same is not None:  # the same item in several tables: merge what each adds
            item = items[same]
            item["where"] += [w for w in where if w not in item["where"]]
            item["category"] = item["category"] or category
            item["use"] = item["use"] or use
            return
        index[_norm(name)] = len(items)
        items.append({"name": name, "category": category, "where": list(where), "use": use, "key": const})

    for item in load_items():
        add(item["name"], item["category"], item["where"], item["use"])
    # Every TM and HM, named with its move, before shop lists add the bare "TM16" entries
    machine_where = load_machine_locations()
    for m in sorted(data.machines, key=lambda m: (m["kind"], m["num"])):
        if m["kind"] == "Tutor" or m["move"] not in data.moves:
            continue
        label = f"{m['kind']}{m['num']:02d}"
        loc = machine_where.get((m["kind"], m["num"]), {})
        const = f"ITEM_{label}"
        need = f"Needs {loc['requires']} to reach." if loc.get("requires") else ""
        name = f"{label} {data.moves[m['move']]['name']}"
        index[_norm(name)] = len(items)
        items.append({"name": name, "category": f"{m['kind']}s", "where": list(loc.get("where", [])), "use": need,
                      "key": const if const in data.item_ids else None, "move": m["move"]})
    for mart in marts(data.paths):
        for const in mart["items"]:
            if const in data.items:
                add(_full_item_name(data, const), "", [mart["where"]], "")
    for item in items:
        # "Daimyn City Mall" from the doc is redundant next to "Daimyn City Mall · Gems shop"
        places = {w.split(" · ")[0] for w in item["where"] if " · " in w}
        # …and "PokeChip Crusher" next to "PokeChip Crusher (5 chips)"
        item["where"] = [w for w in item["where"] if w not in places and not any(o.startswith(w + " (") for o in item["where"])]
        item["category"] = item["category"] or "Other items"
    for names in held.values():
        for h in names:
            add(h.split(" (")[0], "Held by wild Pokémon", [], "")
    for links in evo_links.values():
        for link in links:
            if link.get("item") and link["item"] in data.items and _norm(data.items[link["item"]]) not in index:
                add(data.items[link["item"]], "Evolution", [], "")

    by_const = {}
    for k, item in enumerate(items):
        if item["key"]:
            by_const.setdefault(item["key"], k)
            by_const.setdefault(item["key"], k)
    for const, name in data.items.items():  # the evolution table names items by constant; match through the name too
        if const not in by_const and _norm(name) in index:
            by_const[const] = index[_norm(name)]

    wanted = {i["key"]: data.item_ids[i["key"]] for i in items if i["key"]}
    sheet, offsets = pack(item_icons(data.paths.rom, wanted), 24)
    for item in items:
        item["icon"] = offsets.get(item.pop("key"))
    return items, index, by_const, "data:image/webp;base64," + base64.b64encode(sheet).decode()


def _full_item_name(data: SourceData, const: str) -> str:
    """The ROM caps names at 12 characters ("BlundrPolicy"); the constant spells them out (Blunder Policy)."""
    rom_name = data.items[const]
    spelled = const.removeprefix("ITEM_").replace("_", " ").title()
    short, full = _norm(rom_name), _norm(spelled)
    letters = iter(full)
    abbreviated = len(rom_name) >= 11 and short != full and all(c in letters for c in short)
    return spelled if abbreviated else rom_name  # a renamed item (Link Stone → Linking Cord) keeps its game name


def _abilities(mons: list[dict], officials: dict[str, str]) -> list[dict]:
    """Every ability as players see it, with the Pokémon that can have it ([index, 1 if hidden]).
    Names are per species, so CFRU's renames (Protean shown as Libero on Cinderace) are separate entries."""
    by_name: dict[str, dict] = {}
    for i, m in enumerate(mons):
        for (name, desc, chance), hidden in [(a, 0) for a in m["abilities"]] + ([(m["hidden"], 1)] if m["hidden"] else []):
            entry = by_name.setdefault(name, {"name": name, "official": officials.get(name), "desc": desc, "chance": chance, "mons": []})
            entry["desc"] = entry["desc"] or desc
            entry["mons"].append([i, hidden])
    return sorted(by_name.values(), key=lambda a: a["name"])


def _attach_ability_details(paths: Paths, abilities: list[dict], moves: dict, details: dict | None = None) -> None:
    """The Abilities tab's longer explanation of each ability (ability_details.json, keyed by the name shown), plus
    the moves it affects, taken from the CFRU move tables the entry names (gPunchingMoves for Iron Fist...)."""
    details = details if details is not None else json.loads(ABILITY_DETAILS.read_text(encoding="utf-8"))
    names = {a["name"] for a in abilities}
    missing, unknown = sorted(names - set(details)), sorted(set(details) - names)
    if missing or unknown:
        raise ValueError(f"{ABILITY_DETAILS.name} is out of step with the page: missing {missing}, not on the page {unknown}")
    tables = json.loads((paths.cfru / "assembly/data/move_tables.json").read_text(encoding="utf-8"))
    for a in abilities:
        entry = details[a["name"]]
        a["detail"] = entry["text"]
        a["moves"] = list(dict.fromkeys(m for t in entry.get("moves", []) for m in tables[t] if m in moves))


def _docs(ability_names: set[str] = frozenset()) -> list[dict]:
    """Feature-list topics rendered to HTML, with their images embedded so the page stays one offline file."""
    images = {p.name: "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()
              for p in DOC_IMAGES.glob("*.png")} if DOC_IMAGES.exists() else {}
    return [{"title": g["title"], "topics": [{"title": t["title"], "html": render_topic(t, images, ability_names),
                                              "s": _norm(t["title"] + " " + topic_text(t))} for t in g["topics"]]}
            for g in load_docs()]


def _attach_tutor_locations(moves: dict) -> list[dict]:
    """Where each tutor move is taught, from the feature list's tutor tables. A row like "Fire Fang, or Flame Burst
    (v1.4+)" names two versions; keep the one the game teaches (a move tutor file or a CFRU special tutor)."""
    by_key = {}
    for const, m in moves.items():
        for key in m["s"]:
            by_key.setdefault(key, const)
    taught = {kind: {k for k, m in moves.items() if any(h.startswith(prefix) for _, h in m["learners"])}
              for kind, prefix in (("Regular", "Tutor"), ("Special", "Special:"))}

    rows = []
    for t in load_tutors():
        # The page describes the latest release: "Fire Fang, or Flame Burst (v1.4+)" means Flame Burst
        raw = re.split(r",\s*or\s+", t["move"])
        raw = [o for o in raw if re.search(r"\(v[\d.]+\+?\)", o)] or raw
        options = [re.sub(r"\s*\([^)]*\)", "", o).strip() for o in raw]
        found = []
        for o in options:
            const = by_key.get(_norm(o))
            if const is None:  # doc slips like "Breaking Strike" / "Automize" resolve to the nearest move name
                close = difflib.get_close_matches(_norm(o), list(by_key), n=1, cutoff=0.8)
                const = by_key[close[0]] if close else None
                if const:
                    print(f"note: tutor move {o!r} matched to {moves[const]['name']!r}", file=sys.stderr)
            found.append(const)
        found = [c for c in found if c]
        const = next((c for c in found if c in taught.get(t["kind"], ())), found[0] if found else None)
        if const is None:
            print(f"warning: tutor move {t['move']!r} matches no move", file=sys.stderr)
            continue
        where = re.sub(r"\s*\(v[\d.]+\+?\)", "", t["where"])  # "Battle Frontier (v1.4)": everything is current
        if t["kind"] == "Special":
            where = re.sub(r"\s*\(\d+\)$", "", where)  # "Gym Trainee Mason (1..3)" teach one of three each day
        entry = {"where": where, "note": t["note"], "kind": t["kind"]}
        moves[const].setdefault("tutor", []).append(entry)
        rows.append({"move": const, **entry})
    return rows


def _attach_machine_locations(data: SourceData, moves: dict) -> None:
    where = load_machine_locations()
    for m in data.machines:
        if m["kind"] != "Tutor" and m["move"] in moves:  # "TM02", "tm2" and "HM01" all find the move
            for key in (f"{m['kind']}{m['num']:02d}", f"{m['kind']}{m['num']}"):
                if key.lower() not in moves[m["move"]]["s"]:
                    moves[m["move"]]["s"].append(key.lower())
    for m in data.machines:
        loc = where.get((m["kind"], m["num"]))
        if loc and m["kind"] != "Tutor" and m["move"] in moves:
            moves[m["move"]]["tm"] = {"label": f"{m['kind']}{m['num']:02d}", "where": loc["where"], "requires": loc["requires"]}


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
    "name": "Pokemon Amethyst Companion",
    "short_name": "Amethyst",
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


CHANGELOG = DPE_ROOT.parent / "PokemonShootingStars" / "Changelog.txt"


def game_version() -> str:
    """The newest release in the game's changelog (shown beside the title so players know what the page matches)."""
    if not CHANGELOG.exists():
        return ""
    m = re.search(r"^v(\d+(?:\.\d+)+)\s+-", CHANGELOG.read_text(encoding="utf-8", errors="replace"), flags=re.M)
    return f"v{m.group(1)}" if m else ""


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
            .replace("__BRAND_ICON__", _brand_icon())
            .replace("__GAME_VERSION__", game_version())
            .replace("__APP_SCRIPT__", APP_SCRIPT.read_text(encoding="utf-8").replace("</", "<\/")))
