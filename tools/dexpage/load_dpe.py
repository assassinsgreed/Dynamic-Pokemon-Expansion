"""Loaders for this repo's (DPE) data tables. All results are keyed by SPECIES_* constant name."""

import re
import unicodedata
import warnings
from functools import cache
from pathlib import Path

from .cparse import (
    array_body,
    collect_defines,
    match_brace,
    parse_designated_array,
    parse_int_defines,
    parse_string_table,
    parse_struct_fields,
    read,
    resolve_conditionals,
    split_top_level,
    strip_comments,
)
from .paths import Paths

# Game text escapes used in the .string files
CHAR_ESCAPES = {"[B5]": "♂", "[B6]": "♀", "[.]": "…", "\e": "é"}


def decode_text(text: str) -> str:
    for code, char in CHAR_ESCAPES.items():
        text = text.replace(code, char)
    return text


@cache
def _source(p: Paths, rel: str) -> str:
    defines = collect_defines(p.dpe / "src/defines.h")
    return resolve_conditionals(strip_comments(read(p.dpe / rel)), defines)


@cache
def item_ids(p: Paths) -> dict[str, int]:
    """Item constants as this repo's tables were compiled with them (includes DPE-only spellings)."""
    return parse_int_defines(p.dpe / "include/items.h", "ITEM_")


@cache
def species_ids(p: Paths) -> dict[str, int]:
    return parse_int_defines(p.dpe / "include/species.h", "SPECIES_")


def _species_list(body: str) -> list[str]:
    return re.findall(r"\bSPECIES_\w+", body)


def dex_lists(p: Paths) -> tuple[list[str], list[str]]:
    text = _source(p, "src/Pokedex_Orders.c")
    return (_species_list(array_body(text, "gPokedexOrder_Regional")),
            _species_list(array_body(text, "gPokedexOrder_Divergent_Regional")))


def habitat_forms(p: Paths) -> dict[str, set[str]]:
    text = _source(p, "src/Habitat_Table.c")
    forms: dict[str, set[str]] = {}
    for m in re.finditer(r"const\s+u16\s+(g\w+Page\d+)\s*\[\s*\]\s*=", text):
        kind = "divergent" if "Divergent" in m.group(1) else "standard"
        for species in _species_list(array_body(text, m.group(1))):
            forms.setdefault(species, set()).add(kind)
    return forms


def _strip_prefix(value: str, prefix: str) -> str:
    return value[len(prefix):] if value.startswith(prefix) else value


def _gender(value: str) -> float | None:
    if value == "MON_GENDERLESS":
        return None
    if value == "MON_MALE":
        return 0.0
    if value == "MON_FEMALE":
        return 100.0
    m = re.fullmatch(r"PERCENT_FEMALE\(\s*([\d.]+)\s*\)", value)
    if m:
        return float(m.group(1))
    return round(int(value, 0) / 254 * 100, 1)


@cache
def base_stats(p: Paths) -> dict[str, dict]:
    stats = {}
    for species, body in parse_designated_array(_source(p, "src/Base_Stats.c"), "gBaseStats").items():
        f = parse_struct_fields(body)
        if "baseHP" not in f:
            continue
        types = [_strip_prefix(f["type1"], "TYPE_")]
        if f.get("type2") and f["type2"] != f["type1"]:
            types.append(_strip_prefix(f["type2"], "TYPE_"))
        abilities = []
        for a in (f.get("ability1"), f.get("ability2")):
            if a and a != "ABILITY_NONE" and a not in abilities:
                abilities.append(a)
        hidden = f.get("hiddenAbility")
        hidden = None if hidden in (None, "ABILITY_NONE") or hidden in abilities else hidden
        egg_groups = []
        for g in (f.get("eggGroup1"), f.get("eggGroup2")):
            g = _strip_prefix(g or "", "EGG_GROUP_")
            if g and g not in egg_groups:
                egg_groups.append(g)
        stats[species] = {
            "hp": int(f["baseHP"], 0), "atk": int(f["baseAttack"], 0), "def": int(f["baseDefense"], 0),
            "spa": int(f["baseSpAttack"], 0), "spd": int(f["baseSpDefense"], 0), "spe": int(f["baseSpeed"], 0),
            "types": types,
            "abilities": abilities,
            "hidden_ability": hidden,
            "catch_rate": int(f.get("catchRate", "0"), 0),
            "gender": _gender(f.get("genderRatio", "MON_GENDERLESS")),
            "egg_groups": egg_groups,
            "growth": _strip_prefix(f.get("growthRate", ""), "GROWTH_"),
            "ev_yield": {k: int(f.get(f"evYield_{src}", "0"), 0) for k, src in
                         (("hp", "HP"), ("atk", "Attack"), ("def", "Defense"),
                          ("spa", "SpAttack"), ("spd", "SpDefense"), ("spe", "Speed"))},
        }
    return stats


@cache
def levelup(p: Paths) -> dict[str, list[tuple[int, str]]]:
    text = _source(p, "src/Learnsets.c")
    by_symbol = {}
    for m in re.finditer(r"struct\s+LevelUpMove\s+(\w+)\s*\[\s*\]\s*=", text):
        body = array_body(text, m.group(1))
        by_symbol[m.group(1)] = [(int(lvl), move) for lvl, move in
                                 re.findall(r"LEVEL_UP_MOVE\(\s*(\d+)\s*,\s*(MOVE_\w+)\s*\)", body)]
    return {species: by_symbol[symbol.strip()]
            for species, symbol in parse_designated_array(text, "gLevelUpLearnsets").items()
            if symbol.strip() in by_symbol}


@cache
def egg_moves(p: Paths) -> dict[str, list[str]]:
    text = _source(p, "src/Egg_Moves.c")
    result = {}
    for m in re.finditer(r"egg_moves\(\s*(\w+)\s*,", text):
        start = text.index("(", m.start())
        args = split_top_level(text[start + 1:match_brace(text, start)])
        # GetEggMoves stops at the first entry for a species, so later duplicates never apply
        result.setdefault("SPECIES_" + args[0], [a for a in args[1:] if a.startswith("MOVE_")])
    return result


NUM_TMS = 100  # HM01 is file 101
HEADER_RE = re.compile(r"^(TM|HM|[A-Za-z]+)\s*(\d+)\s*:\s*(.+)$")  # tutor headers include typos like "Tutour"


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())


@cache
def machine_compat(p: Paths) -> list[dict]:
    from .load_cfru import moves

    by_name: dict[str, str] = {}
    for key, m in moves(p).items():
        by_name.setdefault(_norm(m["name"]), key)
        by_name.setdefault(_norm(m["official"]), key)
        by_name.setdefault(_norm(_strip_prefix(key, "MOVE_")), key)

    result = []
    for folder in ("tm_compatibility", "tutor_compatibility"):
        for path in sorted((p.dpe / "src" / folder).glob("*.txt")):
            lines = [line.strip() for line in read(path).splitlines() if line.strip()]
            m = HEADER_RE.match(lines[0])
            if not m:
                raise ValueError(f"{path}: unexpected header {lines[0]!r}")
            move = by_name.get(_norm(m.group(3)))
            if move is None:
                raise ValueError(f"{path}: no move named {m.group(3)!r}")
            kind = "Tutor" if folder == "tutor_compatibility" else m.group(1)
            # The build script numbers machines by filename, so the header number is only a cross-check
            num = int(path.name.split(" - ", 1)[0])
            if kind == "HM":
                num -= NUM_TMS
            if num != int(m.group(2)):
                warnings.warn(f"{path.name}: header says {lines[0]!r}; using the filename number")
            result.append({"kind": kind, "num": num, "move": move,
                           "species": {"SPECIES_" + s for s in lines[1:]}})
    return result


@cache
def evolutions(p: Paths) -> dict[str, list[tuple[str, str, str, str]]]:
    result = {}
    for species, body in parse_designated_array(_source(p, "src/Evolution Table.c"), "gEvolutionTable").items():
        entries = []
        for entry in split_top_level(body):
            parts = split_top_level(entry.strip().strip("{}"))
            if parts and parts[0].startswith("EVO_"):
                parts += ["0"] * (4 - len(parts))
                entries.append(tuple(" ".join(x.split()) for x in parts[:4]))
        result[species] = entries
    return result


@cache
def species_names(p: Paths) -> dict[str, str]:
    """The name table is positional: entry N is species id N."""
    rows = parse_string_table(p.dpe / "strings/Pokemon_Name_Table.string")
    names = {}
    for species, sid in species_ids(p).items():
        if sid < len(rows):
            names[species] = decode_text(rows[sid][1])
    return names


def _graphic(p: Paths, folder: str, name: str) -> Path:
    path = p.dpe / "graphics" / folder / f"{name}.png"
    if not path.exists():  # e.g. Castform keeps its sprites in graphics/castform
        path = next((p.dpe / "graphics").rglob(f"{name}.png"), path)
    return path


@cache
def front_pic(p: Paths) -> dict[str, Path]:
    result = {}
    for species, body in parse_designated_array(_source(p, "src/Front_Pic_Table.c"), "gMonFrontPicTable").items():
        m = re.match(r"(gFrontSprite\w+?)Tiles\b", body.strip())
        if m:
            result[species] = _graphic(p, "frontspr", m.group(1))
    return result


@cache
def shiny_pal(p: Paths) -> dict[str, Path]:
    """gMonShinyPaletteTable names each species' shiny palette after a back sprite (gBackShinySprite…Pal); the game
    compiles that PNG's own palette, so the PNG is the source."""
    result = {}
    for species, body in parse_designated_array(_source(p, "src/Shiny_Palette_Table.c"), "gMonShinyPaletteTable").items():
        m = re.match(r"(gBackShinySprite\w+?)Pal\b", body.strip())
        if m:
            result[species] = _graphic(p, "backspr", m.group(1))
    return result
