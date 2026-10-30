"""Turns the roster into the page: one JSON blob + sprite sheet embedded in template.html."""

import base64
import graphlib
import hashlib
import io
import json
import re
import sys
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw

from .docs import DOC_IMAGES, load_docs, render_topic, topic_text
from .field_items import field_items
from .items import load_items, load_machine_locations, load_script_items, load_tutors
import difflib

from .load_cfru import ability_chances, ability_display, ability_ids, ability_officials, marts, z_crystal_sources
from .locations import attach_encounters, load_encounters
from .paths import DPE_ROOT, Paths
from .roster import Entry, SourceData, build_roster, evolution_links, load_extra_forms, load_source_data
from .rom import POCKET_BERRIES, POCKET_KEY_ITEMS, POCKET_POKE_BALLS, item_fields, item_icons
from .sprites import build_sheet, pack
from .town_map import norm as place_key, place_descriptions, town_map_png, town_map_squares
from .trainers import NATURES, load_trainers

TEMPLATE = Path(__file__).with_name("template.html")
SW_TEMPLATE = Path(__file__).with_name("sw.js")
APP_SCRIPT = Path(__file__).with_name("app.js")  # the page's script, inlined so the page stays one file
ABILITY_DETAILS = Path(__file__).with_name("ability_details.json")  # hand-written, checked against CFRU's code
STAT_KEYS = ("hp", "atk", "def", "spa", "spd", "spe")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _words(s: str) -> str:
    """Lower-case ASCII words separated by single spaces, for searching prose without matching across words."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s.lower()).split())


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
    # Modes where it has no dex number but turns up in swarms; the page tags these "Swarm"
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
    by_key = {e.key: e for e in roster}
    form_rows = [{"name": by_key[x["species"]].name, "form": by_key[x["species"]].form, "mode": x["mode"], "method": x["method"],
                  "location": x["location"], "sub": x["sub"], "rate": "", "levels": "", "item": "", "notes": x["notes"]}
                 for x in load_extra_forms() if x["method"] and x["species"] in by_key]  # e.g. Rotom's appliance forms
    locations, held, unmatched = attach_encounters(load_encounters() + form_rows, roster)
    items, item_index, item_by_const, icon_sheet = _items(data, held, evo_links)
    _attach_machine_locations(data, moves)
    tutors = _attach_tutor_locations(moves)
    mons = [_mon(data, e, index, evo_links.get(e.key, []), locations.get(e.key, []), held.get(e.key, []),
                 item_index, item_by_const) for e in roster]
    for m, shared in zip(mons, _shared_dex_numbers(roster)):
        m["sharedDex"] = shared
    abilities = _abilities(mons, ability_officials(data.paths))
    _attach_ability_details(data.paths, abilities, moves)
    trainers, teams, trainer_sheet = _trainers(data, index, item_by_const)
    return {
        "docs": _docs({a["name"] for a in abilities}),
        "abilities": abilities,
        "tutors": tutors,
        "mons": mons,
        "items": items,
        "itemSheet": icon_sheet,
        "moves": moves,
        "trainers": trainers,
        "teams": teams,
        "trainerSheet": trainer_sheet,
        "townMap": {"img": _smallest_image(town_map_png()), "places": town_map_squares(data.paths), "about": place_descriptions()},
        "unmatchedEncounters": unmatched,
    }


TEAM_KEYS = ("std", "hard", "div", "hdiv")


def _trainers(data: SourceData, index: dict, item_by_const: dict) -> tuple[list[dict], dict, str]:
    """Trainers with a team per table (Standard, Hard, Divergent, Hard Divergent), and their battle sprites.
    A team member is [Pokémon, level, item (index, or name when the Items tab doesn't list it), ability no., move nos.,
    Hard-mode nature no., the two stats Very Hard maxes (in STAT_KEYS order), 1 if the table sets its moves]."""
    def mon_index(species: str) -> int:
        key = species
        while key not in index and "_" in key.removeprefix("SPECIES_"):
            key = key.rsplit("_", 1)[0]  # a form the page doesn't list on its own falls back to its species
        if key not in index:
            raise ValueError(f"trainer Pokémon {species} matches no Pokémon on the page")
        return index[key]

    def ability_name(const: str, species: str) -> str:
        s = data.stats[species]
        return ability_display(data.paths, const, species, data.national.get(species), s["types"])[0]

    def item(const: str | None):
        if const is None:
            return None
        return item_by_const.get(const, _full_item_name(data, const) if const in data.items else const)

    raw, raw_teams, pics = load_trainers(data.paths, data.stats, data.levelup, data.moves, ability_name)
    # Moves and abilities are numbered (DEX.teamMoves / DEX.teamAbilities): written out, they'd double the size
    move_list = sorted({k for team in raw_teams for m in team for k in m["moves"] if k in data.moves})
    ability_list = sorted({m["ability"] for team in raw_teams for m in team})
    move_no, ability_no = {k: n for n, k in enumerate(move_list)}, {a: n for n, a in enumerate(ability_list)}
    teams = [[[mon_index(m["species"]), m["level"], item(m["item"]), ability_no[m["ability"]],
               [move_no[k] for k in m["moves"] if k in move_no], NATURES.index(m["nature"]),
               [STAT_KEYS.index(s) for s in m["evs"]], int(m["custom"])] for m in team] for team in raw_teams]
    sheet, offsets = pack(pics, 64)
    trainers = []
    for t in raw:
        trainers.append({
            "cls": t["cls"], "name": t["name"], "rival": t["rival"], "pic": offsets.get(t["pic"]),
            "place": t["place"], "note": t["note"], "double": t["double"], "scaled": t["scaled"],
            "items": [item(i) for i in t["items"]], "ball": item(t["ball"]), "iv": t["iv"], "teams": [t["teams"][k] for k in TEAM_KEYS],
        })
    return trainers, {"list": teams, "moves": move_list, "abilities": ability_list, "natures": NATURES}, \
        "data:image/webp;base64," + base64.b64encode(sheet).decode()


def _shared_dex_numbers(roster: list[Entry]) -> list[dict[str, int]]:
    """For entries without their own number in a dex, the number they share (the game's Pokédex lists alternate
    forms under their base species, gAlternateDexEntries): their base form's, else a same-named entry's (Kanto
    Farfetch'd shares Galarian Farfetch'd's #063). Empty where an entry has its own number or no relative has one."""
    by_key = {e.key: e for e in roster}
    by_name: dict[str, dict[str, int]] = {}
    for e in roster:
        for field, n in e.dex.items():
            by_name.setdefault(e.name, {}).setdefault(field, n)
    result = []
    for e in roster:
        base = by_key.get(e.base)
        shared = {}
        for field, mode in (("std", "Standard"), ("div", "Divergent")):
            if e.dex.get(field) or mode not in e.modes:
                continue
            n = (base.dex.get(field) if base and base is not e else None) or by_name.get(e.name, {}).get(field)
            if n:
                shared[field] = n
        result.append(shared)
    return result


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
        index[_norm(label)] = len(items)  # shops sell "TM16" under CFRU's ITEM_TM16_ROAR as well as ITEM_TM16
        items.append({"name": name, "category": f"{m['kind']}s", "where": list(loc.get("where", [])), "use": need,
                      "key": const if const in data.item_ids else None, "move": m["move"]})
    for mart in marts(data.paths):
        for const in mart["items"]:
            if const in data.items:
                add(_full_item_name(data, const), "", [mart["where"]], "")
    for const, where in z_crystal_sources(data.paths).items():  # Gym Trainee rewards and wild-held Z-Crystals
        if const in data.items:
            add(_full_item_name(data, const), "Z-Crystals", where, "")
    for extra in load_script_items():  # sources the feature list doesn't cover (apricorn balls, Memories, relics…)
        if extra["const"] not in data.items:
            raise ValueError(f"script_items.csv: unknown item {extra['const']}")
        add(_full_item_name(data, extra["const"]), extra["category"], extra["where"], "")
    for const, places in field_items(data.paths).items():  # item balls and hidden items, read from the ROM's maps
        if const not in data.items:
            continue
        name = _full_item_name(data, const)
        k = index.get(_norm(name), index.get(_norm(data.items[const])))
        if k is None:
            k = next((j for j, it in enumerate(items) if it["key"] == const), None)
        known = " ".join(items[k]["where"]).lower() if k is not None else ""
        # a map the doc already names for this item ("Route 9 (Requires Surf)") isn't repeated as plain "Route 9"
        new = [pl for pl in places if pl.split(" (")[0].lower() not in known]
        if new:
            add(items[k]["name"] if k is not None else name, "", new, "")
    fields = item_fields(data.paths.rom, data.item_ids)
    for item in items:
        item["category"] = _item_category(item, fields)
    for item in items:
        # The Refiner is the one place to get a Mega Stone; the shop rows from the ROM just repeat it
        if item["category"] == "Mega Stones":
            refiner = [w for w in item["where"] if w.startswith("Bought from Mega Stone Refiner")]
            if refiner:
                item["where"] = refiner[:1]
    for item in items:
        # Poké Mart stock only grows with badges: "after 6 badges" covers 7 and 8 (plain "Poké Marts" covers all)
        stock = [w for w in item["where"] if re.fullmatch(r"Poké Marts( \(after \d+ badges?\))?", w)]
        if len(stock) > 1:
            first = min(stock, key=lambda w: int(re.sub(r"\D", "", w) or 0))
            item["where"] = [w for w in item["where"] if w not in stock or w == first]
        item["where"] = _tidy_where(item["where"])
        # "PokeChip Crusher" is redundant next to "PokeChip Crusher (5 chips)"
        item["where"] = [w for w in item["where"] if not any(o.startswith(w + " (") for o in item["where"])]
    for names in held.values():
        for h in names:
            add(h.split(" (")[0], "Held by wild Pokémon", [], "")
    for links in evo_links.values():
        for link in links:
            if link.get("item") and link["item"] in data.items and _norm(data.items[link["item"]]) not in index:
                add(data.items[link["item"]], "Evolution", [], "")

    items.sort(key=lambda it: ITEM_CATEGORY_ORDER.index(it["category"]) if it["category"] in ITEM_CATEGORY_ORDER else len(ITEM_CATEGORY_ORDER) - 1)
    index.clear()
    index.update((_norm(it["name"]), k) for k, it in enumerate(items))
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


ITEM_CATEGORY_ORDER = ["Poké Balls", "Consumables", "Held Items", "Berries", "Breeding", "Evolution", "Mega Stones", "Z-Crystals",
                       "Primal Reversion", "Forme Changing Items", "Key Items", "HMs", "TMs", "Held by wild Pokémon", "Other items"]


def _item_category(item: dict, fields: dict[str, dict]) -> str:
    """Z-Crystals and Poké Balls always get their own group; otherwise the doc's category, else what the game's item
    table says: Key Items pocket, an evolution-stone use (sweets, apples), a field or battle use, a hold effect."""
    key, f = item["key"], fields.get(item["key"])
    if key and key.endswith("IUM_Z"):
        return "Z-Crystals"
    if f and f["pocket"] == POCKET_POKE_BALLS:
        return "Poké Balls"
    if item["category"] or not f:
        return item["category"] or "Other items"
    evolve, unusable = fields["ITEM_FIRE_STONE"]["field_use"], fields["ITEM_LEFTOVERS"]["field_use"]
    if f["pocket"] == POCKET_KEY_ITEMS:
        return "Key Items"
    if f["pocket"] == POCKET_BERRIES:
        return "Berries"
    if f["field_use"] == evolve:
        return "Evolution"
    if f["battle_use"] or f["field_use"] not in (0, unusable):
        return "Consumables"
    return "Held Items" if f["hold"] else "Other items"


def _full_item_name(data: SourceData, const: str) -> str:
    """The ROM caps names at 12 characters ("BlundrPolicy"); the constant spells them out (Blunder Policy)."""
    rom_name = data.items[const]
    spelled = const.removeprefix("ITEM_").replace("_", " ").title()
    short, full = _norm(rom_name), _norm(spelled)
    letters = iter(full)
    abbreviated = len(rom_name) >= 11 and short != full and all(c in letters for c in short)
    # …or cut word by word to fit a narrow menu ("Bug Mem" for ITEM_BUG_MEMORY)
    rom_words, full_words = rom_name.lower().split(), spelled.lower().split()
    clipped = len(rom_words) == len(full_words) and short != full and all(f.startswith(w) for w, f in zip(rom_words, full_words))
    return spelled if abbreviated or clipped else rom_name  # a renamed item (Link Stone → Linking Cord) keeps its game name


MODE_NOTE = re.compile(r"\((Standard|Divergent) (?:Pokemon encounters|Mode) only\)", re.I)


def _tidy_where(where: list[str]) -> list[str]:
    """An item's places, with the feature list's lines said once next to the ROM's shop lines ("<place> · <shop>"):
    version notes go (the page describes the latest release); a doc place a shop line covers goes ("Tsarvosa City
    Market" or "Daimyn City Mall Incense Shop" next to "<that place> · ... shop"); and a mode note line ("(Divergent
    Pokemon encounters only)") becomes a "(Divergent)" tag on the doc lines before it that have none."""
    where = [re.sub(r"\s*\((?:Added in )?v[\d.]+\+?\)", "", re.sub(r", added in v[\d.]+", "", w, flags=re.I), flags=re.I)
             for w in where]
    shops = [(_norm(w.split(" · ")[0]), _norm(re.sub(r"\s*\((?:Standard|Divergent)\)$", "", w.split(" · ", 1)[1])))
             for w in where if " · " in w]

    marts = any(w.startswith("Poké Marts") for w in where)  # the ROM's stock, with the badges it needs

    def covered(piece: str) -> bool:
        p = _norm(piece)
        if piece.startswith("Poké Marts"):
            return False
        if marts and p in ("pokemart", "pokemarts"):  # the doc's "Pokemarts" / "PokeMarts"
            return True
        return any(p.startswith(place) and (p[len(place):] in ("", "market", "mall") or name.startswith(p[len(place):]))
                   for place, name in shops)

    out: list[str] = []
    for w in where:
        note = MODE_NOTE.fullmatch(w)
        if note:
            tag = f" ({note.group(1).title()})"
            out = [o if " · " in o or o.endswith(("(Standard)", "(Divergent)")) else o + tag for o in out]
        elif " · " in w:
            out.append(w)
        elif w:
            kept = ", ".join(piece for piece in re.split(r",\s*(?![^()]*\))", w) if not covered(piece))  # "Route 7, Tsarvosa City Market"
            if kept:
                out.append(kept)
    return list(dict.fromkeys(out))


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


def _smallest_image(source: Path | bytes) -> str:
    """A PNG (file or bytes) as a data URL, re-encoded as lossless WebP when that's smaller (Braille Puzzles: 186 KB → 39 KB)."""
    png = source if isinstance(source, bytes) else source.read_bytes()
    out = io.BytesIO()
    Image.open(io.BytesIO(png)).save(out, "WEBP", lossless=True, exact=True, method=6)
    kind, data = min(("png", png), ("webp", out.getvalue()), key=lambda x: len(x[1]))
    return f"data:image/{kind};base64," + base64.b64encode(data).decode()


def _docs(ability_names: set[str] = frozenset()) -> list[dict]:
    """Feature-list topics rendered to HTML, with their images embedded so the page stays one offline file."""
    images = {p.name: _smallest_image(p) for p in DOC_IMAGES.glob("*.png")} if DOC_IMAGES.exists() else {}
    return [{"title": g["title"], "topics": [{"title": t["title"], "html": render_topic(t, images, ability_names),
                                              "s": _words(t["title"] + " " + topic_text(t))} for t in g["topics"]]}
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


NOT_ON_TOWN_MAP = {"Roaming", "Ultra Space"}


def build(paths: Paths, out: Path) -> None:
    data = load_source_data(paths)
    roster = build_roster(data)
    links = evolution_links(data, {e.key for e in roster})
    sheet, offsets = build_sheet({e.key: data.sprites[e.key] for e in roster})
    page = page_data(data, roster, links)
    for name in page["unmatchedEncounters"]:
        print(f"warning: encounters.csv row for {name!r} matches no Pokémon on the page", file=sys.stderr)
    on_map = {place_key(p) for p in page["townMap"]["places"]}
    for place in sorted({l["location"] for m in page["mons"] for l in m["loc"]} - NOT_ON_TOWN_MAP):
        if place_key(place) not in on_map:
            print(f"warning: {place!r} has no spot on the Town Map (town_map.SPOTS)", file=sys.stderr)
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


CAT_ICON_DIR = Path(__file__).with_name("cat_icons")  # the games' Physical / Special / Status move labels (Bulbapedia archives)


def _cat_icons() -> str:
    return json.dumps({p.stem: "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode() for p in sorted(CAT_ICON_DIR.glob("*.png"))})


def _brand_icon() -> str:
    return "data:image/png;base64," + base64.b64encode(BRAND_ICON.read_bytes()).decode()


def _pack_learners(learners: list) -> dict[str, list[int]]:
    """[[mon, how], ...] as {how: [mon, ...]}: "TM10" or "Special: Water types" is written once per move, not once per
    Pokémon (865 KB → 294 KB). app.js unpacks it by listing each group and sorting by mon (a stable sort), so the
    groups go in an order that keeps each Pokémon's own ways in sequence (Meowth: Lv 12, then Special); the build
    stops if the packing doesn't give back the same list."""
    order = graphlib.TopologicalSorter()
    for (i, a), (j, b) in zip([[None, None]] + learners, learners):
        order.add(b, *([a] if i == j and a != b else []))
    packed: dict[str, list[int]] = {how: [] for how in order.static_order()}
    for i, how in learners:
        packed[how].append(i)
    unpacked = sorted(([i, how] for how, ids in packed.items() for i in ids), key=lambda x: x[0])
    if unpacked != learners:
        raise ValueError(f"learner list doesn't survive packing: {learners[:5]}...")
    return packed


def _pack_ability(ability: list | None, index: dict[tuple, int]) -> list | int | None:
    """A Pokémon's [name, description, chance] as its index in DEX.abilities when that entry has the same text,
    so each description is written once (app.js swaps the index back). Anything that differs is left as it is."""
    return index.get(tuple(ability), ability) if ability else ability


def render(data: dict, sheet: bytes, offsets: dict) -> str:
    index = {(a["name"], a["desc"], a["chance"]): n for n, a in enumerate(data["abilities"])}
    data = dict(data, mons=[dict(m, sp=offsets[m["key"]], abilities=[_pack_ability(a, index) for a in m["abilities"]],
                                 hidden=_pack_ability(m["hidden"], index)) for m in data["mons"]],
                moves={k: dict(m, learners=_pack_learners(m["learners"])) for k, m in data["moves"].items()})
    # Keys keep the move table compact and stable; the page only needs them as ids.
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    sprites = "data:image/webp;base64," + base64.b64encode(sheet).decode()
    return (TEMPLATE.read_text(encoding="utf-8")
            .replace("__DEX_DATA__", blob)
            .replace("__SPRITE_SHEET__", sprites)
            .replace("__BRAND_ICON__", _brand_icon())
            .replace("__CAT_ICONS__", _cat_icons())
            .replace("__GAME_VERSION__", game_version())
            .replace("__APP_SCRIPT__", APP_SCRIPT.read_text(encoding="utf-8").replace("</", "<\/")))
