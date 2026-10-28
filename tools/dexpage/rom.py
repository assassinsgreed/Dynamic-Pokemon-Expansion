"""Reads in-game text that only exists in the built ROM (item names were edited there with HexManiac)."""

from pathlib import Path

from PIL import Image

from .paths import DPE_ROOT

ITEM_STRUCT_SIZE = 44  # FireRed struct Item
ITEM_NAME_LENGTH = 14
TERMINATOR = 0xFF


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
        gfx, pal = lz77(rom, gfx_ptr), lz77(rom, pal_ptr)
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
        icons[const] = img
    return icons


def read_text(rom_path: Path, address: int, limit: int = 200) -> str:
    rom = rom_path.read_bytes()
    o = address - ROM_BASE
    return decode(rom[o:o + limit], load_charmap())


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
            names[const] = decode(rom[offset:offset + ITEM_NAME_LENGTH], charmap)
    return names
