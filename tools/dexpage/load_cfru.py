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
    descriptions = move_descriptions(p)
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
            "desc": descriptions.get(const, ""),
            # chance of the secondary effect (Scald's burn: 30); 0 when the move has none or it always happens
            "chance": c if 0 < (c := _int(f.get("secondaryEffectChance"))) < 100 else 0,
        }
    return result


@cache
def move_descriptions(p: Paths) -> dict[str, str]:
    """gMoveDescriptions (assembly/data/attack_description_table.s): entry N describes move N+1; each entry is a
    vanilla ROM address or a symbol from strings/attack_descriptions.string."""
    from .rom import read_text

    by_id = {v: k for k, v in parse_int_defines(p.cfru / "include/constants/moves.h", "MOVE_").items()}
    strings = _labelled_strings(p, "strings/attack_descriptions.string")
    table = read(p.cfru / "assembly/data/attack_description_table.s")
    entries = re.findall(r"^\.word\s+(\w+)", table[table.index("gMoveDescriptions:"):], flags=re.M)
    result = {}
    for n, target in enumerate(entries):
        const = by_id.get(n + 1)
        if const:
            text = read_text(p.rom, int(target, 16)) if target.startswith("0x") else strings.get(target, "")
            result[const] = " ".join(text.split())
    return result


@cache
def ability_ids(p: Paths) -> dict[str, int]:
    """Ability constant → id. DPE assigns the id a species gets (its own spellings, e.g. ABILITY_GULPMISSLE);
    CFRU supplies the name, description and mechanic stored at that id."""
    return {**parse_int_defines(p.cfru / "include/constants/abilities.h", "ABILITY_"),
            **parse_int_defines(p.dpe / "include/abilities.h", "ABILITY_")}


@cache
def ability_names_by_id(p: Paths) -> dict[int, str]:
    rows = parse_string_table(p.cfru / "strings/ability_name_table.string")  # positional: entry N names ability N
    return {n: decode_text(text) for n, (_, text) in enumerate(rows)}


@cache
def ability_names(p: Paths) -> dict[str, str]:
    names = ability_names_by_id(p)
    return {k: names[v] for k, v in ability_ids(p).items() if v in names}


@cache
def item_ids(p: Paths) -> dict[str, int]:
    return parse_int_defines(p.cfru / "include/constants/items.h", "ITEM_")


@cache
def _labelled_strings(p: Paths, table: str) -> dict[str, str]:
    """Text of every #org @label in a .string file, by label (for strings referenced by symbol, not position).
    Consecutive labels share the text that follows them; #ifdef blocks are resolved first."""
    result, labels = {}, []
    for line in resolve_conditionals(read(p.cfru / table), defines(p)).splitlines():
        if line.startswith("#org"):
            labels.append(line.split("@", 1)[1].strip())
        elif labels and line.strip() and not line.startswith("#"):
            for label in labels:
                result[label] = decode_text(line.strip().replace("\\n", " ").replace("\\l", " "))
            labels = []
    return result


@cache
def ability_descriptions_by_id(p: Paths) -> dict[int, str]:
    """gAbilityDescriptions (assembly/data/ability_description_table.s): entry N describes ability N; each entry is
    either a vanilla ROM address or a symbol from strings/ability_descriptions.string."""
    from .rom import read_text

    strings = _labelled_strings(p, "strings/ability_descriptions.string")
    table = read(p.cfru / "assembly/data/ability_description_table.s")
    entries = re.findall(r"^\.word\s+(\w+)", table[table.index("gAbilityDescriptions:"):], flags=re.M)
    result = {}
    for ability_id, target in enumerate(entries):
        text = read_text(p.rom, int(target, 16)) if target.startswith("0x") else strings.get(target, "")
        result[ability_id] = " ".join(text.split())
    return result


def ability_descriptions(p: Paths) -> dict[str, str]:
    descriptions = ability_descriptions_by_id(p)
    return {k: descriptions[v] for k, v in ability_ids(p).items() if v in descriptions}


@cache
def ability_name_overrides(p: Paths) -> list[tuple[str, str, frozenset, frozenset, frozenset]]:
    """Rules from GetAbilityNameOverride (src/ability_util.c): (ABILITY_*, gText_AbilityName_* label, species,
    national dex numbers, types). The renamed ability applies when the species, its national dex number, or one of its types
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
            rules.append((ability, label, frozenset(), frozenset(re.findall(r"NATIONAL_DEX_\w+", dexes)), frozenset()))
        # if (Predicate(...)) return gText_AbilityName_X;
        for call, label in re.findall(r"if\s*\((\w+\([^)]*\))\)\s*return\s+(gText_AbilityName_\w+)", block):
            fn = call.split("(")[0]
            if fn == "IsSpeciesOfType":
                types = frozenset(t.removeprefix("TYPE_") for t in re.findall(r"TYPE_\w+", call))
                rules.append((ability, label, frozenset(), frozenset(), types))
            elif fn.startswith(("SpeciesHas", "Is")):
                species, national = predicate_targets(fn)
                rules.append((ability, label, species, national, frozenset()))
            else:
                raise ValueError(f"unsupported ability-name rule {call!r}")
    return rules


def ability_display(p: Paths, ability: str, species: str, national: str | None, types: list[str]) -> tuple[str, str]:
    """(name, description) as the game shows them for this species. A renamed ability keeps its base description
    unless the game has a matching gText_AbilityDescription_* string (GetAbilityDescriptionOverride)."""
    ids = ability_ids(p)
    ability_id = ids.get(ability)
    if ability_id is None:
        raise ValueError(f"unknown ability {ability} (not in DPE or CFRU abilities.h)")
    names = _labelled_strings(p, "strings/ability_name_table.string")
    descriptions = _labelled_strings(p, "strings/ability_descriptions.string")
    description = ability_descriptions_by_id(p).get(ability_id, "")
    for rule_ability, label, species_set, national_set, type_set in ability_name_overrides(p):  # rules name CFRU constants
        if ids.get(rule_ability) == ability_id and (species in species_set or national in national_set or set(types) & type_set):
            override = descriptions.get(label.replace("AbilityName", "AbilityDescription"))
            return names[label], " ".join((override or description).split())
    return ability_names_by_id(p).get(ability_id, ability), description


BADGE_WORDS = {"No": 0, "One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5, "Six": 6, "Seven": 7, "Eight": 8}
# Script prefixes whose camel-case name isn't the place players know
PLACE_ALIASES = {"FerroxFacilities": "Ferrox Village", "HeleoFacilities": "Heleo City", "LaplazFacilities": "Laplaz Town"}


def _words(camel: str) -> str:
    return re.sub(r"(?<=[a-z])(?=[A-Z0-9])|(?<=[0-9])(?=[A-Z])", " ", camel)


@cache
def marts(p: Paths) -> list[dict]:
    """Every `pokemart <list>` in CFRU's overworld scripts: {"where": place and shop, "items": [ITEM_*]}.

    The place comes from the script that opens the shop (EventScript_DaimynCityMall_Shop_Gems → Daimyn City Mall),
    falling back to the script file's name; the standard Poké Mart stock is gated by badge count."""
    root = p.cfru / "assembly/overworld_scripts"
    files = {f: strip_comments(read(f)) for f in sorted(root.rglob("*.s"))}
    lists: dict[str, list[str]] = {}
    for text in files.values():
        for m in re.finditer(r"^(\w+):\s*\n((?:[ \t]*\.hword[ \t]+ITEM_\w+[^\n]*\n)+)", text, flags=re.M):
            lists[m.group(1)] = [i for i in re.findall(r"ITEM_\w+", m.group(2)) if i != "ITEM_NONE"]

    result, seen = [], set()
    for path, text in files.items():
        for m in re.finditer(r"pokemart\s+(\w+)", text):
            label = m.group(1)
            items = lists.get(label, [])
            if not items:
                continue
            opener = [x.group(1) for x in re.finditer(r"^(\w+):", text[:m.start()], flags=re.M)]
            script = opener[-1] if opener else ""
            badges = re.fullmatch(r"(\w+?)Badges?_Stock", label)
            if badges:
                n = BADGE_WORDS.get(badges.group(1), 0)
                where = "Poké Marts" + (f" (after {n} badge{'s' if n > 1 else ''})" if n else "")
            else:
                prefix = script.removeprefix("EventScript_").split("_")[0] if script.startswith("EventScript_") else ""
                place = PLACE_ALIASES.get(prefix) or (_words(prefix) if prefix else _words(path.stem.replace("_", " ").title().replace(" ", "")))
                shop = _words(re.sub(r"(Shop|Stock|Items|Mart)(Divergent)?$", "", label.split("_")[-1]) or label)
                where = f"{place} · {shop} shop" + (" (Divergent)" if "Divergent" in label + script else "")
            if (where, label) in seen:
                continue
            seen.add((where, label))
            result.append({"where": where, "items": items})
    return result


# Battle code that rolls for ability effects: Poison Touch, Static, Stench, Shed Skin…
ABILITY_EFFECT_FILES = ("src/ability_battle_effects.c", "src/cmd49.c", "src/new_bs_commands.c", "src/end_turn.c")


@cache
def ability_chances(p: Paths) -> dict[int, int]:
    """Ability id → % chance its effect triggers, read from the `case ABILITY_X:` blocks of CFRU's battle code.
    Recognises `Random() % N == 0` / `umodsi(Random(), N) == 0` (1 in N) and `... % 100 < K` (K%, where K may be a
    `chance = K` set in the same block). Abilities without such a roll are left out."""
    ids = ability_ids(p)
    one_in = re.compile(r"(?:umodsi\(\s*Random\(\)\s*,\s*(\d+)\s*\)|Random\(\)\s*%\s*(\d+))\s*==\s*0")
    percent = re.compile(r"(?:umodsi\(\s*Random\(\)\s*,\s*100\s*\)|Random\(\)\s*%\s*100)\s*<\s*(\d+|\w+)")
    chances: dict[int, int] = {}
    for rel in ABILITY_EFFECT_FILES:
        text = strip_comments(read(p.cfru / rel))
        parts = re.split(r"\bcase\s+(ABILITY_\w+)\s*:", text)
        pending: list[str] = []  # fall-through labels share the next block
        for ability, block in zip(parts[1::2], parts[2::2]):
            pending.append(ability)
            if not block.strip().strip(";"):
                continue
            block = block.split("break;")[0]
            value = None
            if m := one_in.search(block):
                value = round(100 / int(m.group(1) or m.group(2)))
            elif m := percent.search(block):
                k = m.group(1)
                if k.isdigit():
                    value = int(k)
                elif v := re.search(rf"\b{k}\s*=\s*(\d+)\s*;", block):
                    value = int(v.group(1))
            for a in pending:
                if value and a in ids:
                    chances.setdefault(ids[a], value)
            pending = []
    return chances
