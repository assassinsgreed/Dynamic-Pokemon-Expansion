"""Reads in-game text that only exists in the built ROM (item names were edited there with HexManiac)."""

from collections import Counter, defaultdict
from functools import cache
from pathlib import Path

from PIL import Image

from .paths import DPE_ROOT

ITEM_STRUCT_SIZE = 44  # FireRed struct Item
ITEM_NAME_LENGTH = 14
TERMINATOR = 0xFF
POCKET_KEY_ITEMS, POCKET_POKE_BALLS, POCKET_BERRIES = 2, 3, 5  # FireRed bag pockets (struct Item.pocket)


class RomError(Exception):
    pass


def load_charmap(path: Path = DPE_ROOT / "charmap.tbl") -> dict[int, str]:
    charmap: dict[int, str] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if "=" not in line:
            continue
        code, char = line.split("=", 1)
        if len(code) != 2 or not char:
            continue
        byte = int(code, 16)
        if char in ('\\"', "\\$"):  # escaped for the string compiler; the game shows the bare character
            char = char[1]
        # Some bytes have several spellings; prefer the plain-ASCII one (' over ’).
        if byte not in charmap or (not charmap[byte].isascii() and char.isascii()):
            charmap[byte] = char
    return charmap


def decode(data: bytes, charmap: dict[int, str]) -> str:
    out = []
    for b in data:
        if b == TERMINATOR:
            break
        out.append(charmap.get(b, "?"))
    return "".join(out)


def encode(text: str, charmap: dict[int, str]) -> bytes:
    reverse = {}
    for byte, char in charmap.items():
        reverse.setdefault(char, byte)
    return bytes(reverse[c] for c in text) + bytes([TERMINATOR])


def _find_item_table(rom: bytes, charmap: dict[int, str]) -> int:
    """Locate the item table by its first two entries' names rather than a hard-coded offset."""
    candidates = []
    for first, second in (("Master Ball", "Ultra Ball"), ("MASTER BALL", "ULTRA BALL")):
        needle, follow = encode(first, charmap), encode(second, charmap)
        start = rom.find(needle)
        while start != -1:
            if rom[start + ITEM_STRUCT_SIZE:start + ITEM_STRUCT_SIZE + len(follow)] == follow:
                candidates.append(start - ITEM_STRUCT_SIZE)  # item 0 precedes Master Ball
            start = rom.find(needle, start + 1)
    if len(candidates) != 1:
        raise RomError(f"expected exactly one item table in the ROM, found {len(candidates)}")
    return candidates[0]


ROM_BASE = 0x08000000
ICON_CODE = range(0x098600, 0x098B00)  # around AddItemIconSprite (0x8098758); its literal pools point at the table
ICON_GFX_SIZE = 0x120  # 24×24 at 4bpp, LZ77-compressed
ICON_PAL_SIZE = 0x20


def _u32(rom: bytes, offset: int) -> int:
    return int.from_bytes(rom[offset:offset + 4], "little")


def _lz77_size(rom: bytes, pointer: int) -> int | None:
    o = pointer - ROM_BASE
    if not 0 <= o < len(rom) - 4 or rom[o] != 0x10:
        return None
    return rom[o + 1] | rom[o + 2] << 8 | rom[o + 3] << 16


def lz77(rom: bytes, pointer: int) -> bytes:
    o = pointer - ROM_BASE
    size = _lz77_size(rom, pointer)
    o += 4
    out = bytearray()
    while len(out) < size:
        flags = rom[o]
        o += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> bit):
                x = rom[o] << 8 | rom[o + 1]
                o += 2
                distance = (x & 0xFFF) + 1
                for _ in range((x >> 12) + 3):
                    out.append(out[-distance])
            else:
                out.append(rom[o])
                o += 1
    return bytes(out)


def _find_icon_table(rom: bytes) -> int:
    """The literal-pool pointer whose target is a run of (icon gfx, icon palette) pointer pairs."""
    def looks_like_table(offset: int) -> bool:
        return sum(_lz77_size(rom, _u32(rom, offset + 8 * k)) == ICON_GFX_SIZE
                   and _lz77_size(rom, _u32(rom, offset + 8 * k + 4)) == ICON_PAL_SIZE
                   for k in range(1, 41)) >= 36

    found = {w for w in (_u32(rom, o) for o in range(ICON_CODE.start, ICON_CODE.stop, 4))
             if ROM_BASE <= w < ROM_BASE + len(rom) and looks_like_table(w - ROM_BASE)}
    if len(found) != 1:
        raise RomError(f"expected one item icon table near AddItemIconSprite, found {len(found)}")
    return found.pop() - ROM_BASE


def item_icons(rom_path: Path, item_ids: dict[str, int]) -> dict[str, Image.Image]:
    """24×24 RGBA icon per item constant (palette index 0 transparent); items without a valid icon are left out."""
    if not rom_path.exists():
        raise RomError(f"built ROM not found: {rom_path} (build Complete-Fire-Red-Upgrade first)")
    rom = rom_path.read_bytes()
    table = _find_icon_table(rom)
    icons = {}
    for const, idx in item_ids.items():
        gfx_ptr, pal_ptr = _u32(rom, table + 8 * idx), _u32(rom, table + 8 * idx + 4)
        if _lz77_size(rom, gfx_ptr) != ICON_GFX_SIZE or _lz77_size(rom, pal_ptr) != ICON_PAL_SIZE:
            continue
        icons[const] = _icon(lz77(rom, gfx_ptr), lz77(rom, pal_ptr))
    return icons


def _icon(gfx: bytes, pal: bytes) -> Image.Image:
    colors = []
    for k in range(16):
        c = pal[2 * k] | pal[2 * k + 1] << 8
        colors.append(((c & 31) * 255 // 31, (c >> 5 & 31) * 255 // 31, (c >> 10 & 31) * 255 // 31, 0 if k == 0 else 255))
    img = Image.new("RGBA", (24, 24))
    px = img.load()
    for tile in range(9):  # 3×3 tiles of 8×8, two pixels per byte (low nibble first)
        tx, ty = tile % 3 * 8, tile // 3 * 8
        for y in range(8):
            for x in range(8):
                byte = gfx[tile * 32 + y * 4 + x // 2]
                px[tx + x, ty + y] = colors[byte >> 4 if x & 1 else byte & 15]
    return img


def tm_icons(rom_path: Path, machines: dict[str, tuple[int, str]], fairy_pal: int) -> dict[str, Image.Image]:
    """TM/HM bag icons in their move's type colour ({item constant: (item id, move type)} → icon), as the game shows
    them. The item icon table still has FireRed's palette per TM item (stale where a TM teaches another move, and
    generic past TM100), so each type takes the palette most of its TMs have, on the disc most TMs use. FireRed has
    no Fairy disc: CFRU's Fairy_TM_DiskPal (the TM Case's, address from offsets.ini) has the same seven-shade
    gradient at indices 2-8 and its highlight at 14, where a bag palette has them at 3-9 and 14."""
    rom = _rom_bytes(rom_path)
    table = _find_icon_table(rom)
    discs, by_type = Counter(), defaultdict(Counter)
    for idx, move_type in machines.values():
        gfx_ptr, pal_ptr = _u32(rom, table + 8 * idx), _u32(rom, table + 8 * idx + 4)
        discs[gfx_ptr] += 1
        if _lz77_size(rom, pal_ptr) == ICON_PAL_SIZE:
            by_type[move_type][pal_ptr] += 1
    gfx = lz77(rom, discs.most_common(1)[0][0])
    pals = {t: lz77(rom, c.most_common(1)[0][0]) for t, c in by_type.items() if t != "FAIRY"}
    if "FAIRY" in {t for _, t in machines.values()}:
        fairy, base = rom[fairy_pal - ROM_BASE:fairy_pal - ROM_BASE + 32], bytearray(pals["PSYCHIC"])
        base[6:20], base[28:30] = fairy[4:18], fairy[28:30]
        pals["FAIRY"] = bytes(base)
    missing = {t for _, t in machines.values()} - set(pals)
    if missing:
        raise RomError(f"no TM disc palette for {sorted(missing)}")
    return {const: _icon(gfx, pals[t]) for const, (_, t) in machines.items()}


@cache
def _rom_bytes(rom_path: Path) -> bytes:
    return rom_path.read_bytes()


@cache
def _charmap() -> dict[int, str]:
    return load_charmap()


def read_text(rom_path: Path, address: int, limit: int = 200) -> str:
    """Game text at a ROM address, with its line/page breaks (\\n, \\l, \\p) as spaces."""
    o = address - ROM_BASE
    text = decode(_rom_bytes(rom_path)[o:o + limit], _charmap())
    for brk in ("\\n", "\\l", "\\p"):
        text = text.replace("-" + brk, "-").replace(brk, " ")  # "hide-" + break + "melting" is one word
    return " ".join(text.replace("\\e", "é").split())


def item_fields(rom_path: Path, item_ids: dict[str, int]) -> dict[str, dict]:
    """What the game's item table says about each item: its bag pocket, hold effect, and whether it has a field or
    battle use, and its bag description (FireRed struct Item: description at +20, pocket at +26, type at +27 — a
    ball's BALL_TYPE —, fieldUseFunc at +28, battleUsage at +32)."""
    rom = _rom_bytes(rom_path)
    base = _find_item_table(rom, _charmap())
    fields = {}
    for const, idx in item_ids.items():
        o = base + idx * ITEM_STRUCT_SIZE
        if o + ITEM_STRUCT_SIZE <= len(rom):
            b = rom[o:o + ITEM_STRUCT_SIZE]
            desc = int.from_bytes(b[20:24], "little")
            fields[const] = {"hold": b[18], "pocket": b[26], "type": b[27], "field_use": int.from_bytes(b[28:32], "little"), "battle_use": b[32],
                             "desc": read_text(rom_path, desc) if ROM_BASE <= desc < ROM_BASE + len(rom) else ""}
    return fields


def item_names(rom_path: Path, item_ids: dict[str, int]) -> dict[str, str]:
    if not rom_path.exists():
        raise RomError(f"built ROM not found: {rom_path} (build Complete-Fire-Red-Upgrade first)")
    rom = rom_path.read_bytes()
    charmap = load_charmap()
    base = _find_item_table(rom, charmap)
    names = {}
    for const, idx in item_ids.items():
        offset = base + idx * ITEM_STRUCT_SIZE
        if offset + ITEM_NAME_LENGTH <= len(rom):
            names[const] = decode(rom[offset:offset + ITEM_NAME_LENGTH], charmap).replace("\\e", "é")
    return names
