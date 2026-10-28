"""Loaders for data that lives in the sibling Complete-Fire-Red-Upgrade repo."""

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
    for const, body in table.items():
        if const not in names or const == "MOVE_NONE":
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
