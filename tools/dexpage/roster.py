"""Decides which Pokémon get a row, their Mode, their move lists, and their evolution text."""

import re
from dataclasses import dataclass, field
from functools import cache

from . import load_cfru, load_dpe
from .cparse import read, resolve_conditionals, strip_comments
from .paths import Paths
from .rom import item_names

STANDARD, DIVERGENT = "Standard", "Divergent"

# Constant-name suffix → form label. Unlisted suffixes are title-cased.
FORM_LABELS = {
    "A": "Alolan", "G": "Galarian", "H": "Hisuian",
    "MEGA": "Mega", "MEGA_X": "Mega X", "MEGA_Y": "Mega Y",
    "GIGA": "Mega G",  # Gigantamax forms are Mega-style evolutions in this game
    "PRIMAL": "Primal", "N": "Midnight", "DUSK": "Dusk",
    "Y": "Pom-Pom", "P": "Pa'u", "S": "Sensu",
}

DROPPED_METHODS = {"EVO_TRADE", "EVO_TRADE_ITEM", "EVO_GIGANTAMAX"}  # impossible in game
AMPED_NATURES = "Hardy, Brave, Adamant, Naughty, Docile, Impish, Lax, Hasty, Jolly, Naive, Rash, Sassy, Quirky"


@dataclass
class SourceData:
    paths: Paths
    ids: dict
    std: list
    div: list
    habitat: dict
    stats: dict
    levelup: dict
    egg: dict
    machines: list
    evolutions: dict
    names: dict
    sprites: dict
    national: dict
    moves: dict
    items: dict
    abilities: dict


@dataclass
class Entry:
    key: str
    name: str
    form: str | None
    modes: list
    dex: dict
    base: str
    stats: dict
    moves: dict = field(default_factory=dict)
    family: str = ""
    battle_form: bool = False  # Mega/Primal/Ultra: exists only in battle, moves are its base's


def _national_dex(p: Paths) -> dict[str, str]:
    text = load_dpe._source(p, "src/Species_To_Pokdex_Table.c")
    return dict(re.findall(r"\[\s*(SPECIES_\w+)\s*-\s*1\s*\]\s*=\s*(NATIONAL_DEX_\w+)", text))


def load_source_data(p: Paths) -> SourceData:
    std, div = load_dpe.dex_lists(p)
    return SourceData(
        paths=p, ids=load_dpe.species_ids(p), std=std, div=div,
        habitat=load_dpe.habitat_forms(p), stats=load_dpe.base_stats(p),
        levelup=load_dpe.levelup(p), egg=load_dpe.egg_moves(p),
        machines=load_dpe.machine_compat(p), evolutions=load_dpe.evolutions(p),
        names=load_dpe.species_names(p), sprites=load_dpe.front_pic(p),
        national=_national_dex(p), moves=load_cfru.moves(p),
        items=item_names(p.rom, load_cfru.item_ids(p)), abilities=load_cfru.ability_names(p),
    )


# ---------------------------------------------------------------- special tutors

@dataclass(frozen=True)
class TutorRule:
    move: str
    types: tuple
    national: tuple
    friendship: bool


@cache
def _special_tutor_source(p: Paths) -> tuple[frozenset, tuple]:
    """Parse CanMonLearnTutorMove's special section and GetExpandedTutorMove in CFRU src/item.c."""
    raw = strip_comments(read(p.cfru / "src/item.c"))
    begin = raw.index("bool8 CanMonLearnTutorMove(")
    end = raw.index("\n}", raw.index("u16 GetExpandedTutorMove(")) + 2
    text = resolve_conditionals(raw[begin:end], load_cfru.defines(p))
    start = text.index("species == SPECIES_EGG")  # start of the "can't learn any special tutor" blocklist
    block_end = text.index("return FALSE;", start)
    blocklist = frozenset(re.findall(r"SPECIES_\w+", text[start:block_end]))

    switch = text[text.index("switch (tutorId)", block_end):]
    switch = switch[:switch.index("u16 GetExpandedTutorMove")]
    move_for = dict(re.findall(r"case\s+(TUTOR_SPECIAL_\w+)\s*:\s*return\s+(MOVE_\w+)\s*;",
                               text[text.index("u16 GetExpandedTutorMove"):]))

    allowed = {"gBaseStats", "species", "type1", "type2", "dexNum", "GetMonData", "mon",
               "MON_DATA_FRIENDSHIP", "NULL", "MAX_FRIENDSHIP", "return"}
    rules = []
    for m in re.finditer(r"((?:case\s+TUTOR_SPECIAL_\w+\s*:\s*)+)(return\b[^;]*;)", switch):
        expr = m.group(2)
        for token in re.findall(r"\b[A-Za-z_]\w*\b", expr):
            if token not in allowed and not token.startswith(("TYPE_", "NATIONAL_DEX_")):
                raise ValueError(f"unsupported special-tutor rule: {expr!r}")
        types = tuple(sorted({t.removeprefix("TYPE_") for t in re.findall(r"TYPE_\w+", expr)}))
        national = tuple(dict.fromkeys(re.findall(r"NATIONAL_DEX_\w+", expr)))
        for case in re.findall(r"TUTOR_SPECIAL_\w+", m.group(1)):
            rules.append(TutorRule(move_for[case], types, national, "MAX_FRIENDSHIP" in expr))
    return blocklist, tuple(rules)


def _rule_note(rule: TutorRule) -> str:
    parts = [f"{t.title()} types" for t in rule.types]
    parts += [n.removeprefix("NATIONAL_DEX_").replace("_", " ").title() for n in rule.national]
    note = ", ".join(parts)
    return f"Max friendship, {note}" if rule.friendship else note


def special_tutor_moves(species: str, types: list[str], national: str | None,
                        paths: Paths | None = None) -> list[tuple[str, str]]:
    """(MOVE_*, note) for every CFRU special tutor this species can use."""
    blocklist, rules = _special_tutor_source(paths or Paths.default())
    if species in blocklist:
        return []
    return [(r.move, _rule_note(r)) for r in rules
            if set(types) & set(r.types) or (national and national in r.national)]


# ---------------------------------------------------------------- forms

def _split_form(key: str, ids: dict) -> tuple[str, str | None]:
    """(base species, form label) using the longest SPECIES_* prefix that is itself a species."""
    parts = key.split("_")
    for cut in range(len(parts) - 1, 1, -1):
        base = "_".join(parts[:cut])
        if base in ids:
            suffix = "_".join(parts[cut:])
            return base, FORM_LABELS.get(suffix, suffix.replace("_", " ").title())
    return key, None


def _mega_links(data: SourceData, source: str) -> list[tuple]:
    return [e for e in data.evolutions.get(source, [])
            if e[0] == "EVO_MEGA" and e[1] not in ("ITEM_NONE", "MOVE_NONE", "0")]


def _machine_moves(data: SourceData, key: str) -> tuple[list, list]:
    tm, tutor = [], []
    for m in data.machines:
        if key in m["species"]:
            if m["kind"] == "Tutor":
                tutor.append((f"Tutor {m['num']}", m["move"]))
            else:
                tm.append((f"{m['kind']}{m['num']:02d}", m["move"]))
    tm.sort(key=lambda x: (x[0][:2] == "HM", x[0]))
    return tm, tutor


def _moves_for(data: SourceData, key: str, base: str, family_root: str) -> dict:
    tm, tutor = _machine_moves(data, key)
    stats = data.stats.get(key) or data.stats[base]
    national = data.national.get(key) or data.national.get(base)
    egg = data.egg.get(key) or data.egg.get(family_root, [])
    return {
        "level": list(data.levelup.get(key) or data.levelup.get(base, [])),
        "egg": list(egg),
        "tm": tm,
        "tutor": tutor,
        "special": special_tutor_moves(key, stats["types"], national, data.paths),
    }


def all_moves(entry: Entry) -> set[str]:
    found = set()
    for moves in entry.moves.values():
        for item in moves:
            parts = item if isinstance(item, tuple) else (item,)
            found.update(p for p in parts if isinstance(p, str) and p.startswith("MOVE_"))
    return found


def _family_roots(data: SourceData) -> dict[str, str]:
    parent = {}
    for src, entries in data.evolutions.items():
        for method, _, target, _ in entries:
            if method not in DROPPED_METHODS and method != "EVO_MEGA":
                parent.setdefault(target, src)
    roots = {}
    for key in data.ids:
        node, seen = key, set()
        while node in parent and node not in seen:
            seen.add(node)
            node = parent[node]
        roots[key] = node
    return roots


def build_roster(data: SourceData) -> list[Entry]:
    roots = _family_roots(data)
    modes: dict[str, set] = {}
    for s in data.std:
        modes.setdefault(s, set()).add(STANDARD)
    for s in data.div:
        modes.setdefault(s, set()).add(DIVERGENT)
    dex_species = set(modes)

    bases: dict[str, tuple[str, str | None]] = {}
    for key, kinds in data.habitat.items():
        if key in dex_species:
            continue
        base, form = _split_form(key, data.ids)
        bases[key] = (base, form)
        modes[key] = {STANDARD if k == "standard" else DIVERGENT for k in kinds} | modes.get(base, set())

    for source in list(modes):
        for _, _, target, _ in _mega_links(data, source):
            if target not in modes:
                bases[target] = (source, _split_form(target, data.ids)[1])
                modes[target] = set(modes[source])

    entries: dict[str, Entry] = {}
    for key, mode_set in modes.items():
        if key not in data.stats:
            continue
        base, form = bases.get(key, (key, None))
        root = roots.get(base, base)
        is_mega = key in bases and any(t == key for *_, t, _ in _mega_links(data, base))
        entry = Entry(
            key=key, name=data.names.get(key, key), form=form,
            modes=[m for m in (STANDARD, DIVERGENT) if m in mode_set],
            dex={k: v for k, v in (("std", _index(data.std, key)), ("div", _index(data.div, key))) if v},
            base=base, stats=data.stats[key], family=roots.get(key, root), battle_form=is_mega,
        )
        # Megas only exist in battle: they learn exactly what their base learns
        entry.moves = (_moves_for(data, base, base, root) if is_mega
                       else _moves_for(data, key, base, root))
        entries[key] = entry

    for key, (base, _) in bases.items():
        if key in entries and base in entries and base != key and _identical(data, entries[key], entries[base]):
            del entries[key]

    return _ordered(data, entries, bases, roots)


def _index(lst: list, key: str) -> int | None:
    return lst.index(key) + 1 if key in lst else None


def _identical(data: SourceData, a: Entry, b: Entry) -> bool:
    def sprite(k):
        path = data.sprites.get(k)
        return path.read_bytes() if path and path.exists() else None
    return (a.stats == b.stats and a.moves == b.moves and sprite(a.key) == sprite(b.key))


def _ordered(data: SourceData, entries: dict, bases: dict, roots: dict) -> list[Entry]:
    order = [k for k in data.std if k in entries] + [k for k in data.div if k in entries and k not in data.std]
    placed = set(order)
    pre_evo = {}
    for src, evos in data.evolutions.items():
        for method, _, target, _ in evos:
            if method not in DROPPED_METHODS:
                pre_evo.setdefault(target, src)
    for key in entries:
        if key in placed:
            continue
        anchor = bases.get(key, (None,))[0]
        if anchor not in placed or anchor == key:
            anchor = pre_evo.get(key)
        if anchor in placed:
            # after the anchor and any forms already placed after it
            i = order.index(anchor) + 1
            while i < len(order) and bases.get(order[i], (None,))[0] == anchor:
                i += 1
            order.insert(i, key)
        else:
            order.append(key)
        placed.add(key)
    return [entries[k] for k in order]


# ---------------------------------------------------------------- evolution text

def _hour(h: int) -> str:
    return f"{(h % 12) or 12} {'AM' if h < 12 else 'PM'}"


def _pretty_const(value: str, prefix: str) -> str:
    words = value.removeprefix(prefix).split("_")
    out = []
    for w in words:
        m = re.fullmatch(r"([A-Z]+)(\d+)", w)
        out.append(f"{m.group(1).title()} {m.group(2)}" if m else w.title())
    return " ".join(out)


def evolution_text(data: SourceData, method: str, param: str, target: str, extra: str) -> str | None:
    item = lambda c: data.items.get(c) or _pretty_const(c, "ITEM_")
    move = lambda c: data.moves[c]["name"] if c in data.moves else _pretty_const(c, "MOVE_")
    type_ = lambda c: c.removeprefix("TYPE_").title()
    gender = {"MON_MALE": " (male)", "MON_FEMALE": " (female)"}.get(extra, "")
    lv = f"Lv. {param}"
    texts = {
        "EVO_LEVEL": lambda: lv,
        "EVO_LEVEL_NINJASK": lambda: lv,
        "EVO_LEVEL_SHEDINJA": lambda: f"{lv}, with an empty party slot and a Poké Ball in the bag",
        "EVO_LEVEL_DAY": lambda: f"{lv}, daytime",
        "EVO_LEVEL_NIGHT": lambda: f"{lv}, nighttime",
        "EVO_LEVEL_ATK_GT_DEF": lambda: f"{lv}, Attack > Defense",
        "EVO_LEVEL_ATK_EQ_DEF": lambda: f"{lv}, Attack = Defense",
        "EVO_LEVEL_ATK_LT_DEF": lambda: f"{lv}, Attack < Defense",
        "EVO_LEVEL_SILCOON": lambda: f"{lv} (personality-based, 50%)",
        "EVO_LEVEL_CASCOON": lambda: f"{lv} (personality-based, 50%)",
        "EVO_MALE_LEVEL": lambda: f"{lv}, male",
        "EVO_FEMALE_LEVEL": lambda: f"{lv}, female",
        "EVO_LEVEL_HOLD_ITEM": lambda: f"{lv} holding {item(extra)}",
        "EVO_LEVEL_SPECIFIC_TIME_RANGE": lambda: f"{lv}, {_time_range(extra)}",
        "EVO_RAINY_FOGGY_OW": lambda: f"{lv} in rain or fog",
        "EVO_TYPE_IN_PARTY": lambda: f"{lv} with a {type_(extra)}-type Pokémon in the party",
        "EVO_NATURE_HIGH": lambda: f"{lv}, nature {AMPED_NATURES}",
        "EVO_NATURE_LOW": lambda: f"{lv}, any other nature",
        "EVO_FRIENDSHIP": lambda: "Level up with high friendship",
        "EVO_FRIENDSHIP_DAY": lambda: "Level up with high friendship, daytime",
        "EVO_FRIENDSHIP_NIGHT": lambda: "Level up with high friendship, nighttime",
        "EVO_ITEM": lambda: f"Use {item(param)}{gender}",
        "EVO_ITEM_NIGHT": lambda: f"Use {item(param)} at night",
        "EVO_ITEM_HOLD_ITEM": lambda: f"Use {item(param)} while holding {item(extra)}",
        "EVO_ITEM_LOCATION": lambda: f"Use {item(param)} while standing on {_pretty_const(extra, 'MB_').lower()}",
        "EVO_HOLD_ITEM_DAY": lambda: f"Level up holding {item(param)}, daytime",
        "EVO_HOLD_ITEM_NIGHT": lambda: f"Level up holding {item(param)}, nighttime",
        "EVO_MAP": lambda: f"Level up at {_pretty_const(param, 'MAPSEC_')}",
        "EVO_MOVE": lambda: f"Level up knowing {move(param)}",
        "EVO_MOVE_MALE": lambda: f"Level up knowing {move(param)}, male",
        "EVO_MOVE_FEMALE": lambda: f"Level up knowing {move(param)}, female",
        "EVO_MOVE_TYPE": lambda: f"Level up knowing a {type_(param)}-type move"
                                 + (" with high friendship" if extra not in ("0", "FALSE") else ""),
        "EVO_OTHER_PARTY_MON": lambda: f"Level up with {data.names.get(param, param)} in the party",
        "EVO_CRITICAL_HIT": lambda: "Land 3 critical hits in one battle",
        "EVO_BEAUTY": lambda: "Level up with high Beauty",
        "EVO_FLAG_SET": lambda: "Special event",
    }
    if method in DROPPED_METHODS:
        return None
    if method == "EVO_MEGA":
        if param in ("ITEM_NONE", "MOVE_NONE", "0"):
            return None  # reverting to base form, not an evolution
        return {
            "MEGA_VARIANT_PRIMAL": f"Primal Reversion holding {item(param)}",
            "MEGA_VARIANT_WISH": f"Mega Evolve knowing {move(param)}",
            "MEGA_VARIANT_ULTRA_BURST": f"Ultra Burst holding {item(param)}",
        }.get(extra, f"Mega Evolve holding {item(param)}")
    if method not in texts:
        raise ValueError(f"no text for evolution method {method}")
    return texts[method]()


def _time_range(extra: str) -> str:
    m = re.fullmatch(r"TIME_RANGE\(\s*(\d+)\s*,\s*(\d+)\s*\)", extra)
    if not m:
        raise ValueError(f"unexpected time range {extra!r}")
    return f"{_hour(int(m.group(1)))}–{_hour(int(m.group(2)))}"


def evolution_links(data: SourceData, included: set[str]) -> dict[str, list[dict]]:
    links: dict[str, list[dict]] = {}
    for src in included:
        for method, param, target, extra in data.evolutions.get(src, []):
            if target not in included:
                continue
            text = evolution_text(data, method, param, target, extra)
            if text is not None:
                links.setdefault(src, []).append({"to": target, "text": text})
    return links
