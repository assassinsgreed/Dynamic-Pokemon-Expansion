"""Loaders for data that lives in the sibling Complete-Fire-Red-Upgrade repo."""

import re
from functools import cache

from .cparse import (
    collect_defines,
    parse_designated_array,
    parse_int_defines,
    parse_string_table,
    parse_struct_fields,
    read,
    resolve_conditionals,
    strip_comments,
)
from .load_dpe import decode_text
from .paths import Paths

SPLITS = {"SPLIT_PHYSICAL": "physical", "SPLIT_SPECIAL": "special", "SPLIT_STATUS": "status"}


@cache
def defines(p: Paths) -> dict[str, str]:
    """The #defines that decide which CFRU #ifdef branches are compiled."""
    return collect_defines(p.cfru / "src/config.h",
                           p.cfru / "include/constants/pokedex.h",
                           p.cfru / "include/constants/species.h",
                           p.cfru / "include/constants/items.h",
                           p.cfru / "src/defines.h")


def source(p: Paths, rel: str) -> str:
    return resolve_conditionals(strip_comments(read(p.cfru / rel)), defines(p))


def _positional_names(p: Paths, table: str, ids: dict[str, int]) -> dict[str, tuple[str, str]]:
    """(in-game name, official name from the label) per constant, for a positional name table."""
    rows = parse_string_table(p.cfru / table)
    result = {}
    for const, idx in ids.items():
        if idx < len(rows):
            label, text = rows[idx]
            official = " ".join(w.capitalize() for w in label.removeprefix("NAME_").split("_"))
            result[const] = (decode_text(text), official)
    return result


def _int(value: str | None) -> int:
    try:
        return int(value or "0", 0)
    except ValueError:
        return 0


@cache
def moves(p: Paths) -> dict[str, dict]:
    ids = parse_int_defines(p.cfru / "include/constants/moves.h", "MOVE_")
    names = _positional_names(p, "strings/attack_name_table.string", ids)
    table = parse_designated_array(source(p, "src/Tables/battle_moves.c"), "gBattleMoves")
    result = {}
    first_z = ids[collect_defines(p.cfru / "include/constants/moves.h")["FIRST_Z_MOVE"]]  # Z and Max moves can't be learned, and their names don't line up
    for const, body in table.items():
        if const not in names or const == "MOVE_NONE" or ids[const] >= first_z:
            continue
        f = parse_struct_fields(body)
        result[const] = {
            "name": names[const][0],
            "official": names[const][1],
            "type": f.get("type", "TYPE_NORMAL").removeprefix("TYPE_"),
            "split": SPLITS.get(f.get("split", ""), "status"),
            "power": _int(f.get("power")),
            "accuracy": _int(f.get("accuracy")),
            "pp": _int(f.get("pp")),
        }
    return result


@cache
def ability_names(p: Paths) -> dict[str, str]:
    ids = parse_int_defines(p.cfru / "include/constants/abilities.h", "ABILITY_")
    return {k: v[0] for k, v in _positional_names(p, "strings/ability_name_table.string", ids).items()}


@cache
def item_ids(p: Paths) -> dict[str, int]:
    return parse_int_defines(p.cfru / "include/constants/items.h", "ITEM_")


def _labelled_strings(p: Paths, table: str) -> dict[str, str]:
    """Text of every #org @label in a .string file, by label (for strings referenced by symbol, not position)."""
    result, label = {}, None
    for line in read(p.cfru / table).splitlines():
        if line.startswith("#org"):
            label = line.split("@", 1)[1].strip()
        elif label and line.strip():
            result[label] = decode_text(line.strip())
            label = None
    return result


@cache
def ability_name_overrides(p: Paths) -> list[tuple[str, str, frozenset, frozenset, frozenset]]:
    """Rules from GetAbilityNameOverride (src/ability_util.c): (ABILITY_*, display name, species, national dex
    numbers, types). The renamed ability applies when the species, its national dex number, or one of its types
    matches."""
    raw = strip_comments(read(p.cfru / "src/ability_util.c"))
    names = _labelled_strings(p, "strings/ability_name_table.string")

    def function(name: str) -> str:
        m = re.search(rf"^\S[^\n]*\b{name}\s*\([^;{{]*\)\s*{{", raw, flags=re.M)
        if not m:
            raise ValueError(f"{name} not found in ability_util.c")
        return resolve_conditionals(raw[m.start():raw.index("\n}", m.start())], defines(p))

    def predicate_targets(name: str) -> tuple[frozenset, frozenset]:
        body = function(name)
        return frozenset(re.findall(r"species\s*==\s*(SPECIES_\w+)", body)), frozenset(re.findall(r"NATIONAL_DEX_\w+", body))

    body = function("GetAbilityNameOverride")
    rules = []
    cases = re.split(r"\n\t\tcase\s+(ABILITY_\w+)\s*:", body)
    for ability, block in zip(cases[1::2], cases[2::2]):
        # switch (dexNum) { case NATIONAL_DEX_A: case NATIONAL_DEX_B: return gText_AbilityName_X; ... }
        for dexes, label in re.findall(r"((?:case\s+NATIONAL_DEX_\w+\s*:\s*)+)return\s+(gText_AbilityName_\w+)", block):
            rules.append((ability, names[label], frozenset(), frozenset(re.findall(r"NATIONAL_DEX_\w+", dexes)), frozenset()))
        # if (Predicate(...)) return gText_AbilityName_X;
        for call, label in re.findall(r"if\s*\((\w+\([^)]*\))\)\s*return\s+(gText_AbilityName_\w+)", block):
            fn = call.split("(")[0]
            if fn == "IsSpeciesOfType":
                types = frozenset(t.removeprefix("TYPE_") for t in re.findall(r"TYPE_\w+", call))
                rules.append((ability, names[label], frozenset(), frozenset(), types))
            elif fn.startswith(("SpeciesHas", "Is")):
                species, national = predicate_targets(fn)
                rules.append((ability, names[label], species, national, frozenset()))
            else:
                raise ValueError(f"unsupported ability-name rule {call!r}")
    return rules


def ability_display_name(p: Paths, ability: str, species: str, national: str | None, types: list[str]) -> str:
    for rule_ability, name, species_set, national_set, type_set in ability_name_overrides(p):
        if rule_ability == ability and (species in species_set or national in national_set or set(types) & type_set):
            return name
    return ability_names(p).get(ability, ability)
