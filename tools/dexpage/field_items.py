"""Items lying on the ground in the built ROM: item balls (object events) and hidden items (background events).

Map data lives in the ROM, not in CFRU's source, so this reads FireRed's map tables directly: gMapGroups (pointer at
0x0805524C) → map headers → events. An item ball's script is CFRU's ItemScript_Common_<Item> or a map script that
calls ItemScript_Common_FindTM, resolved to its item through offsets.ini and the script sources. A hidden item is a
background event of kind 7 whose data starts with the item id."""

import re
import struct
from functools import cache

from .cparse import read
from .load_cfru import item_ids
from .paths import Paths
from .rom import _charmap, _rom_bytes, decode

MAP_GROUPS_PTR = 0x5524C     # literal pool holding &gMapGroups (vanilla FireRed; CFRU doesn't move it)
MAP_NAMES = 0x3F1CAC         # sMapNames: name per region map section, from MAPSEC 0x58
FIRST_NAMED_MAPSEC = 0x58
HIDDEN_ITEM = 7
# FireRed's Sevii Islands are still in the ROM but no warp leads there in Amethyst
UNUSED_MAPS = {"Water Path", "Memorial Pillar", "Outcast Island", "Trainer Tower", "Green Path", "Tanoby Ruins",
               "Canyon Entrance", "Sevault Canyon"}
RENEWING_HIDDEN = {"Treasure Beach"}  # its hidden items come back (feature list: Treasure Beach)
SKIPPED_ITEMS = {"ITEM_NONE", "ITEM_ENIGMA_BERRY_OLD"}


def _script_items(p: Paths) -> dict[int, str]:
    """ROM address of every overworld script label → the item it gives with finditem / setvar CHOSEN_ITEM."""
    addresses = {}
    for line in read(p.cfru / "offsets.ini").splitlines():
        m = re.match(r"^(\w+):\s+([0-9A-Fa-f]{8})", line)
        if m:
            addresses[m.group(1)] = int(m.group(2), 16)
    items = {}
    for path in (p.cfru / "assembly/overworld_scripts").rglob("*.s"):
        for m in re.finditer(r"^(\w+):\s*\n(.*?)(?=^\w+:|\Z)", read(path), flags=re.M | re.S):
            given = re.search(r"(?:finditem|setvar\s+CHOSEN_ITEM)\s+(ITEM_\w+)", m.group(2))
            if given and m.group(1) in addresses:
                items[addresses[m.group(1)]] = given.group(1)
    return items


@cache
def map_section_names(p: Paths) -> dict[int, str]:
    """Region map section id → its in-game name ("Route 12 East"), from the ROM's sMapNames."""
    rom = _rom_bytes(p.rom)
    names = {}
    for i in range(256):
        v = struct.unpack_from("<I", rom, MAP_NAMES + 4 * i)[0]
        if not 0x08000000 <= v < 0x08000000 + len(rom):
            break
        names[FIRST_NAMED_MAPSEC + i] = decode(rom[v - 0x08000000:v - 0x08000000 + 40], _charmap())
    return names


@cache
def field_items(p: Paths) -> dict[str, list[str]]:
    """Item constant → places it's found ("Route 8", "Route 8 (hidden)"), in map order."""
    rom = _rom_bytes(p.rom)
    u8 = lambda o: rom[o]
    u16 = lambda o: struct.unpack_from("<H", rom, o)[0]
    u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
    is_ptr = lambda v: 0x08000000 <= v < 0x08000000 + len(rom)
    off = lambda v: v - 0x08000000

    names = map_section_names(p)
    by_id = {}
    for const, i in sorted(item_ids(p).items(), key=lambda kv: bool(re.fullmatch(r"ITEM_0[0-9A-F]{2}", kv[0]))):
        by_id.setdefault(i, const)  # prefer the real name over a numbered alias (ITEM_072 is the Rare Bone)
    scripts = _script_items(p)

    found: dict[str, list[str]] = {}
    def note(const, place):
        if const and const not in SKIPPED_ITEMS and place not in found.setdefault(const, []):
            found[const].append(place)

    groups = off(u32(MAP_GROUPS_PTR))
    tables = []
    while is_ptr(u32(groups + 4 * len(tables))):
        tables.append(off(u32(groups + 4 * len(tables))))
    starts = sorted(set(tables) | {groups})
    for table in tables:
        end = min([s for s in starts if s > table] or [table + 4 * 256])  # each group's list ends where the next begins
        for slot in range(table, end, 4):
            if not is_ptr(u32(slot)):
                break
            header = off(u32(slot))
            place = names.get(u8(header + 0x14))
            events = u32(header + 4)
            if not place or place in UNUSED_MAPS or not is_ptr(events):
                continue
            e = off(events)
            objects, backgrounds = u32(e + 4), u32(e + 16)
            for i in range(u8(e) if is_ptr(objects) else 0):
                note(scripts.get(u32(off(objects) + 24 * i + 16)), place)
            for i in range(u8(e + 3) if is_ptr(backgrounds) else 0):
                bg = off(backgrounds) + 12 * i
                if u8(bg + 5) == HIDDEN_ITEM:
                    note(by_id.get(u16(bg + 8)), f"{place} (hidden{', renews' if place in RENEWING_HIDDEN else ''})")
    return found
