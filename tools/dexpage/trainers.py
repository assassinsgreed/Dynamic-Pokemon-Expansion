"""Trainers: every trainer in CFRU's four trainer tables, with the team the game builds for each difficulty.

Which table a battle loads (GetTrainerData in build_pokemon.c), highest priority first:
  Hard + Divergent: hard_divergent_trainer_tables.c, else divergent, else hard, else standard
  Divergent:        divergent_trainer_tables.c, else standard
  Hard:             hard_trainer_tables.c, else standard
A trainer missing from an override table falls through to the next one down. Hard and Very Hard both load the hard
tables (FLAG_HARD_MODE is set for both).

How each Pokémon is finished (CreateNPCTrainerParty), with CFRU's config (no level scaling, no TRAINERS_WITH_EVS):
  IVs: gBaseIVsByTrainerClass, or STANDARD_IV when the class has no entry; 31 on Very Hard (opponents only)
  EVs: none, except Very Hard: 252 in the two best base stats (GiveMon2BestBaseStatEVs)
  Nature: on Hard and Very Hard, chosen from base stats and moves (GiveMonBestStatNature, opponents only)
  Moves: the table's, or the last four level-up moves at that level (GiveBoxMonInitialMoveset)
  Ability: the table's Ability_* choice (a custom team that names none gets Ability_Hidden, the enum's 0). A
    default-move team gets no choice: each Pokémon's personality starts at 0x88 for a MALE trainer or 0x0F for a
    FEMALE one (setMonGender = trainer->gender always, so the name-length branch is never taken), its species-name
    hash is added << 8, and the low bit picks the ability, kept through Hard's nature reroll. So a male trainer's
    Pokémon have their first ability and a female trainer's their second (the first if the species has only one)

Trainer sprites come from the built ROM: each trainer's trainerPic byte is read from the compiled gTrainers (address
from offsets.ini), since TRAINER_PIC_* constants have #ifdef'd duplicates and many pictures are inserted at build time."""

import re
import struct
from functools import cache
from pathlib import Path

from PIL import Image

from .cparse import array_body, collect_defines, match_brace, parse_designated_array, parse_struct_fields, read, split_top_level
from .load_cfru import source
from .paths import Paths
from .rom import _charmap, _rom_bytes, decode, lz77

TABLES = {  # key → (file, array)
    "std": ("src/Tables/trainer_tables.c", "gTrainers"),
    "hard": ("src/Tables/hard_trainer_tables.c", "gHardTrainers"),
    "div": ("src/Tables/divergent_trainer_tables.c", "gDivergentTrainers"),
    "hdiv": ("src/Tables/hard_divergent_trainer_tables.c", "gHardDivergentTrainers"),
}
FALLBACK = {"std": ("std",), "hard": ("hard", "std"), "div": ("div", "std"), "hdiv": ("hdiv", "div", "hard", "std")}

TRAINER_PIC_TABLE = 0x23957C  # gTrainerFrontPicTable: {LZ77 tiles, size, tag}
TRAINER_PAL_TABLE = 0x239A1C  # gTrainerFrontPicPaletteTable: {LZ77 palette, tag}
CLASS_NAMES = 0x23E558        # gTrainerClassNames: 13 bytes each
CLASS_NAME_LENGTH = 13

# Stat order of gBaseStats / GetVisualBaseStat: HP, Atk, Def, Spe, SpA, SpD
STATS = ("hp", "atk", "def", "spe", "spa", "spd")
NATURES = ["Hardy", "Lonely", "Brave", "Adamant", "Naughty", "Bold", "Docile", "Relaxed", "Impish", "Lax",
           "Timid", "Hasty", "Serious", "Jolly", "Naive", "Modest", "Mild", "Quiet", "Bashful", "Rash",
           "Calm", "Gentle", "Sassy", "Careful", "Quirky"]
SPEED_BOOSTING = {"MOVE_AGILITY", "MOVE_AUTOTOMIZE", "MOVE_DRAGONDANCE", "MOVE_ESPERWING", "MOVE_FLAMECHARGE",
                  "MOVE_GEOMANCY", "MOVE_QUIVERDANCE", "MOVE_ROCKPOLISH", "MOVE_SHELLSMASH", "MOVE_SHIFTGEAR",
                  "MOVE_VICTORYDANCE"}
FIXED_DAMAGE = {"EFFECT_0HKO", "EFFECT_SUPER_FANG", "EFFECT_DRAGON_RAGE", "EFFECT_SONICBOOM", "EFFECT_LEVEL_DAMAGE",
                "EFFECT_PSYWAVE", "EFFECT_COUNTER", "EFFECT_MIRROR_COAT", "EFFECT_BIDE", "EFFECT_ENDEAVOR",
                "EFFECT_MEMENTO"}
VARIABLE_POWER_ESTIMATE = 70

# The rival's team follows the generation of the player's water starter (var 0x408E, 0-7); trainer IDs run in this order
WATER_STARTERS = {"V": "Squirtle", "J": "Totodile", "F": "Mudkip", "E": "Piplup", "U": "Oshawott", "L": "Froakie",
                  "G": "Popplio", "S": "Sobble"}
# Variants the constant's name doesn't explain, checked against CFRU's overworld scripts
NOTES = {
    "TRAINER_HELEO_CITY_GYM_LEADER_RAINE": "Team when challenged with 2 badges",
    "TRAINER_HELEO_CITY_GYM_LEADER_RAINE_2": "Team when challenged with 3 badges",
    "TRAINER_HELEO_CITY_GYM_LEADER_RAINE_3": "Team when challenged with 4 badges",
    "TRAINER_DAIMYN_CITY_GYM_LEADER_CHANCE": "Team when challenged with 2 or 3 badges",
    "TRAINER_DAIMYN_CITY_GYM_LEADER_CHANCE_2": "Team when challenged with 4 badges",
    "TRAINER_DAIMYN_CITY_RIVAL_EXHIBITION_BATTLE_2": "Exhibition battle: Emraldin team, before the game is cleared",
    "TRAINER_POSTGAME_RIVAL_EXHIBITION_BATTLE_EMRALDIN": "Exhibition battle: Emraldin team, after the game is cleared",
}
# "Important trainers" sit in their own region of gTrainers; most constants start with their place's name
RIVAL_PLACES = {"TRAINER_RIVAL1": "Route 17", "TRAINER_RIVAL2": "Route 3", "TRAINER_RIVAL3": "Daimyn City"}
# Battles fought with FLAG_SCALE_TRAINER_LEVELS (0x90E) set, so every Pokémon comes out at your party's highest level:
# the Trainer Houses, Nurse Brianne, the dev team and the Gym Trainees set it in their scripts; Collin lists the Stats
# Dojo disciples too (not Kaito, the dojo master)
SCALED = re.compile(r"TRAINER_HOUSE|_NURSE_BRIANNE$|_DEV_TEAM_|_GYM_TRAINEE_|_STATS_DOJO_\w+_\d$")
CASEY_NOTE = {"F": "Female Casey: battled when you play as a boy", "M": "Male Casey: battled when you play as a girl"}


def _const_note(const: str) -> str:
    if const in NOTES:
        return NOTES[const]
    m = re.search(r"_RIVAL_([VJFEULGS])$", const) or re.search(r"EXHIBITION_BATTLE_([VJFEULGS])$", const)
    if m:
        what = "Exhibition battle: Eevee team, after the game is cleared · " if "EXHIBITION" in const else ""
        return f"{what}Team when your water starter is {WATER_STARTERS[m.group(1)]}"
    m = re.search(r"_REMATCH_(\d)$", const)
    if m:
        return f"Rematch team {m.group(1)} of 4 (one is picked at random each day)"
    if const.endswith("_REMATCH"):
        return "Rematch"
    m = re.search(r"CASEY_([FM])(?:_|$)", const)
    if m:
        return CASEY_NOTE[m.group(1)]
    m = re.search(r"STATS_DOJO_\w+_(\d)$", const)
    if m:
        return f"Level {m.group(1)} of 3 (you choose)"
    m = re.search(r"DEV_TEAM_\w+_(\d)$", const)
    if m:
        return f"Team {m.group(1)} of 2"
    m = re.search(r"COPYCAT_([MF])$", const)
    if m:
        return "Copies your team · " + ("battled when you play as a boy" if m.group(1) == "M" else "battled when you play as a girl")
    return ""


@cache
def _easy_text(p: Paths) -> dict[str, int]:
    return {k: int(v, 0) for k, v in collect_defines(p.cfru / "include/easy_text.h").items() if re.fullmatch(r"0x[0-9A-Fa-f]+|\d+", v or "")}


def _name(p: Paths, value: str) -> str:
    """{_C, _a, _s, _e, _y, _END} → Casey; NO_NAME (the rival) → ""."""
    letters = re.findall(r"\w+", value)
    if not letters or letters == ["NO_NAME"]:
        return ""
    codes = _easy_text(p)
    return decode(bytes(codes[x] for x in letters if x in codes) + b"\xff", _charmap()).strip()


def _parties(text: str) -> dict[str, list[dict]]:
    """Every `const struct TrainerMon… sParty_X[] = {…}` → its Pokémon's fields."""
    parties = {}
    for m in re.finditer(r"\bstruct\s+TrainerMon\w+\s+(\w+)\s*\[\s*\]\s*=\s*{", text):
        start = m.end() - 1
        body = text[start + 1:match_brace(text, start)]
        parties[m.group(1)] = [parse_struct_fields(e.strip()[1:-1]) for e in split_top_level(body)]
    return parties


def _place_words(name: str) -> list[str]:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).split()


def _regions(p: Paths) -> tuple[dict[str, str], dict[str, int]]:
    """(trainer constant → place, place → sort position). Places are the `// #region` headings of gTrainers (Route 1,
    Heleo City…), which follow the game's route. Trainers under "Important trainers" go to the place their constant
    starts with (TRAINER_TORMA_CAVE_CASEY_F → Torma Cave) and sort with it."""
    text = read(p.cfru / TABLES["std"][0])
    text = text[text.index("gTrainers[]"):]
    regions, current = {}, ""
    for line in text.splitlines():
        m = re.match(r"\s*//\s*#region\s+(.+?)\s*$", line)
        if m:
            current = m.group(1)
        m = re.match(r"\s*\[(TRAINER_\w+)\]\s*=", line)
        if m:
            regions[m.group(1)] = current
    names = [r for r in dict.fromkeys(regions.values()) if r != "Important trainers"]
    order = {r: n for n, r in enumerate(names)}
    parts = [(w, r) for r in names for part in re.split(r"\s*(?:&|\band\b)\s*", r) if (w := _place_words(part))]
    for const, region in regions.items():
        if region != "Important trainers":
            continue
        words = _place_words(const.removeprefix("TRAINER_"))
        found = [(len(w), r) for w, r in parts if words[:len(w)] == w]
        place = RIVAL_PLACES.get(const) or (max(found)[1] if found else region)
        regions[const] = place
        if place not in order:  # a place with no trainers of its own: beside a region named like it, else first
            near = [order[r] for r in names if _place_words(r)[:len(_place_words(place))] == _place_words(place)]
            order[place] = min(near) - 0.5 if near else -1
    # Gym and Trainer House trainers get their building in the place name (TRAINER_LAPLAZ_TRAINER_HOUSE_… → Laplaz
    # Town Trainer House), listed right after their town; the Gym Trainees' café isn't a gym
    for const, region in regions.items():
        m = re.match(r"TRAINER_(\w+?)_(GYM|TRAINER_HOUSE|LIBRARY)_", const)
        if not m or "_GYM_TRAINEE_" in const or region.endswith(" Gym"):
            continue
        prefix = _place_words(m.group(1))
        towns = [part for part in re.split(r"\s*(?:&|\band\b)\s*", region) if _place_words(part)[:len(prefix)] == prefix]
        building = {"GYM": " Gym", "TRAINER_HOUSE": " Trainer House", "LIBRARY": " Library"}[m.group(2)]
        place = (towns[0] if towns else region) + building
        if building == " Library":  # the game calls it Ferrox Library, not Ferrox Village Library
            place = m.group(1).replace("_", " ").title() + building
        regions[const] = place
        order.setdefault(place, order.get(region, len(order)) + (0.25 if building == " Gym" else 0.5))
    return regions, order


@cache
def load_tables(p: Paths) -> dict[str, dict[str, dict]]:
    """Table key → trainer constant → {fields…, "party": [mon fields]}."""
    result = {}
    for key, (rel, array) in TABLES.items():
        text = source(p, rel)
        parties = _parties(text)
        trainers = {}
        for const, body in parse_designated_array(text, array).items():
            f = parse_struct_fields(body)
            m = re.search(r"=\s*(\w+)", f.get("party", ""))
            if not m:
                continue  # a blank entry: the game falls through to the next table
            f["party_list"] = parties[m.group(1)]
            trainers[const] = f
        result[key] = trainers
    return result


@cache
def class_names(p: Paths) -> list[str]:
    rom = _rom_bytes(p.rom)
    names = []
    for i in range(len(_class_ids(p))):
        raw = rom[CLASS_NAMES + CLASS_NAME_LENGTH * i:CLASS_NAMES + CLASS_NAME_LENGTH * (i + 1)]
        raw = raw.replace(b"\x53\x54", b"\xca\xc5\xc7\xc8")  # the [PK][MN] glyphs → "PKMN"
        names.append(decode(raw, _charmap()).strip())
    return names


@cache
def _class_ids(p: Paths) -> dict[str, int]:
    text = read(p.cfru / "include/constants/trainer_classes.h")
    body = text[text.index("{") + 1:text.index("}")]
    ids, n = {}, -1
    for entry in re.findall(r"^\s*(CLASS_\w+)\s*(?:=\s*(\w+))?\s*,", body, flags=re.M):
        n = int(entry[1], 0) if entry[1] else n + 1
        ids[entry[0]] = n
    return ids


@cache
def class_balls(p: Paths) -> dict[str, str]:
    """Trainer class → the Poké Ball its Pokémon come out of (gClassPokeBalls, as an item constant). A class the table
    leaves out reads ball type 0, the Master Ball."""
    table = parse_designated_array(source(p, "src/Tables/class_based_pokeball_table.c"), "gClassPokeBalls")
    return {cls: "ITEM_" + ball.strip().removeprefix("BALL_TYPE_") for cls, ball in table.items()}


@cache
def _class_ivs(p: Paths) -> dict[str, int]:
    text = source(p, "src/Tables/trainers_with_evs_table.h")
    return {k: min(31, int(v, 0)) for k, v in parse_designated_array(text, "gBaseIVsByTrainerClass").items()}


TRAINER_STRUCT_SIZE = 0x28
TRAINER_PIC_OFFSET = 3


def _rom_pics(p: Paths, ids: dict[str, int]) -> dict[str, int]:
    """Trainer constant → the trainerPic byte of its compiled gTrainers entry in the ROM."""
    m = re.search(r"^gTrainers:\s+([0-9A-Fa-f]{8})", read(p.cfru / "offsets.ini"), flags=re.M)
    base = int(m.group(1), 16) - 0x08000000
    rom = _rom_bytes(p.rom)
    return {const: rom[base + TRAINER_STRUCT_SIZE * n + TRAINER_PIC_OFFSET] for const, n in ids.items()}


def trainer_pic(p: Paths, pic: int) -> Image.Image:
    """A trainer's 64×64 battle sprite, decoded from the ROM."""
    rom = _rom_bytes(p.rom)
    u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
    tiles = lz77(rom, u32(TRAINER_PIC_TABLE + 8 * pic))
    pal = lz77(rom, u32(TRAINER_PAL_TABLE + 8 * pic))
    colours = []
    for i in range(16):
        c = struct.unpack_from("<H", pal, 2 * i)[0]
        colours.append(((c & 31) * 255 // 31, (c >> 5 & 31) * 255 // 31, (c >> 10 & 31) * 255 // 31, 0 if i == 0 else 255))
    img = Image.new("RGBA", (64, 64))
    px = img.load()
    for t in range(64):
        for y in range(8):
            for x in range(8):
                b = tiles[t * 32 + y * 4 + x // 2]
                px[(t % 8) * 8 + x, (t // 8) * 8 + y] = colours[b >> 4 if x & 1 else b & 15]
    return img


# ---------------------------------------------------------------- building each Pokémon

def default_moves(learnset: list[tuple[int, str]], level: int) -> list[str]:
    """GiveBoxMonInitialMoveset: the last four level-up moves at or below the level (stopping at the first one
    above it), given in order; a move already known is skipped rather than taking a slot."""
    stack = []
    for lvl, move in learnset:
        if lvl > level:
            break
        stack.append(move)
    known = []
    for move in stack[-4:]:
        if move not in known:
            known.append(move)
    return known


def best_stat_nature(stats: dict, moves: list[str], move_data: dict) -> str:
    """GiveMonBestStatNature: raise the best stat it uses, lower one it doesn't need."""
    base = {s: stats[s] for s in STATS}
    phys = spec = 0
    speed_booster = any(m in SPEED_BOOSTING for m in moves)
    slow = "MOVE_TRICKROOM" in moves or "MOVE_GYROBALL" in moves
    for move in moves:
        mv = move_data.get(move)
        if not mv or mv["split"] == "status" or move in ("MOVE_FOULPLAY", "MOVE_BODYPRESS") or mv["effect"] in FIXED_DAMAGE:
            continue
        power = mv["power"] if mv["power"] > 1 else VARIABLE_POWER_ESTIMATE
        if move in ("MOVE_PHOTONGEYSER", "MOVE_SHELLSIDEARM"):
            phys += power
            spec += power
        elif mv["split"] == "physical":
            phys += power
        else:
            spec += power
    order = STATS[1:]  # Atk, Def, Spe, SpA, SpD
    can_raise = dict.fromkeys(order, True)
    can_lower = dict.fromkeys(order, True)
    atk_score, spa_score = base["atk"] * phys, base["spa"] * spec
    best = worst = dump = lean = None
    if atk_score or spa_score:
        lean = "atk" if atk_score >= spa_score else "spa"
        can_raise["spa" if lean == "atk" else "atk"] = False
        if min(atk_score, spa_score) * 2 >= max(atk_score, spa_score):
            can_lower["atk"] = can_lower["spa"] = False
        else:
            dump = "spa" if lean == "atk" else "atk"
    if slow:
        can_raise["spe"] = False
        dump = "spe"
    elif speed_booster:
        can_lower["spe"] = False
    for s in order:
        if can_raise[s] and (best is None or base[s] > base[best] or (base[s] == base[best] and s == lean)):
            best = s
    if dump:
        worst = dump
    else:
        for s in order:
            if s != best and can_lower[s] and (worst is None or base[s] < base[worst]):
                worst = s
    return NATURES[order.index(best) * 5 + order.index(worst)]


def best_two_stats(stats: dict) -> list[str]:
    """GiveMon2BestBaseStatEVs: the two stats that get 252 EVs on Very Hard (earlier stats win ties)."""
    b1, b2 = ("hp", "atk") if stats["hp"] > stats["atk"] else ("atk", "hp")
    for s in STATS[2:]:
        if stats[s] > stats[b1]:
            b1, b2 = s, b1
        elif stats[s] > stats[b2]:
            b2 = s
    return [b1, b2]


def _ability(choice: str | None, species_stats: dict, female: bool = False) -> str:
    """The ability the game gives: Ability_1 / _2 / _Hidden; either of the two regular ones for Ability_Random_1_2
    (rolled in battle), joined with " or "; and for a default-move team, which names none, the one its trainer's
    gender sets (module docstring): the first for a male trainer, the second for a female one."""
    a1 = species_stats["abilities"][0] if species_stats["abilities"] else None
    a2 = species_stats["abilities"][1] if len(species_stats["abilities"]) > 1 else a1
    if choice is None:
        return (a2 if female else a1) or ""
    if choice in ("Ability_Random_1_2", "Ability_RandomAll"):  # RandomAll: the hidden one a third of the time
        extra = (species_stats["hidden_ability"],) if choice == "Ability_RandomAll" else ()
        return " or ".join(dict.fromkeys(a for a in (a1, a2, *extra) if a))
    pick = {"Ability_1": a1, "Ability_2": a2, "Ability_Hidden": species_stats["hidden_ability"] or a1}.get(choice)
    return pick or ""


def _gender(species_stats: dict, female_trainer: bool) -> str | None:
    """"M", "F" or None (genderless). The personality's low byte is the trainer's 0x88 (MALE) or 0x0F (FEMALE), and
    FireRed's GetGenderFromSpeciesAndPersonality (0x803F78C, not hooked) makes a Pokémon female when its gender ratio
    is above that byte. So a female trainer's Pokémon are female whenever they can be, and a male trainer's male,
    except species 75%+ female (ratio 191 > 136; Galarian Corsola on Swimmer Huey)."""
    pct = species_stats["gender"]
    if pct is None:
        return None
    ratio = int(min(254, pct * 255 / 100))  # PERCENT_FEMALE, truncated to the u8 field
    if ratio in (0, 254):
        return "M" if ratio == 0 else "F"
    return "F" if ratio > (0x0F if female_trainer else 0x88) else "M"


@cache
def move_effects(p: Paths) -> dict[str, str]:
    table = parse_designated_array(source(p, "src/Tables/battle_moves.c"), "gBattleMoves")
    return {k: parse_struct_fields(v).get("effect", "") for k, v in table.items()}


def load_trainers(p: Paths, stats: dict, learnsets: dict, move_data: dict, ability_name) -> tuple[list[dict], list[list[dict]], dict[int, Image.Image]]:
    """(trainers, teams, pics). Each trainer names a team per table key; identical teams are stored once.
    ability_name(const, species) gives the name a species shows for an ability."""
    tables = load_tables(p)
    regions, place_order = _regions(p)
    class_ids, names, class_ivs = _class_ids(p), class_names(p), _class_ivs(p)
    standard_iv = int(collect_defines(p.cfru / "src/config.h")["STANDARD_IV"].split()[0])
    effects = move_effects(p)
    moves = {k: dict(m, effect=effects.get(k, "")) for k, m in move_data.items()}
    ids = {k: int(v) for k, v in collect_defines(p.cfru / "include/constants/opponents.h").items()
           if k.startswith("TRAINER_") and (v or "").isdigit()}
    order = sorted(ids, key=ids.get)
    rom_pics = _rom_pics(p, ids)

    teams: list[list[dict]] = []
    team_index: dict[str, int] = {}
    pics: dict[int, Image.Image] = {}
    trainers = []
    for const in order:
        std = tables["std"].get(const)
        if not std or "PARTNER" in const:
            continue  # partners fight on your side; the page lists only opponents
        found = {}
        for key, chain in FALLBACK.items():
            table = next(t for t in chain if const in tables[t] or t == "std")
            entry = tables[table][const]
            team = _team(entry, stats, learnsets, moves, ability_name)
            sig = repr(team)
            if sig not in team_index:
                team_index[sig] = len(teams)
                teams.append(team)
            found[key] = team_index[sig]
        cls = std["trainerClass"]
        pic = rom_pics[const]
        if pic not in pics:
            pics[pic] = trainer_pic(p, pic)
        trainers.append({
            "const": const,
            "cls": names[class_ids[cls]] if cls in class_ids else cls,
            "name": _name(p, std.get("trainerName", "")),
            "rival": cls in ("CLASS_RIVAL", "CLASS_RIVAL_2"),
            "pic": pic,
            "place": regions.get(const, ""),
            "note": _const_note(const),
            "double": std.get("doubleBattle") == "TRUE",
            "scaled": bool(SCALED.search(const)),
            "items": [i for i in re.findall(r"ITEM_\w+", std.get("items", "")) if i != "ITEM_NONE"],
            "iv": class_ivs.get(cls) or standard_iv,
            "ball": class_balls(p).get(cls, "ITEM_MASTER_BALL"),
            "teams": found,
        })
    trainers.sort(key=lambda t: place_order.get(t["place"], len(place_order)))  # stable: ID order within a place
    return trainers, teams, pics


def _team(entry: dict, stats: dict, learnsets: dict, moves: dict, ability_name) -> list[dict]:
    flags = entry.get("partyFlags", "0")
    custom, held = "PARTY_FLAG_CUSTOM_MOVES" in flags, "PARTY_FLAG_HAS_ITEM" in flags
    team = []
    for mon in entry["party_list"]:
        species, level = mon["species"], int(mon["lvl"], 0)
        s = stats[species]
        known = ([m for m in re.findall(r"MOVE_\w+", mon.get("moves", "")) if m != "MOVE_NONE"] if custom
                 else default_moves(learnsets.get(species, []), level))
        female = entry.get("gender") == "FEMALE"  # unset is 0, MALE
        ability = _ability(mon.get("ability", "Ability_Hidden") if custom else None, s, female)
        team.append({
            "species": species,
            "level": level,
            "gender": _gender(s, female),
            "item": mon.get("heldItem") if held and mon.get("heldItem") not in (None, "ITEM_NONE") else None,
            "ability": " or ".join(ability_name(a, species) for a in ability.split(" or ")) if ability else "",
            "moves": known,
            "custom": custom,  # False: the game picks the moves for the level the Pokémon is made at
            "nature": best_stat_nature(s, known, moves),
            "evs": best_two_stats(s),
        })
    return team
