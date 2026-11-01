"""Which maps make up each place, what stands on them, and how their floors fit together, read from the built ROM.

Only maps with a file in PokemonShootingStars/maps count; everything else in the ROM is a FireRed leftover.
Import after rom_maps.init(paths)."""

import re
from collections import ChainMap, defaultdict, deque

from PIL import Image, ImageFont

from ..field_items import _script_items
from ..load_cfru import item_ids
from ..load_dpe import species_names
from ..rom import item_names
from . import curation as C
from . import rom_maps as gen
from .rom_maps import P, ROM, header, is_ptr, off, render, s16, u8, u16, u32

PSS_MAPS = P.dpe.parent / "PokemonShootingStars/maps"
DUNGEONS = ["Rubarr Desert", "Varisi Forest", "Torma Cave", "Forgotten Manse", "Hesson Pass", "Peradon Forest",
            "Pluto HQ", "Mimmett Jungle", "Carnelidge Volcano", "Uteyan Ruins", "Victory Road"]
PREFIX_PLACES = ["Pluto HQ", "Daimyn Factory"]  # map files named "<place> <room>"
HIDDEN_ITEM = 7
CUTSCENE_COPIES = ("Empty ", "Credits ")  # image names of cutscene copies of real maps
BLACK = (20, 20, 20)


def bold(n):
    try:
        return ImageFont.truetype("arialbd.ttf", n)
    except OSError:
        return ImageFont.load_default(n)


# ---------- which maps exist ----------

def pss_maps():
    """(group, num) → (file name, nicer image name or None)."""
    maps, images, places = {}, {}, set()
    for f in PSS_MAPS.glob("*/*.map"):
        m = re.match(r"(.*) \((\d+)\.(\d+)\)\.map$", f.name)
        if m:
            maps[(int(m.group(2)), int(m.group(3)))] = m.group(1)
            places.add(m.group(1))
    for f in PSS_MAPS.glob("*/Images/*.png"):
        m = re.match(r"\((\d+)\.(\d+)\) (.*)\.png$", f.name)
        if m:
            images[(int(m.group(1)), int(m.group(2)))] = m.group(3)
    out = {}
    for k, v in maps.items():
        img = images.get(k)
        if img and img.startswith(CUTSCENE_COPIES):
            continue
        # the image export is newer than some .map file names (1.84 Route 12 West → Calicin Bay, 1.30 Route 9 →
        # Daimyn Factory Overworld); trust it when it names another place that has map files
        named = img and max((p for p in places if (img == p or img.startswith(p + " ")) and not img.startswith(v)),
                            key=len, default=None)
        out[k] = (C.PLACE_OF.get(k) or named or v, img)
    return out


def events(key):
    h = header(*key)
    e = u32(h + 4)
    return off(e) if is_ptr(e) else None


def warps_of(key):
    e = events(key)
    out = []
    for i in range(u8(e + 1) if e is not None else 0):
        wp = off(u32(e + 8)) + 8 * i
        out.append({"x": s16(wp), "y": s16(wp + 2), "to": (u8(wp + 7), u8(wp + 6)), "warp": u8(wp + 5)})
    return out


def connections(key):
    c = u32(header(key[0], key[1]) + 12)
    if not is_ptr(c):
        return []
    n, lst = u32(off(c)), u32(off(c) + 4)
    if not is_ptr(lst) or n > 8:
        return []
    out = []
    for i in range(n):
        o = off(lst) + 12 * i
        out.append({"dir": u8(o), "offset": struct_s32(o + 4), "to": (u8(o + 8), u8(o + 9))})
    return out


def struct_s32(o):
    v = u32(o)
    return v - (1 << 32) if v & 0x80000000 else v


def layout_size(key):
    lay = u32(header(*key))
    if not is_ptr(lay):
        return None
    w, h = u32(off(lay)), u32(off(lay) + 4)
    return (w, h) if 0 < w < 512 and 0 < h < 512 else None


LEFTOVER_WARPS = []
VALID = {}


def valid_maps():
    pss = pss_maps()
    ok, dropped = {}, []
    for key, names in pss.items():
        size = layout_size(key)
        ws = warps_of(key) if size else []
        if not size or len(ws) > 64 or key in C.BROKEN_MAPS:
            dropped.append((key, names[0]))
            continue
        ok[key] = names
        for w in ws:
            if w["to"] not in pss:
                LEFTOVER_WARPS.append((key, names[0], w["to"]))
    return ok, dropped


def place_groups(maps):
    """Place name → its map keys. Map files are named after their place; small rooms whose only way out is
    into one other place (rest houses, gyms with their own file name) join that place."""
    base = {}
    for key, (name, _) in maps.items():
        base[key] = next((p for p in PREFIX_PLACES if name.startswith(p)), name)
    counts = defaultdict(int)
    for p in base.values():
        counts[p] += 1
    for key, p in list(base.items()):
        w, h = layout_size(key)
        if counts[p] == 1 and not connections(key) and w <= 32 and h <= 32:
            outs = {base[w["to"]] for w in warps_of(key) if w["to"] in base} - {p}
            parent = outs.pop() if len(outs) == 1 else None
            if parent:
                base[key] = parent
    groups = defaultdict(list)
    for key, p in base.items():
        groups[p].append(key)
    return dict(groups), base


# ---------- overworld sprites (CFRU's NPC tables in test.gba) ----------

# CFRU's tables move with every build, so they come from its offsets.ini
_SYMBOLS = {name: addr for addr, name in gen.script_labels().items()}
OW_TABLES = _SYMBOLS["gOverworldTableSwitcher"]               # table id → GraphicsInfo pointer list
OW_PALETTES = _SYMBOLS["gObjectEventSpritePalettesSwitcher"]  # table id → SpritePalette list
FALLBACK_PAL_TABLE = 0x11
INITIAL_FACING = 0x39FD5D   # gInitialMovementTypeFacingDirections (movement type → 1 S, 2 N, 3 W, 4 E)
INITIAL_FACING_COUNT = 81
FACE_ANIM = {1: 0, 2: 1, 3: 2, 4: 3}  # facing → ANIM_STD_FACE_SOUTH/NORTH/WEST/EAST
_sprites = {}


def _palette(tag):
    table = u32(off(OW_PALETTES) + 4 * (tag >> 8 & 0xFF)) or u32(off(OW_PALETTES) + 4 * FALLBACK_PAL_TABLE)
    o = off(table)
    for i in range(512):
        data, t = u32(o + 8 * i), u16(o + 8 * i + 4)
        if t == 0x11FF:
            break
        if t == tag and is_ptr(data):
            cols = [u16(off(data) + 2 * c) for c in range(16)]
            return [((v & 31) * 255 // 31, (v >> 5 & 31) * 255 // 31, (v >> 10 & 31) * 255 // 31) for v in cols]
    return None


def sprite(gfx_id, movement):
    """The frame the game first shows for an overworld sprite: its movement type's starting facing
    (gInitialMovementTypeFacingDirections) picks the sprite's face animation, whose first frame and flip are used.
    So a sheet like the Battle Frontier cactus/flag shows the flag where the map faces it north."""
    facing = ROM[INITIAL_FACING + movement] if movement < INITIAL_FACING_COUNT else 1
    key = (gfx_id, facing)
    if key in _sprites:
        return _sprites[key]
    img = None
    table = u32(off(OW_TABLES) + 4 * (gfx_id >> 8 & 0xFF)) or u32(off(OW_TABLES))
    info = u32(off(table) + 4 * (gfx_id & 0xFF)) if is_ptr(table) else 0
    if is_ptr(info):
        i = off(info)
        w, h, pal = s16(i + 8), s16(i + 10), _palette(u16(i + 2))
        images = u32(i + 0x1C)
        fi, flip = 0, False
        anims = u32(i + 0x18)
        anim = u32(off(anims) + 4 * FACE_ANIM.get(facing, 0)) if is_ptr(anims) else 0
        if is_ptr(anim):
            cmd = u32(off(anim))
            if cmd & 0xFFFF < 0x100:  # a frame command, not a jump/loop
                fi, flip = cmd & 0xFFFF, bool(cmd >> 22 & 1)
        if pal and is_ptr(images) and 0 < w <= 64 and 0 < h <= 64:
            data_ptr, size = u32(off(images) + 8 * fi), u16(off(images) + 8 * fi + 4)
            if size != w * h // 2:  # inanimate sprites have one frame
                data_ptr, size = u32(off(images)), u16(off(images) + 4)
            if is_ptr(data_ptr) and size == w * h // 2:
                raw = ROM[off(data_ptr):off(data_ptr) + size]
                img = Image.new("RGBA", (w, h))
                px = img.load()
                tw = w // 8
                for t in range(w * h // 64):
                    ox, oy = (t % tw) * 8, (t // tw) * 8
                    for b in range(32):
                        v = raw[t * 32 + b]
                        for n, c in enumerate((v & 15, v >> 4)):
                            if c:
                                px[ox + (b % 4) * 2 + n, oy + b // 4] = pal[c] + (255,)
                if flip:
                    img = img.transpose(Image.FLIP_LEFT_RIGHT)
    _sprites[key] = img
    return img


# ---------- objects ----------

def script_texts():
    """Every label's lines, plus each file's own blocks: files reuse local label names."""
    blocks, files = {}, {}
    for path in (P.cfru / "assembly/overworld_scripts").rglob("*.s"):
        files[path] = gen.script_blocks(path.read_text(encoding="utf-8", errors="replace"))
        blocks.update(files[path])
    return blocks, files


def words(s):
    s = re.sub(r"(?<=[a-z])(?=[A-Z0-9])|(?<=[A-Z])(?=[A-Z][a-z])", " ", s)
    return s.replace("Pokemon", "Pokémon").strip()


VAR_RUNTIME_CHANGEABLE = 0x5028     # CFRU src/config.h
POSTGAME_HIDE_FLAGS = {0x9D, 0x6C}   # cleared when Selene is beaten (ascension_tower.s): postgame / post-credits NPCs
GAME_CLEARED = r"checkflag (0x82C|0x4BC)\b"


def map_script_labels(key, labels):
    ms = u32(header(*key) + 8)
    out = []
    if not is_ptr(ms):
        return out
    o = off(ms)
    for _ in range(8):
        kind = u8(o)
        if kind == 0:
            break
        out.append(labels.get(u32(o + 1), ""))
        o += 5
    return out


# The rival's optional side events (CFRU assembly/overworld_scripts/common/rival_events.s): what each asks for and
# gives, and whether it differs in Divergent mode. Hand-written: the asks are scattered across specials and callasms.
RIVAL_EVENTS = {
    1: ("Rival: give 5 Poké Balls, receive ₽1,500", False),
    2: ("Rival: give a Revive, receive 3 Ultra Balls", False),
    3: ("Rival: trade any Egg for a random Litleo, Shellos or Scraggy Egg (Aipom, Impidimp or Spheal in Divergent)", True),
    4: ("Rival: catch 10 Pokémon by fishing, receive 5 Net Balls", False),
    5: ("Rival: complete this area's DexNav, receive 3 Rare Candies", False),
    6: ("Rival: trade a Lv 30+ Pokémon for a random Boldore, Gurdurr or Phantump with its Hidden Ability "
        "(Alolan Graveler, Machoke or Kadabra in Divergent)", True),
    7: ("Rival: win a battle, receive 3 Bottle Caps", False),
    8: ("Rival: bring a Pokémon that knows Return, its friendship is maxed out", False),
}


class Objects:
    def __init__(self):
        self.labels = gen.script_labels()
        self.items = _script_items(P)
        ids = item_ids(P)
        self.names = item_names(P.rom, ids)
        self.by_id = {}
        for const, i in ids.items():
            self.by_id.setdefault(i, const)
        self.blocks, self.file_blocks = script_texts()
        self.species_name = species_names(P)
        self.species = {re.sub(r"[^A-Z]", "", n.upper()) for n in self.species_name.values() if n.strip("?")}
        # machine number → move, from DPE's "43 - Move.txt" compatibility files (101+ are the HMs)
        self.machine_moves = {int(m.group(1)): m.group(2) for f in (P.dpe / "src/tm_compatibility").iterdir()
                              if (m := re.fullmatch(r"(\d+) - (.+)\.txt", f.name))}

    def item_name(self, const):
        if m := re.fullmatch(r"ITEM_(TM|HM)(\d+)", const):
            n = int(m.group(2)) + (100 if m.group(1) == "HM" else 0)  # HMs follow the 100 TMs
            move = self.machine_moves.get(n)
            return f"{const[5:]} {move}" if move else const[5:]
        return self.names.get(const) or const.removeprefix("ITEM_").replace("_", " ").title()

    def divergent_item(self, label):
        """Item scripts that give something else in Divergent mode (checkflag 0x945 → a second finditem)."""
        body = self.blocks.get(label, [])
        if not any("checkflag 0x945" in l for l in body):
            return None
        alt = next((m.group(1) for l in body if (m := re.search(r"_goto (\w+)", l))), None)
        found = [m.group(1) for lab in (label, alt) for l in self.blocks.get(lab, [])
                 if (m := re.search(r"(?:finditem|setvar CHOSEN_ITEM)\s+(ITEM_\w+)", l))]
        if len(found) >= 2:
            return f"{self.item_name(found[0])} ({self.item_name(found[1])} in Divergent)"
        return None

    def walk_modes(self, label, divergent=False, depth=0, seen=None):
        """Every script line reachable from a label, with whether it runs in Divergent mode: a `checkflag 0x945`
        (Divergent mode) splits the script, the `if SET` target and the rest going to opposite modes."""
        seen = seen if seen is not None else set()
        if (label, divergent) in seen or label not in self.blocks or depth > 4:
            return
        seen.add((label, divergent))
        body = self.blocks[label]
        mode = divergent
        for i, line in enumerate(body):
            yield line, mode
            nxt = body[i + 1] if i + 1 < len(body) else ""
            if line.startswith("checkflag 0x945") and (m := re.match(r"if (NOT_)?SET _(?:goto|call) (\w+)", nxt)):
                yield from self.walk_modes(m.group(2), not m.group(1), depth + 1, seen)
                if "_goto" in nxt:
                    mode = bool(m.group(1))  # falling through means the jump wasn't taken
            elif (m := re.search(r"(?:goto|call)\s+(\w+)\s*$", line)) and not (
                    i > 0 and body[i - 1].startswith("checkflag 0x945")):
                yield from self.walk_modes(m.group(1), mode, depth + 1, seen)
            if line in ("end", "return") or line.startswith("goto "):
                break

    def by_mode(self, label, pattern, name):
        """What a pattern finds in Standard and in Divergent mode, as 'X' or 'X (Y in Divergent)'."""
        found = {False: [], True: []}
        for line, div in self.walk_modes(label):
            if m := re.search(pattern, line):
                found[div].append(name(m.group(1)))
        std, div = (list(dict.fromkeys(found[d])) for d in (False, True))
        if not std and not div:
            return None, False
        if not div or div == std:
            return ", ".join(std), False
        if not std:
            return f"{', '.join(div)} (Divergent only)", True
        return f"{', '.join(std)} ({', '.join(div)} in Divergent)", True

    def runtime_sprites(self, key):
        """Runtime-changeable overworld sprites (graphics 0xFF0n read var VAR_RUNTIME_CHANGEABLE + n, CFRU config.h):
        the value the map's own scripts set in Standard mode (Rubarr's Groudon/Hoopa, Seppire's Kyogre/Lugia)."""
        out = {}
        # the map's scripts are the ones in its own file (Mimmett's SetLegendarySprite is not Seppire's)
        ms = self.labels.get(u32(header(*key) + 8), "")
        own = next((b for b in self.file_blocks.values() if ms in b), {})
        base, self.blocks = self.blocks, ChainMap(own, self.blocks)
        try:
            for top in map_script_labels(key, self.labels):
                for line, div in self.walk_modes(top):
                    if not div and (m := re.match(r"setvar (0x[0-9A-Fa-f]+) (0x[0-9A-Fa-f]+|\d+)", line)):
                        slot = int(m.group(1), 16) - VAR_RUNTIME_CHANGEABLE
                        if 0 <= slot <= 0xF:
                            out.setdefault(slot, int(m.group(2), 0))
        finally:
            self.blocks = base
        return out

    ROLE_WORDS = [(r"Tutor|teachmove", "move tutor"), (r"Reminder|Relearn", "move reminder"),
                  (r"Deleter", "move deleter"), (r"pokemart|Mart\b|Shop|Merchant|DailyDeal|Seller", "shop"),
                  (r"PlayerHeal|Nurse", "heals your team"), (r"HandleTrade|Trade", "trade"),
                  (r"givepokemon", "gives a Pokémon"), (r"giveegg", "gives an Egg")]

    def npc_role(self, label):
        """What a person does beyond talking, read from their script and the labels it jumps to."""
        seen, todo, text, items = set(), [(label, 0)], [label.split("_")[-1]], []
        while todo:
            lab, depth = todo.pop()
            if lab in seen or lab not in self.blocks:
                continue
            seen.add(lab)
            for line in self.blocks[lab]:
                text.append(line)
                if m := re.match(r"(?:giveitem|obtainitem|finditem)\s+(ITEM_\w+)", line):
                    items.append(self.item_name(m.group(1)))
                if depth < 3 and (m := re.search(r"(?:goto|call)\s+(\w+)\s*$", line)):
                    todo.append((m.group(1), depth + 1))
                    text.append(m.group(1))
        blob = "\n".join(text)
        roles = []
        if items:
            uniq = list(dict.fromkeys(items))
            roles.append("gives " + ", ".join(uniq[:2]) + (f" +{len(uniq) - 2}" if len(uniq) > 2 else ""))
        roles += [r for pat, r in self.ROLE_WORDS if re.search(pat, blob)]
        return ", ".join(dict.fromkeys(roles)) or None

    def postgame_flags(self, key):
        """Flags this map's own scripts clear only once the game is cleared (Kurtis in the Route 13 cave)."""
        flags = set()
        for top in map_script_labels(key, self.labels):
            todo, seen = [top], set()
            while todo:
                lab = todo.pop()
                if lab in seen or lab not in self.blocks:
                    continue
                seen.add(lab)
                gated = False
                body = self.blocks[lab]
                for i, line in enumerate(body):
                    if re.match(GAME_CLEARED, line) and i + 1 < len(body) and "NOT_SET" in body[i + 1]:
                        gated = True
                    elif gated and (m := re.match(r"clearflag (0x[0-9A-Fa-f]+|\d+)", line)):
                        flags.add(int(m.group(1), 0))
                    if m := re.search(r"(?:goto|call)\s+(\w+)\s*$", line):
                        if not line.startswith("if"):
                            todo.append(m.group(1))
        return flags

    def classify(self, key):
        e = events(key)
        out = []
        late = self.postgame_flags(key) if e is not None else set()
        if e is None:
            return out
        swaps = self.runtime_sprites(key)
        for i in range(u8(e)):
            o = off(u32(e + 4)) + 24 * i
            x, y, script, ttype = s16(o + 4), s16(o + 6), u32(o + 16), u16(o + 12)
            label = self.labels.get(script, "")
            x, y = C.FINAL_SPOT.get(label, (x, y))  # where a scene leaves them (Chance, Meltan)
            tail = label.split("_")[-1] if label else ""
            gfx = u8(o + 1) | u8(o + 3) << 8
            if gfx >> 8 == 0xFF and (gfx & 0xFF) in swaps:  # a runtime-changeable sprite: the map sets which one
                gfx = swaps[gfx & 0xFF]
            ob = {"x": x, "y": y, "label": label, "gfx": gfx, "move": u8(o + 9), "modes": False}
            flag = u16(o + 20)
            ob["postgame"] = flag in POSTGAME_HIDE_FLAGS or flag in late or "UltraWormhole_" in label
            if label in C.NO_SPRITE:
                continue
            if label in C.NOTES:
                ob["kind"], (ob["text"], ob["modes"], pg) = "npc", C.NOTES[label]
                ob["postgame"] |= pg
                same = next((o for o in out if o.get("label") == label and abs(o["x"] - x) + abs(o["y"] - y) == 1), None)
                if same:  # two people sharing one event (Calicin Bay's Clancy and Ena): one marker between them
                    out.append(dict(ob, kind="scenery"))
                    same["mx"], same["my"] = (same["x"] + x) / 2, (same["y"] + y) / 2
                else:
                    out.append(ob)
                continue
            if m := re.fullmatch(r"EventScript_RivalEvent(\d)", label):
                ob["kind"], (ob["text"], ob["modes"]) = "npc", RIVAL_EVENTS[int(m.group(1))]
                out.append(ob)
                continue
            if (not label and ttype) or "Rival" in label:
                continue  # spawned in by a cutscene or facility (Battle Frontier actors, the rival): never just standing there
            if "Statue_" in label and "RubarrDesertCaves" in label:
                ob["kind"] = "statue"
                out.append(ob)
                continue  # numbered by the Rubarr puzzle
            wild, wild_modes = self.by_mode(label, r"(?:setwildbattle|wildbattle)\s+(SPECIES_\w+)",
                                            lambda s: self.species_name.get(s, s)) if label else (None, False)
            if script in self.items or "ItemScript" in label:
                ob["kind"] = "item"
                given, ob["modes"] = self.by_mode(label, r"(?:finditem|setvar CHOSEN_ITEM)\s+(ITEM_\w+)", self.item_name)
                ob["text"] = given or self.item_name(self.items.get(script, "?"))
            elif label.endswith(("_RockSmash", "_Strength", "_Cut")):
                ob["kind"], ob["text"] = "hm", {"RockSmash": "R", "Strength": "S", "Cut": "C"}[tail]
            elif "UltraWormhole_" in label:
                ob["kind"], ob["text"] = "wild", f"Ultra Wormhole ({tail})"
            elif wild and not ttype:
                ob["kind"], ob["text"], ob["modes"] = "wild", wild, wild_modes
            elif tail and re.sub(r"Encounter\d*$", "", tail).upper() in self.species and (
                    "Encounter" in tail or not ttype):
                ob["kind"], ob["text"] = "wild", re.sub(r"Encounter\d*$", "", tail)
            elif ttype:
                ob["kind"] = "scenery"  # trainers: sprite only (Collin: players look for warps, items and special NPCs)
            elif label and ((role := self.npc_role(label)) or ob["postgame"]):
                ob["kind"], ob["text"] = "npc", f"{words(tail)}: {role}" if role else words(tail)
                gift, ob["modes"] = self.by_mode(label, r"(?:giveitem|obtainitem)\s+(ITEM_\w+)", self.item_name)
                if ob["modes"]:
                    ob["text"] = f"{words(tail)}: gives {gift}"
            elif label:
                ob["kind"] = "scenery"  # only talks: sprite, no badge
            elif not u16(o + 20):
                ob["kind"] = "scenery"  # no script and never hidden: decoration drawn as a sprite
            else:
                continue  # no script but hidden by a flag: a cutscene actor
            if label in C.WILD_NOTES and ob["kind"] == "wild":
                ob["text"], pg = C.WILD_NOTES[label]
                ob["modes"] = "Divergent" in ob["text"]
                ob["postgame"] |= pg
            if (label in C.NO_MARKER or key in C.NO_MARKER_MAPS) and ob["kind"] in ("npc", "wild", "item"):
                ob["kind"] = "scenery"
            out.append(ob)
        for i in range(u8(e + 2)):  # step triggers that start an event (Lake Laplaz's roamers)
            c = off(u32(e + 12)) + 16 * i
            label = self.labels.get(u32(c + 12), "")
            if label in C.NOTES:
                text, modes, pg = C.NOTES[label]
                out.append({"x": s16(c), "y": s16(c + 2), "kind": "npc", "text": text, "modes": modes, "postgame": pg})
        for i in range(u8(e + 3)):
            bg = off(u32(e + 16)) + 12 * i
            x, y = s16(bg), s16(bg + 2)
            if u8(bg + 5) == HIDDEN_ITEM and (key, x, y) not in C.NO_HIDDEN:
                const = self.by_id.get(u16(bg + 8), "?")
                out.append({"x": x, "y": y, "kind": "hidden", "text": self.item_name(const)})
            elif u8(bg + 5) < 5 and (label := self.labels.get(u32(bg + 8), "")) in C.NOTES:  # signs (Rotom's catalog)
                text, modes, pg = C.NOTES[label]
                out.append({"x": x, "y": y, "kind": "npc", "text": text, "modes": modes, "postgame": pg})
        return out


# ---------- one sheet ----------

DIRS = {1: "down", 2: "up", 3: "left", 4: "right"}


def floor_order(keys):
    """Walking order: start at the map with the most ways out of the place, then breadth-first over warps."""
    keyset = set(keys)
    outside = lambda k: sum(w["to"] not in keyset and w["to"] in VALID for w in warps_of(k)) + len(connections(k))
    start = max(keys, key=lambda k: (outside(k), (layout_size(k) or (0, 0))[0] * (layout_size(k) or (0, 0))[1]))
    seen, q = [start], deque([start])
    while q:
        k = q.popleft()
        for w in warps_of(k):
            if w["to"] in keyset and w["to"] not in seen:
                seen.append(w["to"])
                q.append(w["to"])
    return seen + sorted(keyset - set(seen))


def floor_rank(name):
    """1F → 1, 2F → 2, B1F / BF1 / BF → -1 …; None for names that aren't a floor number."""
    if name in ("BF", "Underground"):
        return -1
    m = re.fullmatch(r"(B?)(\d+)F|BF(\d+)|F(\d+)", name)
    if not m:
        return None
    if m.group(2):
        return -int(m.group(2)) if m.group(1) else int(m.group(2))
    return -int(m.group(3)) if m.group(3) else int(m.group(4))


def sort_floors(order, fnames):
    """Keep the entrance first, then numbered floors in order (up from 1F, down from B1F), then the rest."""
    first, rest = order[0], order[1:]
    ranked = sorted((k for k in rest if floor_rank(fnames[k]) is not None), key=lambda k: abs(floor_rank(fnames[k])))
    return [first] + ranked + [k for k in rest if floor_rank(fnames[k]) is None]


FLOOR_NAMES = {(1, 1): "Desert", (1, 114): "Cave Rooms (1F)", (1, 123): "Caverns B1F", (1, 3): "Caverns B2F",
               **C.FLOOR_NAMES}


def floor_names(place, keys, maps):
    names = {k: FLOOR_NAMES[k] for k in keys if k in FLOOR_NAMES}
    for k in keys:
        if k in names:
            continue
        file_name, image = maps[k]
        n = image or file_name
        n = n[len(place):].strip(" -") if n.startswith(place) else n
        n = n or place
        names[k] = n or place
    dup = defaultdict(list)
    for k, n in names.items():
        dup[n].append(k)
    for n, ks in dup.items():
        if len(ks) > 1:
            for i, k in enumerate(sorted(ks), 1):
                names[k] = f"{n} ({i})" if n != place else f"Area {i}"
    return names


def stitch(place, order, fnames, imgs, entries, spots):
    """Maps of one place that share an edge (map connections: the Battle Frontier quadrants, Mimmett Jungle's
    rooms) become one picture, laid out by their connection offsets."""
    keyset, at, groups = set(order), {}, []
    for start in order:
        if start in at:
            continue
        at[start] = (0, 0)
        group, todo = [start], [start]
        while todo:
            k = todo.pop()
            (x, y), (w, h) = at[k], layout_size(k)
            for cn in connections(k):
                nb = cn["to"]
                if nb not in keyset or nb in at or cn["dir"] not in DIRS:
                    continue
                nw, nh = layout_size(nb)
                at[nb] = {"down": (x + cn["offset"], y + h), "up": (x + cn["offset"], y - nh),
                          "left": (x - nw, y + cn["offset"]), "right": (x + w, y + cn["offset"])}[DIRS[cn["dir"]]]
                group.append(nb)
                todo.append(nb)
        groups.append(group)
    if all(len(g) == 1 for g in groups):
        return order, fnames, imgs, entries, spots, {}
    rename, shift = {}, {}
    for g in groups:
        if len(g) == 1:
            continue
        x0, y0 = min(at[k][0] for k in g), min(at[k][1] for k in g)
        x1 = max(at[k][0] + layout_size(k)[0] for k in g)
        y1 = max(at[k][1] + layout_size(k)[1] for k in g)
        canvas = Image.new("RGBA", ((x1 - x0) * 16, (y1 - y0) * 16))
        for k in g:
            canvas.alpha_composite(imgs[k], ((at[k][0] - x0) * 16, (at[k][1] - y0) * 16))
        head = g[0]
        name = place if order[0] in g else max(g, key=lambda k: imgs[k].width * imgs[k].height)
        name = name if isinstance(name, str) else fnames[name]
        for k in g:
            rename[fnames[k]] = name
            shift[k] = (head, (at[k][0] - x0) * 16, (at[k][1] - y0) * 16)
        imgs = {kk: v for kk, v in imgs.items() if kk not in g} | {head: canvas}
        fnames = dict(fnames) | {head: name}
    order = list(dict.fromkeys(shift.get(k, (k,))[0] for k in order))
    entries = [(e[0], e[1], e[2], rename.get(e[3], e[3]), *e[4:]) for e in entries]
    spots = {pid: [(shift[k][0], x + shift[k][1], y + shift[k][2]) if k in shift else (k, x, y) for k, x, y in pts]
             for pid, pts in spots.items()}
    return order, fnames, imgs, entries, spots, shift



RUBARR = {}


def rubarr():
    """Rubarr Desert's sand puzzle: the statues on Caverns B1F (1.123), numbered in map order, and the pits they fill
    on Caverns B2F (1.3), found through the B2F load script's flag and sand-level checks and the setmaptiles they run."""
    if RUBARR:
        return RUBARR
    text = (P.cfru / "assembly/overworld_scripts/dungeons/rubarr_desert.s").read_text(encoding="utf-8")
    blocks, consts = gen.script_blocks(text), gen.equs(text)
    by_flag, by_level = {}, {}
    body = blocks["MapEntryScript_RubarrDesertBF2_SetSand"]
    for a, b in zip(body, body[1:]):
        m, n = re.match(r"checkflag (\w+)", a), re.match(r"if SET _call (\w+)", b)
        if m and n:
            by_flag[int(m.group(1), 0)] = n.group(1)
        m, n = re.match(r"compare (\w+) (\w+)", a), re.match(r"if equal _goto (\w+)", b)
        if m and n:
            by_level[int(m.group(2), 0)] = n.group(1)
    labels = gen.script_labels()
    e = events((1, 123))
    statues = []
    for i in range(u8(e)):
        o = off(u32(e + 4)) + 24 * i
        label = labels.get(u32(o + 16), "")
        if "Statue_" not in label:
            continue
        sb = blocks.get(label, [])
        statues.append({"n": len(statues) + 1, "x": s16(o + 4), "y": s16(o + 6),
                        "flag": next((int(m.group(1), 0) for l in sb if (m := re.match(r"setflag (\w+)", l))), None),
                        "addsLevel": any(l.startswith("addvar 0x40A3") for l in sb)})
    w, h = layout_size((1, 3))

    def pit(label):  # the setmaptiles that land on the map (the 0x450 columns don't)
        tiles = [t for t in gen.tiles_set(blocks, consts, label) if t[0] < w and t[1] < h]
        if not tiles:
            return None
        x0, y0 = min(t[0] for t in tiles), min(t[1] for t in tiles)
        return {"x": x0, "y": y0, "w": max(t[0] for t in tiles) - x0 + 1, "h": max(t[1] for t in tiles) - y0 + 1}

    fills = {f"flag{flag}": pit(label) for flag, label in by_flag.items() if label in blocks}
    fills |= {f"level{level}": pit(label) for level, label in by_level.items()}
    RUBARR.update(statues=statues, fills={k: v for k, v in fills.items() if v})
    return RUBARR


def draw_rubarr_pits(d):
    """Outline each pit on Caverns B2F with the number of the statue that fills it."""
    statues, fills = rubarr()["statues"], rubarr()["fills"]
    big = "·".join(str(s["n"]) for s in statues if s["addsLevel"])
    pits = [(fills[f"flag{s['flag']}"], str(s["n"])) for s in statues if not s["addsLevel"]]
    pits.append((fills["level3"], f"{big} (3 levels)"))
    for fill, tag in pits:
        box = (fill["x"] * 16, fill["y"] * 16, (fill["x"] + fill["w"]) * 16, (fill["y"] + fill["h"]) * 16)
        d.rectangle(box, fill=(86, 180, 233, 70))
        for i, col in enumerate((BLACK, (86, 180, 233))):  # two-tone dashes read on sand and on rock
            dashed(d, box, col, phase=i * 8)
        t = f"Pit {tag}"
        tw = d.textlength(t, font=bold(14)) + 12
        d.rounded_rectangle((box[0], box[1] - 22, box[0] + tw, box[1]), 4, fill=(86, 180, 233), outline=BLACK)
        d.text((box[0] + 6, box[1] - 11), t, font=bold(14), fill=BLACK, anchor="lm")

def dashed(d, box, color, dash=8, width=3, phase=0):
    x0, y0, x1, y1 = box
    for x in range(int(x0) + phase, int(x1), dash * 2):
        d.line((x, y0, min(x + dash, x1), y0), fill=color, width=width)
        d.line((x, y1, min(x + dash, x1), y1), fill=color, width=width)
    for y in range(int(y0) + phase, int(y1), dash * 2):
        d.line((x0, y, x0, min(y + dash, y1)), fill=color, width=width)
        d.line((x1, y, x1, min(y + dash, y1)), fill=color, width=width)
